"""
Utility functions and classes for the FastAPI server
"""

from fastapi import WebSocket
import sqlite3
import os
from datetime import datetime
import asyncio
import json



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
        if message.get('sort') == 'secret' or message.get('sort') == 'error':
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
        self.DATABASE_PATH = 'main.db'
        self.conn = sqlite3.connect(self.DATABASE_PATH)
        self.cursor = self.conn.cursor()
        self.create_game_sessions_table()

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
        return [name for name in chat_tables if name != "rooms"]

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

    def restore_game_from_chat(self, game_id, game=None):
        """No-op: load_game_session handles restore for now."""
        return

    def create_game_sessions_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                game_id TEXT PRIMARY KEY,
                updated_at TEXT,
                player_num INTEGER,
                phase_sec INTEGER,
                max_round INTEGER,
                state_json TEXT
            )
        ''')
        self.conn.commit()

    def save_game_session(self, game):
        updated_at = datetime.now().isoformat()
        state_json = game.dict_to_json()
        self.cursor.execute('''
            INSERT INTO rooms (game_id, updated_at, player_num, phase_sec, max_round, state_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                updated_at = excluded.updated_at,
                player_num = excluded.player_num,
                phase_sec = excluded.phase_sec,
                max_round = excluded.max_round,
                state_json = excluded.state_json
        ''', (
            game.id,
            updated_at,
            game.player_num,
            game.phase_sec,
            game.max_rounds,
            state_json
        ))
        self.conn.commit()

    def load_game_session(self, game_id):
        self.cursor.execute('''
            SELECT state_json, player_num, phase_sec, max_round
            FROM rooms
            WHERE game_id = ?
        ''', (game_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        state_json, player_num, phase_sec, max_round = row
        from .game_core import Game
        game = Game.json_to_dict(state_json)
        if player_num:
            game.player_num = player_num
        if phase_sec:
            game.phase_sec = phase_sec
        if max_round:
            game.max_rounds = max_round
        return game

    def get_room_ids(self):
        self.cursor.execute("SELECT game_id FROM rooms")
        return [row[0] for row in self.cursor.fetchall()]

    def kill_all_chat_tables(self):
        """Delete all tables in the main.db database."""
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
            self.create_game_sessions_table()
            print(f"Successfully deleted {deleted_count} table(s).")
        except Exception as e:
            print(f"Error killing database: {e}")
            import traceback
            traceback.print_exc()

class TimeManager:
    def __init__(self):
        pass

    def cancel_phase_timer(self, game):
        task = getattr(game, "phase_timer_task", None)
        current_task = asyncio.current_task()
        if task and not task.done() and task is not current_task:
            task.cancel()

    async def offset_timer(self,game):
        seconds = game.offset_sec
        for i in range(seconds):
            await conM.broadcast_to_game(game.id, {
                "type": "offset_timer",
                "seconds": seconds - i
            })
            await asyncio.sleep(1)
        await conM.broadcast_to_game(game.id, {
            "type": "offset_timer",
            "seconds": 0
        })

    async def phase_timer(self,game):
        seconds = game.phase_sec # 10의 배수
        for i in range(seconds):
            await asyncio.sleep(1)
            if i % 10 == 0:
                await conM.broadcast_to_game(game.id, {
                    "type": "phase_timer",
                    "seconds": seconds - i
                })
        await conM.broadcast_to_game(game.id, {
            "type": "phase_timer",
            "seconds": 0
        })



# class instance
dbM = DatabaseManager()
conM = ConnectionManager()
timeM = TimeManager()
