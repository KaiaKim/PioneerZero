"""
Global variables and core server setup for the FastAPI server
"""
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import traceback
from dotenv import load_dotenv
from .util import conmanager, dbmanager
from . import auth_guest
from . import auth_google
import uuid



# Load environment variables from .env file
load_dotenv()

# Global game sessions dictionary: {game_id: Game object}
# Games are loaded lazily from the database when accessed
sessions = {}

# FastAPI app instance
app = FastAPI()

# Include OAuth router
app.include_router(auth_google.router)


# Serve static files
app.mount("/style", StaticFiles(directory="style"), name="style")
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/javaScript", StaticFiles(directory="javaScript"), name="javaScript")


# HTTP endpoints for serving HTML files
@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/room.html")
async def read_room():
    return FileResponse("room.html")

# Main WebSocket endpoint - routes messages to appropriate handlers
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Lazy imports to avoid circular dependency
    from . import lobby_ws, game_ws
    
    await conmanager.connect(websocket)

    try:
        # Wait for authentication message first
        auth_message = await websocket.receive_json()
        auth_action = auth_message.get('action')

        # Handle Google OAuth authentication
        if auth_action == 'authenticate_google':
            await auth_google.handle_google_auth(websocket, auth_message)
        # Handle guest authentication (existing flow)
        elif auth_action == 'authenticate_guest':
            await auth_guest.handle_guest_auth(websocket, auth_message)
        else:
            await websocket.close()
            print("Error: invalid authentication action")
            return

        # Now continue with normal message loop
        while True:
            message = await websocket.receive_json()
            action = message.get("action")

            if action == "kill_db":
                #Clean up chat tables for prototype purpose only. Do not use in production.
                dbmanager.kill_all_chat_tables()
                sessions.clear()
                continue

            # Route lobby actions
            if action == "create_game":
                game_id = uuid.uuid4().hex[:10].upper()  # generate a random session id
                sessions[game_id] = await lobby_ws.handle_create_game(websocket, game_id)  # create a new game session
                continue

            if action == "list_games":
                chat_tables = dbmanager.get_chat_tables()
                await lobby_ws.handle_list_sessions(websocket, chat_tables)
                continue


            if action == "join_game":
                game_id =  message.get("game_id")
                if not game_id:
                    await websocket.send_json({"type": "no_game_id"})
                    continue
                try:
                    game = sessions[game_id]
                except KeyError:
                    await websocket.send_json({"type": "game_not_found"})
                    continue
                await lobby_ws.handle_join_game(websocket, game_id)
                continue

            # Get the game_id for this connection (from message or connection tracking)
            game_id =  message.get("game_id") or conmanager.get_game_id(websocket)
            try:
                game = sessions[game_id]
            except KeyError:
                await websocket.send_json({"type": "game_not_found"})
                continue

            # Route game actions
            if action == "load_game":
                await game_ws.handle_load_game(websocket, game)
                continue
            
            if action == "end_game":
                await game_ws.handle_end_game(websocket, game_id)
                continue
            
            if action == "chat":
                await game_ws.handle_chat(websocket, message, game)
                continue
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()
    finally:
        # Always disconnect when WebSocket closes
        await conmanager.disconnect(websocket)

