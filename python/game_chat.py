'''
Purpose: SQLite database operations for chat messages
Responsibilities:
Initialize database (create table if it doesn't exist)
Store chat messages
Retrieve chat history (by session_id, by time range, etc.)
Handle database connections
'''
import sqlite3
import os

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
            sort TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_chat(session_id, sender, time, content, sort):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT INTO "{session_id}" (sender, time, content, sort) 
        VALUES (?, ?, ?, ?)
    ''', (sender, time, content, sort))
    conn.commit()
    conn.close()
    return {"type": "chat", "sender": sender, "time": time, "content": content, "sort": sort}

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

def kill_database():
    """Delete all tables in the chat.db database."""
    try:
        # Check if database file exists
        if not os.path.exists(DATABASE_PATH):
            print(f"Database file '{DATABASE_PATH}' does not exist.")
            return
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        # Get all user tables (exclude sqlite system tables)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database.")
            conn.close()
            return
        
        print(f"Found {len(tables)} table(s) to delete:")
        deleted_count = 0
        for table in tables:
            table_name = table[0]
            print(f"  - Dropping table: {table_name}")
            try:
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                deleted_count += 1
            except Exception as e:
                print(f"    Error dropping table {table_name}: {e}")
        
        conn.commit()
        conn.close()
        print(f"Successfully deleted {deleted_count} table(s).")
    except Exception as e:
        print(f"Error killing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Killing all chat tables in database...")
    kill_database()
    print("All done.")
