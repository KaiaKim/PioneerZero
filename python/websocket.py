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
    session_id = None
    
    try:
        while True:
            message = await websocket.receive_json()  # Already parses to Python dict (JSON)
            #data = await websocket.receive_json() #receive text?
            #message = json.loads(data)
            now = datetime.now().isoformat()  # Full ISO format: "2024-01-15T14:30:45.123456"
            
            # Handle start_game (doesn't need session check)
            if message.get("action") == "start_game":
                session_id = uuid.uuid4().hex[:10].upper() # generate a random session id
                sessions[session_id] = Game(session_id) # create a new game session
                init_database(session_id)

                msg = save_chat(session_id, "System", now, f"Game session {session_id} started.", "system")
                await manager.broadcast(msg)
                continue
            
            # For all other actions, check if session exists first
            if not sessions:
                await manager.broadcast({"type": "no_session"})
                continue
            
            # Get the session_id for this connection
            session_id, game = next(iter(sessions.items()))
            
            # Handle load_game
            if message.get("action") == "load_game":
                vomit_data = game.vomit()
                await manager.broadcast(vomit_data)
                continue
            
            # Handle end_game
            if message.get("action") == "end_game":
                my_id = message.get("session_id")
                if my_id and my_id in sessions:
                    del sessions[my_id]
                    msg = save_chat(my_id, "System", now, f"Game session {my_id} ended.", "system")
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
                        result = sessions[session_id].move_player(sender, command)
                    elif "스킬" in command:
                        result = "스킬 사용함"
                    elif "행동" in command:
                        result = "행동함"
                    msg = save_chat(session_id, "System", now, result, "system") 
                else:
                    msg = save_chat(session_id, sender, now, content, "user")
                await manager.broadcast(msg)
                continue

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()

    