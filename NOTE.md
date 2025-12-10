Explaining which files to add/edit and the dataflow for implementing SQLite chat storage:


[2 tools called]

## Files to add/edit

### 1. New file: `python/chat_storage.py`
Purpose: SQLite database operations for chat messages

Responsibilities:
- Initialize database (create table if it doesn't exist)
- Store chat messages
- Retrieve chat history (by session_id, by time range, etc.)
- Handle database connections

Key functions:
- `init_database()` - Create table on startup
- `save_message(session_id, sender, time, content, message_type)` - Store a message
- `get_chat_history(session_id, limit=None)` - Retrieve messages for a session
- `get_recent_messages(session_id, count=50)` - Get last N messages

### 2. Edit: `python/websocket.py`
Changes needed:
- Import `chat_storage` module
- Initialize database on startup
- Store messages when received (line 78 area)
- Send chat history when game loads (in `load_game` block)
- Store system messages too

### 3. Optional: `python/database.py` or `python/db.py`
Alternative: If you want to expand to store game sessions too later, you could create a more general database module.

### 4. Auto-created: `chat.db` or `game.db`
SQLite will automatically create this file in your project root (or wherever you specify the path).

## Dataflow

### Current flow (without storage):
```
Client → WebSocket → Server → Broadcast to clients
```

### New flow (with SQLite storage):

#### 1. Server startup:
```
Server starts → chat_storage.init_database() → Creates chat.db and messages table
```

#### 2. User sends chat message:
```
Client sends chat → WebSocket receives → Store in SQLite → Broadcast to clients
```

Detailed steps:
1. Client: `ws.send({type: "user_chat", sender: "Pikita", time: "...", content: "..."})`
2. Server receives in `websocket.py` line 69
3. Before broadcasting (line 78), call `chat_storage.save_message(session_id, sender, time, content, "user_chat")`
4. Then broadcast to clients as before

#### 3. Game loads (load_game action):
```
Client requests load_game → Server retrieves chat history from SQLite → Send to client along with game data
```

Detailed steps:
1. Client sends `{action: "load_game"}`
2. Server finds game session (line 51)
3. Get chat history: `chat_history = chat_storage.get_chat_history(session_id)`
4. Send game data + chat history to client
5. Client displays chat history in chat log

#### 4. System messages:
```
Server generates system message → Store in SQLite → Broadcast to clients
```

Example: When game starts (line 41-44), also store the system message in the database.

## Database schema

Table: `messages`
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    time TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT NOT NULL,  -- 'user_chat' or 'system_message'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Indexes:
- `session_id` (for fast retrieval by session)
- `created_at` (for chronological ordering)

## Integration points

### In `websocket.py`:

1. Import (top of file):
   ```python
   from .chat_storage import init_database, save_message, get_chat_history
   ```

2. Initialize on startup (after app creation):
   ```python
   init_database()
   ```

3. Store user chat (line 78 area):
   ```python
   elif message.get("type") == "user_chat":
       # ... existing command handling ...
       # Store before broadcasting
       save_message(session_id, sender, time, content, "user_chat")
       await websocket.send_json(message)
   ```

4. Store system messages (line 41-44, 65):
   ```python
   save_message(session_id, "System", timestamp, content, "system_message")
   ```

5. Send chat history on load_game (line 46-58):
   ```python
   elif message.get("action") == "load_game":
       if game_sessions:
           session_id, game = next(iter(game_sessions.items()))
           vomit_data = game.vomit()
           await websocket.send_json(vomit_data)
           
           # Send chat history
           chat_history = get_chat_history(session_id)
           await websocket.send_json({
               "type": "chat_history",
               "messages": chat_history
           })
   ```

## Client-side changes

### In `javaScript/back.js`:

Handle `chat_history` message type:
```javascript
else if (msg.type === "chat_history") {
    // Load all historical messages into chat log
    msg.messages.forEach(msg => {
        loadChat(msg.sender, msg.time, msg.content, msg.message_type === "system_message");
    });
}
```

## Summary

Files:
- New: `python/chat_storage.py` (database operations)
- Edit: `python/websocket.py` (integrate storage)
- Edit: `javaScript/back.js` (handle chat history)
- Auto-created: `chat.db` (SQLite database file)

Dataflow:
1. Startup: Initialize database
2. Chat sent: Store → Broadcast
3. Game load: Retrieve history → Send to client
4. System messages: Store → Broadcast

This keeps chat data persistent across server restarts and allows loading chat history when a game session is restored.
