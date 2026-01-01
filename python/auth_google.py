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
from .util import conmanager

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
async def google_login(request: Request, session_id: Optional[str] = None):
    """Initiate Google OAuth login - accepts session_id from client query parameter"""
    # Use provided session_id or generate one for CSRF protection
    if not session_id:
        session_id = secrets.token_urlsafe(32)
    
    # Store state (in production, associate with session)
    _oauth_states[session_id] = session_id
    
    # Create OAuth flow
    flow = get_flow()
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=session_id,
        prompt='consent'
    )
    
    return RedirectResponse(url=authorization_url)


@router.get("/auth/google/callback")
async def google_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    """Handle Google OAuth callback - stores token and sends postMessage to parent window"""
    import json
    
    if error:
        # Send error to parent window
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{type: 'oauth_error', error: {json.dumps(error)}}}, '*');
                }}
                setTimeout(() => window.close(), 1000);
            </script>
            <p>Authentication error: {error}</p>
        </body>
        </html>
        """
        if state:
            _oauth_tokens[state] = {'error': error}
        return HTMLResponse(content=error_html)
    
    if not code or not state:
        error_msg = 'Missing authorization code or state'
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{type: 'oauth_error', error: {json.dumps(error_msg)}}}, '*');
                }}
                setTimeout(() => window.close(), 1000);
            </script>
            <p>Authentication error: {error_msg}</p>
        </body>
        </html>
        """
        if state:
            _oauth_tokens[state] = {'error': error_msg}
        return HTMLResponse(content=error_html)
    
    # Verify state
    if state not in _oauth_states:
        error_msg = 'Invalid state token'
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{type: 'oauth_error', error: {json.dumps(error_msg)}}}, '*');
                }}
                setTimeout(() => window.close(), 1000);
            </script>
            <p>Authentication error: {error_msg}</p>
        </body>
        </html>
        """
        _oauth_tokens[state] = {'error': error_msg}
        return HTMLResponse(content=error_html)
    
    try:
        # Exchange code for token
        flow = get_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store token data (in production, store in DB)
        # Use state as session_id
        session_id = state
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'id_token': credentials.id_token if hasattr(credentials, 'id_token') else None
        }
        _oauth_tokens[session_id] = token_data
        
        # Send success message to parent window with session_id
        success_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Authentication Successful</title></head>
        <body>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'oauth_success',
                        session_id: {json.dumps(session_id)}
                    }}, '*');
                }}
                setTimeout(() => window.close(), 500);
            </script>
            <p>Authentication successful! Closing window...</p>
        </body>
        </html>
        """
        return HTMLResponse(content=success_html)
        
    except Exception as e:
        # Send error to parent window
        error_msg = f'Failed to exchange token: {str(e)}'
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{type: 'oauth_error', error: {json.dumps(error_msg)}}}, '*');
                }}
                setTimeout(() => window.close(), 1000);
            </script>
            <p>Authentication error: {error_msg}</p>
        </body>
        </html>
        """
        _oauth_tokens[state] = {'error': error_msg}
        return HTMLResponse(content=error_html)


def verify_google_token(session_id: str) -> Optional[dict]:
    """Verify and return token data for a session"""
    return _oauth_tokens.get(session_id)


def get_user_info_from_token(token_data: dict) -> Optional[dict]:
    """Get user info from stored token, with token refresh if needed"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        
        creds = Credentials(
            token=token_data['token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes']
        )
        
        # Refresh token if expired
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update stored token with new access token
                token_data['token'] = creds.token
                print("Token refreshed successfully")
            except Exception as refresh_error:
                print(f"Error refreshing token: {refresh_error}")
                return None
        
        user_info_service = build('oauth2', 'v2', credentials=creds)
        user_info = user_info_service.userinfo().get().execute()
        return user_info
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None

async def handle_google_login(websocket: WebSocket, auth_message: dict):
    """Handle Google OAuth authentication via WebSocket - sends responses via websocket.send_json"""
    session_id = auth_message.get('session_id')
    print(f"Handling Google auth with session_id: {session_id}")
    token_data = verify_google_token(session_id) if session_id else None
    
    if not token_data:
        print(f"No token data found for session_id: {session_id}")
        await websocket.send_json({
            'type': 'auth_error',
            'message': 'Invalid session or token expired'
        })
        await websocket.close()
        return
    
    # Check if token_data contains an error from the callback
    if 'error' in token_data:
        await websocket.send_json({
            'type': 'auth_error',
            'message': token_data['error']
        })
        await websocket.close()
        # Clean up invalid token
        _oauth_tokens.pop(session_id, None)
        return
    
    # Get user info from token
    user_info = get_user_info_from_token(token_data)
    if not user_info:
        await websocket.send_json({
            'type': 'auth_error',
            'message': 'Failed to get user info'
        })
        await websocket.close()
        # Clean up invalid token
        _oauth_tokens.pop(session_id, None)
        return
    
    # Verify user is in member list
    if user_info.get('email') not in member_list:
        await websocket.send_json({
            'type': 'auth_error',
            'message': "You're not a community member"
        })
        await websocket.close()
        # Clean up token for non-member
        _oauth_tokens.pop(session_id, None)
        return
    
    # Success - send success message
    await websocket.send_json({
        'type': 'auth_success',
        'user_info': {
            'id': user_info.get('id'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'isGoogle': True,
            'isGuest': False
        }
    })
    print(f"Google authentication successful for user: {user_info.get('email')}")
    
    # Clean up OAuth state (keep token_data for potential future use if needed)
    # Remove state verification entry since it's no longer needed
    _oauth_states.pop(session_id, None)
    # Note: We keep token_data in _oauth_tokens in case we need to refresh later
    # In production, you might want to store this in a database with expiration
    
    # Continue to message loop after successful auth
