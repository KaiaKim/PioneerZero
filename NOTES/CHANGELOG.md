# Changelog

## [Current] - Multi-Session Lobby & Room System

### Added
- **Lobby System** (`index.html`)
  - Game lobby page showing active sessions
  - "New Game" button to create sessions
  - Clickable session list to join games

- **Game Room Page** (`room.html`)
  - Dedicated page for individual game sessions
  - Opens in new tab with game_id URL parameter
  - Auto-joins game on load

- **Session Management**
  - Track active game sessions in lobby
  - Join/leave game functionality
  - Per-game connection tracking

### Changed
- **Connection Management** (`python/websocket.py`)
  - Connections tracked per game session
  - `broadcast_to_game()` sends messages only to players in same game
  - Join/leave game messages
  - Guest tracking per connection

- **Client Architecture** (`javaScript/`)
  - Lobby displays active sessions
  - Room page auto-joins game on load
  - Session list updates dynamically
  - Multiple tabs can join different games

---

## [Previous] - Chat History Loading

### Added
- Chat history loading on game start
- `clearChat()` function

### Changed
- Server sends chat history when game loads
- Client displays historical messages

---

## [Earlier] - Core Features

- Authentication system with guest numbers
- Modular JavaScript (CtoS.js, StoC.js)
- SQLite chat storage
- Game state management
- WebSocket improvements

---

## Future Improvements

- Multiple concurrent game sessions
- User accounts
- Game state persistence
- Character movement visualization
