# Changelog

## [Current] - Chat History Loading & Code Cleanup

### Added
- **Chat History Loading**
  - Server sends chat history when game loads
  - Client displays all previous chat messages on game load
  - Chat history retrieved from SQLite database
  - `clearChat()` function to reset chat display

### Changed
- **WebSocket Message Flow** (`python/websocket.py`)
  - `load_game` action now sends chat history to requesting client
  - Chat history formatted and sent as `{type: 'chat_history', messages: [...]}`
  - Only requesting client receives chat history (not broadcast)

- **Client Message Handling** (`javaScript/StoC.js`)
  - Handles `chat_history` message type
  - Automatically loads all historical messages into chat log
  - Chat cleared when new game is created

- **Documentation**
  - Removed `NOTES/NOTE.md` (consolidated into other docs)

---

## [Previous] - WebSocket Improvements & Game State Management

### Added
- Game ID management in localStorage
- Game creation confirmation (`game_created` message)
- Connection cleanup for dead WebSocket connections
- UI enhancements (guest number display, chat styling)

### Changed
- All game actions require `game_id` in messages
- Improved error handling and connection state management
- Better game state synchronization

---

## [Earlier] - Authentication & Architecture Refactoring

### Added
- **Authentication System** (`python/auth.py`)
  - Guest ID management with persistent guest numbers
  - UUID-based client identification

- **Modular JavaScript Architecture**
  - `CtoS.js` - Client-to-server communication
  - `StoC.js` - Server-to-client message handling
  - Clear separation of concerns

- **SQLite Chat Storage** (`python/chat.py`)
  - Session-based chat tables
  - Persistent chat messages across server restarts

### Changed
- Replaced `middle.js` with modular structure
- WebSocket authentication flow
- Documentation moved to `NOTES/` directory

---

## [Initial] - Project Setup

- Basic game functionality
- WebSocket communication
- FastAPI server setup
- Frontend UI components

---

## Future Improvements

- Multiple concurrent game sessions
- User accounts and persistent authentication
- Game state persistence
- Character movement visualization
- Skill system implementation
- Reconnection handling
