"""
FastAPI server with WebSocket support for game initialization
"""
from re import A
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .game import Game
#import json
import uuid
from .chat import init_database, save_chat, get_chat_history
from datetime import datetime
import traceback
from .auth import get_or_assign_guest_number
#import os

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
        self.game_connections: dict[str, list[WebSocket]] = {}  # {game_id: [websocket1, websocket2, ...]}
        self.connection_to_game: dict[WebSocket, str] = {}  # {websocket: game_id}
        self.connection_to_guest: dict[WebSocket, int] = {}  # {websocket: guest_number}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        await self.leave_game(websocket)
    
    def set_guest_number(self, websocket: WebSocket, guest_number: int):
        """Store guest_number for a connection"""
        self.connection_to_guest[websocket] = guest_number
    
    async def join_game(self, websocket: WebSocket, game_id: str):
        """Assign a connection to a game session"""
        if game_id not in self.game_connections:
            self.game_connections[game_id] = []
        if websocket not in self.game_connections[game_id]:
            self.game_connections[game_id].append(websocket)
        self.connection_to_game[websocket] = game_id
    
    async def leave_game(self, websocket: WebSocket):
        """Remove connection from its game and send leave message"""
        game_id = self.connection_to_game.get(websocket)
        
        if game_id and game_id in self.game_connections:
            if websocket in self.game_connections[game_id]:
                self.game_connections[game_id].remove(websocket)
        
        self.connection_to_game.pop(websocket, None)
        self.connection_to_guest.pop(websocket, None)
    
    async def broadcast_to_game(self, game_id: str, message: dict):
        """Broadcast message only to connections in a specific game"""
        if game_id not in self.game_connections:
            return
        dead_connections = []
        for connection in self.game_connections[game_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        
        # Cleanup dead connections
        for dead_conn in dead_connections:
            if dead_conn in self.game_connections[game_id]:
                self.game_connections[game_id].remove(dead_conn)
            self.connection_to_game.pop(dead_conn, None)
            if dead_conn in self.active_connections:
                self.active_connections.remove(dead_conn)
    
    def get_game_connections(self, game_id: str) -> list[WebSocket]:
        """Get list of connections for a game"""
        return self.game_connections.get(game_id, [])
    
    def get_game_id(self, websocket: WebSocket) -> str | None:
        """Get game_id for a connection"""
        return self.connection_to_game.get(websocket)

manager = ConnectionManager()

@app.get("/")
async def read_root():
    return FileResponse("index.html")
    # For absolute path, use
    # BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/room.html")
async def read_room():
    return FileResponse("room.html")

@app.get("/api/sessions")
async def list_sessions():
    """Return list of active game sessions for the lobby"""
    return {
        "sessions": [
            {
                "game_id": game_id,
                "player_count": len(manager.get_game_connections(game_id)),
                "status": "active"
            }
            for game_id, game in sessions.items()
        ]
    }

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
            message = await websocket.receive_json()  # Already parses to Python dict (JSON)
            now = datetime.now().isoformat()  # Full ISO format: "2024-01-15T14:30:45.123456"
            
            # print('Server received message:', message)
            if message.get("action") == "create_game":
                game_id = uuid.uuid4().hex[:10].upper() # generate a random session id
                sessions[game_id] = Game(game_id) # create a new game session
                init_database(game_id)
                
                # Auto-join creator to the game
                await manager.join_game(websocket, game_id)

                msg = save_chat(game_id, "System", now, f"Game {game_id} started.", "system")
                await manager.broadcast_to_game(game_id, msg)
                await websocket.send_json({
                    'type': 'game_created',
                    'game_id': game_id
                })
                continue
            
            # Handle join_game
            if message.get("action") == "join_game":
                game_id = message.get("game_id")
                if game_id and game_id in sessions:
                    await manager.join_game(websocket, game_id)
                    await websocket.send_json({
                        'type': 'joined_game',
                        'game_id': game_id
                    })
                else:
                    await websocket.send_json({
                        'type': 'join_failed',
                        'message': 'Game not found'
                    })
                continue
            
            # Get the game_id for this connection (from message or connection tracking)
            game_id = message.get("game_id") or manager.get_game_id(websocket)
            if not game_id or game_id not in sessions:
                await websocket.send_json({"type": "no_game"})
                continue
            game = sessions[game_id]

            # Handle load_game
            if message.get("action") == "load_game":
                vomit_data = game.vomit()
                # Send to requesting client only
                await websocket.send_json(vomit_data)
                
                # Load and send chat history to the requesting client
                chat_history_rows = get_chat_history(game_id)
                chat_messages = []
                for row in chat_history_rows:
                    # row format: (id, sender, time, content, sort)
                    chat_messages.append({
                        "type": "chat",
                        "sender": row[1],
                        "time": row[2],
                        "content": row[3],
                        "sort": row[4]
                    })
                
                # Send chat history only to the requesting client
                await websocket.send_json({
                    "type": "chat_history",
                    "messages": chat_messages
                })
                continue
            
            # Handle end_game
            if message.get("action") == "end_game":
                msg = save_chat(game_id, "System", now, f"Game {game_id} ended.", "system")
                await manager.broadcast_to_game(game_id, msg)
                # Remove all connections from this game
                connections = manager.get_game_connections(game_id)
                for conn in connections:
                    manager.connection_to_game.pop(conn, None)
                manager.game_connections.pop(game_id, None)
                del sessions[game_id]
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
                await manager.broadcast_to_game(game_id, msg)
                continue
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()
    finally:
        # Always disconnect when WebSocket closes
        await manager.disconnect(websocket)

    