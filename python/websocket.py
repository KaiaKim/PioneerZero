"""
FastAPI server with WebSocket support for game initialization
"""
from re import A
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .game import Game
import json
import uuid
from .chat import init_database, save_chat
from datetime import datetime
import traceback
from .auth import get_or_assign_guest_number


app = FastAPI()

# Store active game sessions
sessions = {}

# Serve static files
app.mount("/style", StaticFiles(directory="style"), name="style")
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/javaScript", StaticFiles(directory="javaScript"), name="javaScript")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    game_id = None

    try:
        # Wait for authentication message first
        auth_message = await websocket.receive_json()
        guest_id = auth_message.get('guest_id')
        
        if not guest_id or auth_message.get('action') != 'authenticate':
            # Handle error - no guest_id provided
            await websocket.close()
        
        # Get or assign guest number
        guest_number = get_or_assign_guest_number(guest_id)
        
        # Send guest_number back to client (optional, for display)
        await websocket.send_json({
            'type': 'guest_assigned',
            'guest_number': guest_number
        })


        # Now continue with normal message loop
        while True:
            message = await websocket.receive_json()  # Already parses to Python dict (JSON)
            now = datetime.now().isoformat()  # Full ISO format: "2024-01-15T14:30:45.123456"
            
            # Handle start_game (doesn't need session check)
            if message.get("action") == "start_game":
                game_id = uuid.uuid4().hex[:10].upper() # generate a random session id
                sessions[game_id] = Game(game_id) # create a new game session
                init_database(game_id)

                msg = save_chat(game_id, "System", now, f"Game {game_id} started.", "system")
                await manager.broadcast(msg)
                continue
            
            # For all other actions, check if session exists first
            if not sessions:
                await manager.broadcast({"type": "no_game"})
                continue
            
            # Get the game_id for this connection
            game_id, game = next(iter(sessions.items()))
            
            # Handle load_game
            if message.get("action") == "load_game":
                vomit_data = game.vomit()
                #print("load_game vomit_data: ", vomit_data)
                await manager.broadcast(vomit_data)
                continue
            
            # Handle end_game
            if message.get("action") == "end_game":
                my_id = message.get("game_id")
                if my_id and my_id in sessions:
                    del sessions[my_id]
                    msg = save_chat(my_id, "System", now, f"Game {my_id} ended.", "system")
                    await manager.broadcast(msg)
                continue
            
            # Handle chat
            if message.get("type") == "chat":
                content = message.get("content", "")
                sender = message.get("sender")
                
                if content and content[0] == "/":
                    command = content[1:]
                    result = "unknown command"
                    if "이동" in command:
                        result = sessions[game_id].move_player(sender, command)
                    elif "스킬" in command:
                        result = "스킬 사용함"
                    elif "행동" in command:
                        result = "행동함"
                    msg = save_chat(game_id, "System", now, result, "system") 
                else:
                    msg = save_chat(game_id, sender, now, content, "user")
                await manager.broadcast(msg)
                continue

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        traceback.print_exc()
        
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()

    