# Technical Documentation

## Project Architecture

### Overview
This is a real-time multiplayer game application built with FastAPI (Python backend) and vanilla JavaScript (frontend), using WebSocket for bidirectional communication and SQLite for persistent chat storage.

---

## File Structure

### Frontend (`javaScript/`)

#### `CtoS.js` (Client-to-Server)
Handles all outgoing messages from client to server.

**Key Functions:**
- `sendMessage()` - Sends chat messages to server
- `startGame()` - Initiates a new game session
- `loadGame()` - Requests current game state
- `endGame()` - Terminates the current game session

**Message Types Sent:**
- `{type: 'chat', sender: 'Pikita', content: '...'}` - Chat messages
- `{action: 'start_game'}` - Start new game
- `{action: 'load_game'}` - Load existing game
- `{action: 'end_game', session_id: '...'}` - End game
- `{action: 'authenticate', guest_id: '...'}` - Authenticate connection

#### `StoC.js` (Server-to-Client)
Handles all incoming messages from server to client.

**Key Features:**
- WebSocket connection management
- Guest ID management (stored in localStorage)
- Message routing and parsing
- UI state management

**Message Types Received:**
- `{type: 'guest_assigned', guest_number: N}` - Guest number assignment
- `{type: 'vomit_data', game_id: '...', characters: [...]}` - Game state data
- `{type: 'chat', sender: '...', time: '...', content: '...', sort: 'user'|'system'}` - Chat messages
- `{type: 'no_game'}` - No active game session

#### `front.js`
UI manipulation and view management functions.

---

### Backend (`python/`)

#### `websocket.py`
FastAPI WebSocket server handling all game logic and communication.

**Key Components:**
- `ConnectionManager` - Manages active WebSocket connections
- `sessions` - Dictionary storing active game sessions (game_id -> Game instance)
- Authentication flow on connection
- Message routing and command processing

**Message Flow:**
1. Client connects → Server waits for authentication
2. Client sends `{action: 'authenticate', guest_id: '...'}`
3. Server assigns guest number and sends confirmation
4. Normal message loop begins

**Actions Handled:**
- `start_game` - Creates new game session, initializes chat database
- `load_game` - Sends current game state to all clients
- `end_game` - Removes game session, broadcasts end message
- `chat` - Processes chat messages and commands

**Command Processing:**
Chat messages starting with `/` are treated as commands:
- `/이동 ...` - Player movement commands
- `/스킬 ...` - Skill usage (placeholder)
- `/행동 ...` - Action commands (placeholder)

#### `chat.py`
SQLite database operations for persistent chat storage.

**Database Structure:**
- One table per game session (table name = session_id)
- Each table stores: `id`, `sender`, `time`, `content`, `sort`

**Key Functions:**
- `init_database(session_id)` - Creates session-specific chat table
- `save_chat(session_id, sender, time, content, sort)` - Stores message, returns formatted message object
- `get_chat_history(session_id, limit=None)` - Retrieves chat history
- `kill_database()` - Utility to delete all chat tables

**Database File:**
- `chat.db` - SQLite database file (excluded from git)

#### `auth.py`
Guest authentication and session management.

**Key Functions:**
- `get_or_assign_guest_number(guest_id)` - Maps client UUID to persistent guest number
- `get_guest_number(guest_id)` - Retrieves guest number without assignment
- `remove_guest(guest_id)` - Removes guest mapping on disconnect

**How It Works:**
1. Client generates/retrieves UUID from localStorage
2. Client sends UUID to server on connection
3. Server maps UUID to sequential guest number (1, 2, 3, ...)
4. Same UUID always gets same guest number (persistent across reconnects)

#### `game.py`
Game logic and state management (character positions, game rules, etc.)

---

## Data Flow

### Connection Flow
```
1. Client: WebSocket connection to ws://localhost:8000/ws
2. Server: Accepts connection, waits for authentication
3. Client: Sends {action: 'authenticate', guest_id: 'uuid-from-localStorage'}
4. Server: Assigns guest_number, sends {type: 'guest_assigned', guest_number: N}
5. Client: Stores guest_number in localStorage
6. Normal message loop begins
```

### Chat Message Flow
```
1. User types message → CtoS.js sendMessage()
2. Client: ws.send({type: 'chat', sender: 'Pikita', content: '...'})
3. Server: Receives in websocket.py
4. Server: Checks if message starts with '/' (command)
   - If command: Process command, create system message
   - If regular chat: Store as user message
5. Server: save_chat() → Stores in SQLite database
6. Server: Broadcasts formatted message to all clients
7. Clients: Receive in StoC.js, display via loadChat()
```

### Game Start Flow
```
1. User clicks "Start Game" → CtoS.js startGame()
2. Client: ws.send({action: 'start_game'})
3. Server: Generates game_id (10-char hex)
4. Server: Creates Game instance, stores in sessions[game_id]
5. Server: init_database(game_id) → Creates chat table
6. Server: Saves system message "Game {game_id} started."
7. Server: Broadcasts system message
8. Client: Calls loadGame() to request game state
9. Server: Sends vomit_data with game state
10. Client: Receives vomit_data, displays game view
```

### Game Load Flow
```
1. Client connects → StoC.js connectWebSocket()
2. Client: Automatically calls loadGame()
3. Client: ws.send({action: 'load_game'})
4. Server: Checks if sessions exist
   - If no sessions: Sends {type: 'no_game'}
   - If sessions exist: Gets first session, sends vomit_data
5. Client: Receives vomit_data or no_game, updates UI accordingly
```

---

## Database Schema

### Chat Tables (Dynamic)
Each game session gets its own table named after the session_id:

```sql
CREATE TABLE "{session_id}" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    time TEXT,
    content TEXT,
    sort TEXT  -- 'user' or 'system'
);
```

**Notes:**
- Table names are session IDs (e.g., "A1B2C3D4E5")
- Tables are created on game start
- Messages are stored with ISO timestamp format
- `sort` field distinguishes user messages from system messages

---

## WebSocket Message Protocol

### Client → Server Messages

**Authentication:**
```json
{
  "action": "authenticate",
  "guest_id": "uuid-string"
}
```

**Chat:**
```json
{
  "type": "chat",
  "sender": "Pikita",
  "content": "Hello world"
}
```

**Game Actions:**
```json
{
  "action": "start_game"
}
```
```json
{
  "action": "load_game"
}
```
```json
{
  "action": "end_game",
  "session_id": "A1B2C3D4E5"
}
```

### Server → Client Messages

**Guest Assignment:**
```json
{
  "type": "guest_assigned",
  "guest_number": 1
}
```

**Game Data:**
```json
{
  "type": "vomit_data",
  "game_id": "A1B2C3D4E5",
  "characters": [...],
  ...
}
```

**Chat:**
```json
{
  "type": "chat",
  "sender": "Pikita",
  "time": "2024-01-15T14:30:45.123456",
  "content": "Hello world",
  "sort": "user"
}
```

**System Messages:**
```json
{
  "type": "chat",
  "sender": "System",
  "time": "2024-01-15T14:30:45.123456",
  "content": "Game A1B2C3D4E5 started.",
  "sort": "system"
}
```

**No Game:**
```json
{
  "type": "no_game"
}
```

---

## Key Design Decisions

1. **Modular JavaScript Architecture**
   - Clear separation: CtoS (outgoing) vs StoC (incoming)
   - Easier to maintain and debug
   - Single responsibility principle

2. **Session-Based Chat Storage**
   - Each game session has its own chat table
   - Chat history persists across server restarts
   - Easy to query and manage per-session

3. **Guest Authentication**
   - Client-side UUID generation (localStorage)
   - Server-side sequential numbering
   - Persistent identity across reconnects

4. **Command System**
   - Chat messages starting with `/` are commands
   - Commands processed server-side
   - Results broadcast as system messages

5. **Broadcast Communication**
   - All messages broadcast to all connected clients
   - Real-time synchronization
   - Simple but effective for small-scale multiplayer

---

## Development Notes

### Starting the Server
```bash
python -m uvicorn python.websocket:app --host 0.0.0.0 --port 8000 --reload
```

### Database Management
- Database file: `chat.db` (auto-created)
- To clear all chat tables: Run `python -m python.chat` (calls `kill_database()`)

### Testing
- Open `http://localhost:8000` in browser
- Multiple browser tabs = multiple clients
- All clients see same game state and chat

### Known Limitations
- Single game session at a time (sessions dictionary)
- Guest numbers reset on server restart
- No user accounts or persistent authentication
- Chat history not loaded on game load (only new messages)
