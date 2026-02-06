"""
Database access: chat tables, game sessions, rooms.
"""
import sqlite3
import os
from datetime import datetime

from ..config import settings


class DatabaseManager:
    def __init__(self, database_path: str = None):
        self.DATABASE_PATH = database_path or settings.DATABASE_PATH
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
        from ..services.game_core.session import Game
        game = Game.json_to_dict(state_json)
        game.player_num = player_num
        game.phase_sec = phase_sec
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


dbM = DatabaseManager()
