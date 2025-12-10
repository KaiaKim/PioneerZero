# Changelog

## Latest Update - Code Refactoring & Chat System Enhancement

### 📁 **JavaScript Architecture Refactoring**

#### New Files:
- **`javaScript/CtoS.js`** (Client-to-Server)
  - Handles all client-to-server communication
  - Functions: `sendMessage()`, `startGame()`, `loadGame()`, `endGame()`
  - Manages WebSocket message sending to server

- **`javaScript/StoC.js`** (Server-to-Client)
  - Handles all server-to-client message receiving
  - WebSocket connection management
  - Message parsing and routing:
    - `vomit_data` - Game state data
    - `chat` - Chat messages (user and system)
    - `no_session` - No active game session

#### Removed Files:
- **`javaScript/middle.js`** - Replaced by the new modular structure (CtoS.js and StoC.js)

#### Modified Files:
- **`javaScript/front.js`** - Updated to work with new module structure
- **`index.html`** - Updated script imports:
  - Removed: `middle.js`
  - Added: `CtoS.js`, `StoC.js`

### 🐍 **Python Backend Updates**

#### New Files:
- **`python/chat.py`** - SQLite database operations for chat persistence
  - `init_database(session_id)` - Creates session-specific chat tables
  - `save_chat()` - Stores chat messages in database
  - `get_chat_history()` - Retrieves chat history for a session
  - `kill_database()` - Utility to clear all chat tables

#### Modified Files:
- **`python/websocket.py`**
  - Integrated SQLite chat storage
  - Chat messages now persist across server restarts
  - Improved message handling with `sort` field (user/system)
  - Better error handling and logging

- **`python/game.py`** - Minor updates for compatibility

### 📝 **Documentation**

#### New Files:
- **`LOAD.md`** - Server startup instructions
  - How to start FastAPI server with uvicorn
  - Command reference and troubleshooting tips
  - Network configuration options

- **`NOTE.md`** - Technical documentation
  - SQLite chat storage implementation guide
  - Dataflow diagrams
  - Database schema documentation
  - Integration points and code examples

### 🔧 **Configuration**

- **`.gitignore`** - Updated to exclude database files (`*.db`, `*.sqlite`, `*.sqlite3`)

### 🎯 **Key Improvements**

1. **Modular JavaScript Architecture**
   - Clear separation of concerns (CtoS vs StoC)
   - Easier to maintain and debug
   - Better code organization

2. **Persistent Chat Storage**
   - Chat messages saved to SQLite database
   - Chat history persists across server restarts
   - Session-based chat isolation

3. **Improved Message Handling**
   - Chat messages now have `sort` field (user/system)
   - Better message type differentiation
   - More robust WebSocket communication

4. **Better Documentation**
   - Server setup instructions
   - Technical implementation details
   - Code structure explanations

### 📊 **Statistics**
- **Files Added:** 4 (CtoS.js, StoC.js, chat.py, LOAD.md, NOTE.md)
- **Files Removed:** 1 (middle.js)
- **Files Modified:** 5 (index.html, front.js, websocket.py, game.py, .gitignore)
- **Total Changes:** ~323 insertions, ~199 deletions

---

## Previous Updates

### Initial Commit
- Project structure setup
- Basic game functionality
- WebSocket communication
- Frontend UI components

