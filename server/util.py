"""
Utility functions and classes for the FastAPI server
"""

from fastapi import WebSocket
import sqlite3
import os
from datetime import datetime
import time


class ConnectionManager:
    """Manages WebSocket connections and game assignments"""
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.game_connections: dict[str, list[WebSocket]] = {}  # {game_id: [websocket1, websocket2, ...]}
        self.connection_to_game: dict[WebSocket, str] = {}  # {websocket: game_id}
        self.connection_user_info: dict[WebSocket, dict] = {}  # {websocket: user_info}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # leave_game is now called separately to get return values
        self.connection_user_info.pop(websocket, None)
    
    def set_user_info(self, websocket: WebSocket, user_info: dict):
        """Store user_info for a connection"""
        self.connection_user_info[websocket] = user_info
    
    def get_user_info(self, websocket: WebSocket) -> dict | None:
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
        if message.get('sort') == 'secret':
            target_user_id = message.get('user_id')
            if target_user_id:
                for connection in self.game_connections[game_id]:
                    user_info = self.connection_user_info.get(connection)
                    if user_info and user_info.get('id') == target_user_id:
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


class DatabaseManager:
    def __init__(self):
        self.DATABASE_PATH = 'chat.db'
        self.conn = sqlite3.connect(self.DATABASE_PATH)
        self.cursor = self.conn.cursor()

    def create_chat_table(self, game_id):
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{game_id}" (
                chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                time TEXT,
                content TEXT,
                sort TEXT,
                user_id TEXT
            )
        ''')
        self.conn.commit()

    def save_chat(self, game_id, content, sort="system", sender="System", user_id=None, time=None):
        if time is None:
            time = datetime.now().isoformat()

        self.cursor.execute(f'''
            INSERT INTO "{game_id}" (sender, time, content, sort, user_id) 
            VALUES (?, ?, ?, ?, ?)
        ''', (sender, time, content, sort, user_id))
        self.conn.commit()
        return {"type": "chat", "sender": sender, "time": time, "content": content, "sort": sort, "user_id": user_id}

    def get_chat_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        chat_tables = [row[0] for row in self.cursor.fetchall()]
        return chat_tables

    def get_chat_history(self, game_id, viewer_id=None, limit=None):
        query = f'SELECT chat_id, sender, time, content, sort, user_id FROM "{game_id}"'
        ## TODO: is combat state is 'combat ended', show all messages
        
        # Exclude secret messages that don't belong to the viewer
        if viewer_id:
            query += f" WHERE (sort != 'secret' OR user_id = ?)"
            params = (viewer_id,)
        else:
            # If no viewer_id, exclude all secret messages
            query += f" WHERE sort != 'secret'"
            params = ()
        
        if limit:
            query += f' LIMIT {limit}'
        
        self.cursor.execute(query, params)
        messages = self.cursor.fetchall()
        return messages

    def restore_game_from_chat(self, game_id):
        """Load a Game object from chat history. For now, creates a new Game instance."""
        from .game_core import Game
        # TODO: Reconstruct Game state from chat_history if needed
        # For now, return a new Game instance with the game_id
        game = Game(game_id)
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

class TimeManager:
    def __init__(self):
        self.timer_type = 'session'
        self.duration = None
        self.start_time = None
        self.pause_time = None
        self.elapsed_time = 0
        self.is_paused = False
        self.is_running = False

    def start_timer(self, timer_type='session', duration=None):
        self.timer_type = timer_type
        self.duration = duration
        self.start_time = time.time()
        self.is_running = True
        self.is_paused = False
        self.pause_time = None
        self.elapsed_time = 0
    
    def stop_timer(self):
        """Stop the timer"""
        
    def pause_timer(self):
        """Pause the timer (preserves elapsed time)"""
        
    def resume_timer(self):
        """Resume a paused timer"""
        
    def reset_timer(self):
        """Reset timer to initial state"""
        
    def get_timer_state(self):
        """Get current timer state (elapsed time, remaining time if countdown)"""
        
    def update_timer_type(self, timer_type, duration=None):
        """Change timer type and optionally set new duration"""

# class instance
dbmanager = DatabaseManager()
conmanager = ConnectionManager()
timemanager = TimeManager()
