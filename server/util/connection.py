"""
WebSocket connection and game assignment management.
"""
from fastapi import WebSocket

from .models import UserInfo


class ConnectionManager:
    """Manages WebSocket connections and game assignments"""
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.game_connections: dict[str, list[WebSocket]] = {}  # {game_id: [websocket1, websocket2, ...]}
        self.connection_to_game: dict[WebSocket, str] = {}  # {websocket: game_id}
        self.connection_user_info: dict[WebSocket, UserInfo] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.connection_user_info.pop(websocket, None)

    def set_user_info(self, websocket: WebSocket, user_info: UserInfo) -> None:
        """Store user_info for a connection"""
        self.connection_user_info[websocket] = user_info

    def get_user_info(self, websocket: WebSocket) -> UserInfo | None:
        """Get user_info for a connection"""
        return self.connection_user_info.get(websocket)
    
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
        user_info = self.connection_user_info.get(websocket)
        
        if game_id and game_id in self.game_connections:
            if websocket in self.game_connections[game_id]:
                self.game_connections[game_id].remove(websocket)
        
        self.connection_to_game.pop(websocket, None)
        
        # Return game_id and user_info for cleanup in main.py
        return game_id, user_info
    
    def _cleanup_dead_connections(self, dead_connections: list, game_id: str):
        """Helper method to cleanup dead connections"""
        for dead_conn in dead_connections:
            if dead_conn in self.game_connections[game_id]:
                self.game_connections[game_id].remove(dead_conn)
            self.connection_to_game.pop(dead_conn, None)
            if dead_conn in self.active_connections:
                self.active_connections.remove(dead_conn)

    async def broadcast_to_game(self, game_id: str, message: dict):
        """Broadcast message only to connections in a specific game"""
        if game_id not in self.game_connections:
            return
        
        dead_connections = []
        
        # For secret messages, only send to connections with matching user_id
        if message.get('sort') == 'secret' or message.get('sort') == 'error':
            target_user_id = message.get('user_id')
            if target_user_id:
                for connection in self.game_connections[game_id]:
                    user_info = self.connection_user_info.get(connection)
                    if user_info and user_info.id == target_user_id:
                        try:
                            await connection.send_json(message)
                        except Exception:
                            dead_connections.append(connection)
                self._cleanup_dead_connections(dead_connections, game_id)
            return
        
        # Regular broadcast for non-secret messages
        for connection in self.game_connections[game_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        
        self._cleanup_dead_connections(dead_connections, game_id)
    
    def get_game_connections(self, game_id: str) -> list[WebSocket]:
        """Get list of connections for a game"""
        return self.game_connections.get(game_id, [])
    
    def get_game_id(self, websocket: WebSocket) -> str | None:
        """Get game_id for a connection"""
        return self.connection_to_game.get(websocket)


conM = ConnectionManager()
