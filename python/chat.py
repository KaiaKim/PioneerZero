'''
Purpose: SQLite database operations for chat messages
Responsibilities:
Initialize database (create table if it doesn't exist)
Store chat messages
Retrieve chat history (by session_id, by time range, etc.)
Handle database connections
'''
import sqlite3

DATABASE_PATH = 'chat.db'

def init_database(session_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{session_id}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            time TEXT,
            content TEXT,
            message_type TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_message(session_id, sender, time, content, message_type):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT INTO "{session_id}" (sender, time, content, message_type) 
        VALUES (?, ?, ?, ?)
    ''', (sender, time, content, message_type))
    conn.commit()
    conn.close()

def get_chat_history(session_id, limit=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    query = f'SELECT * FROM "{session_id}"'
    if limit:
        query += f' LIMIT {limit}'
    cursor.execute(query)
    messages = cursor.fetchall()
    conn.close()
    return messages

