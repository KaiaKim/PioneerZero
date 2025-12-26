# Changelog

## [Current] - Critical Bug Fix: Multi-Tab Game ID Management

### Fixed
- **Critical Bug: Game ID Storage Conflict**
  - Fixed critical issue where multiple game tabs shared the same `game_id` from localStorage
  - Resolved bug where chat messages from one tab were incorrectly sent to other games
  - Changed `getGameId()` function to read from URL parameter instead of localStorage
  - Each browser tab now operates independently based on its URL parameter (`room.html?game_id=XXX`)

- **Backend Game ID Validation**
  - Backend now exclusively uses `game_id` from message payload, never from connection tracking
  - All game actions (`load_game`, `chat`, `end_game`, `join_game`) now require `game_id` in message
  - Improved error handling with clear messages for missing or invalid `game_id`

- **Game End Behavior**
  - `end_game` action now only broadcasts "Game ended" message to all players
  - Removed automatic player disconnection on game end (archival requirement)
  - Games remain fully accessible in memory and database after ending
  - All game data is preserved for historical access

### Changed
- **Frontend Game ID Management**
  - `getGameId()` function now reads from URL search parameters instead of localStorage
  - Removed `setGameId()` function and all localStorage operations for `game_id`
  - Game creation flow now opens room page directly with `game_id` in URL parameter
  - Removed localStorage cleanup from `endGame()` function
  - `game_front.js` no longer stores `game_id` in localStorage on page load

- **Backend Action Routing**
  - Unified `game_id` retrieval pattern: all actions require `game_id` in message
  - Improved action routing order in `main.py` WebSocket handler
  - Better error messages: `"no_game_id"` for missing game_id, `"game_not_found"` for invalid game_id
  - `join_game` action now follows same pattern as other game actions

- **Game Creation Flow**
  - Game creation now automatically opens new tab with game room URL
  - Removed localStorage dependency for game navigation
  - Direct URL-based game access for better multi-tab support

### Technical Details
- Each browser tab maintains its own `game_id` from URL parameter
- No shared state between tabs for `game_id` management
- Backend validates `game_id` presence before processing any game action
- Games are archived (not deleted) when ended, maintaining full history
- URL-based game identification enables proper multi-tab functionality

---

## [Previous] - Authentication & UI Improvements

### Changed
- **Authentication System**
  - Enhanced Google OAuth flow with improved error handling
  - Updated guest authentication with better session management
  - Improved WebSocket authentication integration
  - Refined token verification and user info retrieval

- **UI & Styling**
  - Updated lobby and room page layouts
  - Enhanced global CSS styles
  - Improved button styling and visual consistency
  - Better user interface responsiveness

- **Backend**
  - Streamlined `main.py` with cleaner router organization
  - Enhanced chat functionality integration
  - Improved WebSocket connection handling

---

## [Previous] - Google OAuth Authentication

### Added
- **Google OAuth Integration**
  - `python/auth_google.py` - Backend OAuth handlers and token verification
  - `javaScript/auth_google.js` - Frontend OAuth flow with popup window
  - Google OAuth login button in lobby (`index.html`)
  - Google logo image (`images/google2.png`)
  - `.env.example` - Environment variable template

- **Authentication Features**
  - Google Sign-In with OAuth 2.0 flow
  - Popup-based OAuth authentication
  - User info retrieval (name, email, profile)
  - Token-based session management
  - WebSocket integration for authenticated users
  - LocalStorage persistence for authenticated sessions

### Changed
- **Authentication System**
  - Updated `python/main.py` to include OAuth router
  - Enhanced WebSocket endpoint to handle Google authentication
  - Modified `javaScript/lobby_ws.js` to support authenticated sessions
  - Updated `javaScript/game_ws.js` for authenticated game connections
  - Improved `javaScript/global.js` with auth utilities
  - Renamed `python/auth.py` → `python/auth_guest.py`

- **UI Updates**
  - Added "Sign in with Google" button to lobby interface
  - Updated `style/lobby.css` with OAuth button styling
  - Enhanced user greeting display with authenticated user info

### Technical Details
- Uses `google-auth-oauthlib` and `google-auth` Python libraries
- OAuth 2.0 flow with state verification for security
- Token storage and verification system
- Seamless integration with existing guest authentication fallback

---

## [Previous] - Code Refactoring & Modular Architecture

### Added
- **Backend Module Separation**
  - `game_core.py` - Game logic and session management
  - `game_chat.py` - Chat database operations
  - `game_ws.py` - Game WebSocket handlers
  - `lobby_ws.py` - Lobby WebSocket handlers
  - `util.py` - ConnectionManager and utility functions

- **Frontend Utilities**
  - `global.js` - Shared utility functions (game_id, chat helpers)

### Changed
- **Code Organization**
  - Split monolithic `websocket.py` into focused modules
  - Separated lobby and game WebSocket logic
  - Better separation of concerns
  - Improved code maintainability

- **File Renames**
  - `game.py` → `game_core.py`
  - `temp_char.py` → `temp_character.py`
  - `chat.py` → `game_chat.py`

---

## [Previous] - Multi-Session Lobby & Room System

### Added
- Lobby system with active session list
- Game room page (`room.html`)
- Per-game connection tracking
- Join/leave game functionality

---

## [Earlier] - Core Features

- Authentication system
- Modular JavaScript architecture
- SQLite chat storage
- Chat history loading
- WebSocket improvements

---

## Future Improvements

- User accounts
- Game state persistence
- Character movement visualization
- Skill system implementation
