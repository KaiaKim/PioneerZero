"""
Google OAuth authentication handlers
"""
from fastapi import APIRouter, Request, Response, WebSocket
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os
import secrets
from typing import Dict, Optional
from dotenv import load_dotenv
from .util import manager

# allowed member (later move to DB)
member_list = ["kaiakim0727@gmail.com"]

# Load environment variables from .env file
load_dotenv()

# Google OAuth credentials from environment variables
CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"]

# Validate required environment variables
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError(
        "Missing required environment variables: GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET. "
        "Please create a .env file with these variables. See .env.example for reference."
    )

# Temporary storage for OAuth state and tokens (in production, use Redis or DB)
_oauth_states: Dict[str, str] = {}  # {state: session_id}
_oauth_tokens: Dict[str, dict] = {}  # {session_id: token_data}

router = APIRouter()


def get_flow():
    """Create Google OAuth flow"""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )


@router.get("/auth/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state (in production, associate with session)
    _oauth_states[state] = state
    
    # Create OAuth flow
    flow = get_flow()
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=state,
        prompt='consent'
    )
    
    return RedirectResponse(url=authorization_url)


@router.get("/auth/google/callback")
async def google_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    """Handle Google OAuth callback"""
    if error:
        # OAuth error occurred
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <h1>Authentication Error</h1>
            <p>{error}</p>
            <script>
                window.opener.postMessage({{type: 'oauth_error', error: '{error}'}}, '*');
                window.close();
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    if not code or not state:
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <h1>Authentication Error</h1>
            <p>Missing authorization code or state</p>
            <script>
                window.opener.postMessage({type: 'oauth_error', error: 'Missing code or state'}, '*');
                window.close();
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    # Verify state
    if state not in _oauth_states:
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <h1>Authentication Error</h1>
            <p>Invalid state token</p>
            <script>
                window.opener.postMessage({type: 'oauth_error', error: 'Invalid state'}, '*');
                window.close();
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    try:
        # Exchange code for token
        flow = get_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store token data (in production, store in DB)
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'id_token': credentials.id_token if hasattr(credentials, 'id_token') else None
        }
        
        # Use state as session_id for now
        session_id = state
        _oauth_tokens[session_id] = token_data
        
        # Get user info
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        import json
        
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        # Prepare data for postMessage (properly escaped via JSON)
        token_data = {
            'type': 'oauth_success',
            'token': {
                'session_id': session_id,
                'access_token': credentials.token,
                'user_info': {
                    'id': user_info.get('id', ''),
                    'email': user_info.get('email', ''),
                    'name': user_info.get('name', ''),
                    'picture': user_info.get('picture', '')
                }
            }
        }
        
        # Send token to parent window via postMessage
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Authentication Successful</title></head>
        <body>
            <h1>Authentication Successful!</h1>
            <p>You can close this window.</p>
            <script>
                window.opener.postMessage({json.dumps(token_data)}, '*');
                window.close();
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
        
    except Exception as e:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <h1>Authentication Error</h1>
            <p>Failed to exchange token: {str(e)}</p>
            <script>
                window.opener.postMessage({{type: 'oauth_error', error: '{str(e)}'}}, '*');
                window.close();
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html)


def verify_google_token(session_id: str) -> Optional[dict]:
    """Verify and return token data for a session"""
    return _oauth_tokens.get(session_id)


def get_user_info_from_token(token_data: dict) -> Optional[dict]:
    """Get user info from stored token"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        creds = Credentials(
            token=token_data['token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes']
        )
        
        user_info_service = build('oauth2', 'v2', credentials=creds)
        user_info = user_info_service.userinfo().get().execute()
        return user_info
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None

async def handle_google_auth(websocket: WebSocket, auth_message: dict):
    session_id = auth_message.get('session_id')
    token_data = verify_google_token(session_id) if session_id else None
    
    if token_data:
        user_info = get_user_info_from_token(token_data)
        if user_info:
            # Store user info with connection
            if user_info.get('email') in member_list:
                manager.set_guest_number(websocket, user_info.get('id', 'unknown'))
                await websocket.send_json({
                    'type': 'google_auth_success',
                    'user_info': {
                        'id': user_info.get('id'),
                        'email': user_info.get('email'),
                        'name': user_info.get('name'),
                        'picture': user_info.get('picture')
                    }
                })
                # Continue to message loop after successful auth
            else:
                await websocket.send_json({
                    'type': 'google_auth_error',
                    'message': "You're not a community member"
                })
                await websocket.close()
                return
        else:
            await websocket.send_json({
                'type': 'google_auth_error',
                'message': 'Failed to get user info'
            })
            await websocket.close()
            return
    else:
        await websocket.send_json({
            'type': 'google_auth_error',
            'message': 'Invalid session or token expired'
        })
        await websocket.close()
        return
