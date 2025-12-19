"""
Global variables and core server setup for the FastAPI server
"""
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import traceback
from .util import manager

# FastAPI app instance
app = FastAPI()

# Store active game sessions # move to DB later
sessions = {}

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
    from .auth import get_or_assign_guest_number
    from . import lobby_ws, game_ws
    
    await manager.connect(websocket)
    game_id = None

    try:
        # Wait for authentication message first
        auth_message = await websocket.receive_json()
        guest_id = auth_message.get('guest_id')
        
        if not guest_id or auth_message.get('action') != 'authenticate':
            # Handle error - no guest_id provided
            await websocket.close()
            print("Error: no guest_id provided")
            return
        
        # Get or assign guest number
        guest_number = get_or_assign_guest_number(guest_id)
        manager.set_guest_number(websocket, guest_number)
        
        # Send guest_number back to client (optional, for display)
        await websocket.send_json({
            'type': 'guest_assigned',
            'guest_number': guest_number
        })

        # Now continue with normal message loop
        while True:
            message = await websocket.receive_json()
            
            # Route lobby actions
            if message.get("action") == "create_game":
                await lobby_ws.handle_create_game(websocket)
                continue

            if message.get("action") == "list_games":
                await websocket.send_json(await lobby_ws.list_sessions())
                continue

            if message.get("action") == "join_game":
                await lobby_ws.handle_join_game(websocket, message)
                continue
            
            # Get the game_id for this connection (from message or connection tracking)
            game_id = message.get("game_id") or manager.get_game_id(websocket)
            if not game_id or game_id not in sessions:
                await websocket.send_json({"type": "no_game"})
                continue
            game = sessions[game_id]

            # Route game actions
            if message.get("action") == "load_game":
                await game_ws.handle_load_game(websocket, game_id, game)
                continue
            
            if message.get("action") == "end_game":
                await game_ws.handle_end_game(websocket, game_id)
                continue
            
            if message.get("type") == "chat":
                await game_ws.handle_chat(websocket, message, game_id)
                continue
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()
    finally:
        # Always disconnect when WebSocket closes
        await manager.disconnect(websocket)

