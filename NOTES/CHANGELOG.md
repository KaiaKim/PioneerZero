# Changelog

All notable changes to this project will be documented in this file.

---

## [Current] - Latest Updates

### Added
- **Authentication System** (`python/auth.py`)
  - Guest ID management using client-provided UUIDs
  - Persistent guest number assignment (1, 2, 3, ...)
  - Guest numbers persist across reconnects for same UUID
  - Server logs guest connections and reconnections

- **Documentation Organization**
  - Moved all documentation to `NOTES/` directory
  - Better file organization and structure

### Changed
- **WebSocket Connection Flow**
  - Added authentication step before normal message handling
  - Client must send `{action: 'authenticate', guest_id: '...'}` on connection
  - Server assigns and returns guest number
  - Improved connection reliability

- **Client-Side Guest Management** (`javaScript/StoC.js`)
  - Automatic UUID generation and storage in localStorage
  - Guest ID sent to server on WebSocket connection
  - Guest number stored in localStorage for display

### Technical Details
- Guest authentication happens before any game actions
- Server closes connection if authentication fails
- Guest numbers are sequential and persistent per UUID

---

## [Previous] - Code Refactoring & Chat System Enhancement

### Added

#### JavaScript Architecture Refactoring
- **`javaScript/CtoS.js`** (Client-to-Server)
  - Handles all client-to-server communication
  - Functions: `sendMessage()`, `startGame()`, `loadGame()`, `endGame()`
  - Manages WebSocket message sending to server
  - Clean separation of outgoing message logic

- **`javaScript/StoC.js`** (Server-to-Client)
  - Handles all server-to-client message receiving
  - WebSocket connection management
  - Message parsing and routing:
    - `vomit_data` - Game state data
    - `chat` - Chat messages (user and system)
    - `no_game` - No active game session
    - `guest_assigned` - Guest number assignment
  - Automatic game loading on connection

#### Python Backend
- **`python/chat.py`** - SQLite database operations for chat persistence
  - `init_database(session_id)` - Creates session-specific chat tables
  - `save_chat()` - Stores chat messages in database
  - `get_chat_history()` - Retrieves chat history for a session
  - `kill_database()` - Utility to clear all chat tables
  - Session-based table structure (one table per game session)

#### Documentation
- **`NOTES/LOAD.md`** - Server startup instructions
  - How to start FastAPI server with uvicorn
  - Command reference and troubleshooting tips
  - Network configuration options
  - Common issues and solutions

- **`NOTES/NOTE.md`** - Technical documentation
  - Complete architecture documentation
  - Dataflow diagrams
  - Database schema documentation
  - WebSocket message protocol
  - Integration points and code examples

### Changed

#### File Structure
- **Removed:** `javaScript/middle.js` - Replaced by modular structure (CtoS.js and StoC.js)
- **Modified:** `javaScript/front.js` - Updated to work with new module structure
- **Modified:** `index.html` - Updated script imports:
  - Removed: `middle.js`
  - Added: `CtoS.js`, `StoC.js`

#### Backend Updates
- **`python/websocket.py`**
  - Integrated SQLite chat storage
  - Chat messages now persist across server restarts
  - Improved message handling with `sort` field (user/system)
  - Command processing for chat messages starting with `/`
  - Better error handling and logging
  - Session-based game management

- **`python/game.py`** - Updates for compatibility with new architecture

#### Configuration
- **`.gitignore`** - Updated to exclude database files (`*.db`, `*.sqlite`, `*.sqlite3`)

### Improvements

1. **Modular JavaScript Architecture**
   - Clear separation of concerns (CtoS vs StoC)
   - Easier to maintain and debug
   - Better code organization
   - Single responsibility principle

2. **Persistent Chat Storage**
   - Chat messages saved to SQLite database
   - Chat history persists across server restarts
   - Session-based chat isolation
   - One table per game session for easy management

3. **Improved Message Handling**
   - Chat messages now have `sort` field (user/system)
   - Better message type differentiation
   - More robust WebSocket communication
   - Command system for game actions via chat

4. **Better Documentation**
   - Server setup instructions
   - Technical implementation details
   - Code structure explanations
   - Dataflow documentation

### Statistics
- **Files Added:** 5 (CtoS.js, StoC.js, chat.py, auth.py, LOAD.md, NOTE.md)
- **Files Removed:** 1 (middle.js)
- **Files Modified:** 5 (index.html, front.js, websocket.py, game.py, .gitignore)
- **Total Changes:** ~450+ insertions, ~200 deletions

---

## [Initial] - Project Setup

### Added
- Project structure setup
- Basic game functionality
- WebSocket communication
- Frontend UI components
- FastAPI server setup
- Static file serving
- Basic game session management

---

## Future Improvements

### Planned
- Load chat history when game loads
- Multiple concurrent game sessions
- User accounts and persistent authentication
- Chat history pagination
- Better error handling and reconnection logic
- Game state persistence
- Character movement visualization
- Skill system implementation

### Under Consideration
- Redis for session management
- WebSocket connection pooling
- Rate limiting for chat messages
- Message encryption
- Admin panel for game management
