"""
Utility functions and classes for the FastAPI server
"""
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and game assignments"""
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


# Singleton ConnectionManager instance
manager = ConnectionManager()

