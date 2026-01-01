"""
Utility functions and classes for the FastAPI server
"""

from fastapi import WebSocket
import sqlite3
import os


class ConnectionManager:
    """Manages WebSocket connections and game assignments"""
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.game_connections: dict[str, list[WebSocket]] = {}  # {game_id: [websocket1, websocket2, ...]}
        self.connection_to_game: dict[WebSocket, str] = {}  # {websocket: game_id}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        await self.leave_game(websocket)
    
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


class DatabaseManager:
    def __init__(self):
        self.DATABASE_PATH = 'chat.db'
        self.conn = sqlite3.connect(self.DATABASE_PATH)
        self.cursor = self.conn.cursor()

    def create_chat_table(self, session_id):
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{session_id}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                time TEXT,
                content TEXT,
                sort TEXT
            )
        ''')
        self.conn.commit()

    def save_chat(self, session_id, sender, time, content, sort):
        self.cursor.execute(f'''
            INSERT INTO "{session_id}" (sender, time, content, sort) 
            VALUES (?, ?, ?, ?)
        ''', (sender, time, content, sort))
        self.conn.commit()
        return {"type": "chat", "sender": sender, "time": time, "content": content, "sort": sort}

    def get_chat_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        chat_tables = [row[0] for row in self.cursor.fetchall()]
        return chat_tables

    def get_chat_history(self, session_id, limit=None):
        query = f'SELECT * FROM "{session_id}"'
        if limit:
            query += f' LIMIT {limit}'
        self.cursor.execute(query)
        messages = self.cursor.fetchall()
        return messages

    def restore_game_from_chat(self, session_id):
        """Load a Game object from chat history. For now, creates a new Game instance."""
        from .game_core import Game
        # TODO: Reconstruct Game state from chat_history if needed
        # For now, return a new Game instance with the session_id
        game = Game(session_id)
        return game

    def kill_all_chat_tables(self):
        """Delete all tables in the chat.db database."""
        try:
            # Check if database file exists
            if not os.path.exists(self.DATABASE_PATH):
                print(f"Database file '{self.DATABASE_PATH}' does not exist.")
                return
            
            # Get all user tables (exclude sqlite system tables)
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = self.cursor.fetchall()
            
            if not tables:
                print("No tables found in database.")
                return
            
            print(f"Found {len(tables)} table(s) to delete:")
            deleted_count = 0
            for table in tables:
                table_name = table[0]
                print(f"  - Dropping table: {table_name}")
                try:
                    self.cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                    deleted_count += 1
                except Exception as e:
                    print(f"    Error dropping table {table_name}: {e}")
            
            self.conn.commit()
            print(f"Successfully deleted {deleted_count} table(s).")
        except Exception as e:
            print(f"Error killing database: {e}")
            import traceback
            traceback.print_exc()

# class instance
dbmanager = DatabaseManager()
conmanager = ConnectionManager()

