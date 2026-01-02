# Changelog

## [Current] - React Migration Complete

### Added
- **React Frontend Architecture**
  - Complete migration from vanilla JavaScript to React 18
  - React Router DOM for client-side routing
  - Vite build system for modern development workflow
  - Component-based architecture with reusable React components

- **React Components**
  - `src/components/auth.jsx` - Authentication component
  - `src/components/lobby.jsx` - Lobby/session selection component
  - `src/components/gameRoom.jsx` - Game room component with full game functionality

- **Custom React Hooks**
  - `src/hooks/useAuth.js` - Authentication state management hook
  - `src/hooks/useGame.js` - Game state and WebSocket management hook
  - `src/hooks/useLobby.js` - Lobby state and session management hook

- **Project Structure**
  - `src/App.jsx` - Main React application with routing
  - `src/main.jsx` - React entry point
  - `vite.config.js` - Vite configuration
  - `package.json` - React dependencies and build scripts
  - `public/` directory for static assets (images, audio)

- **Documentation**
  - `NOTES/ARCHITECTURE_DIAGRAMS.md` - System architecture documentation
  - `NOTES/MIGRATION_PLAN.md` - Migration planning documentation
  - `NOTES/SETUP_INSTRUCTIONS.md` - Setup and installation guide

### Changed
- **Frontend Architecture**
  - Migrated from vanilla JavaScript to React functional components
  - Replaced direct DOM manipulation with React state management
  - Implemented React Router for navigation (`/` for lobby, `/room/:gameId` for game rooms)
  - Moved all frontend code from `javaScript/` to `src/` directory structure

- **Backend Updates**
  - Enhanced `python/game_ws.py` with improved WebSocket handling
  - Updated `python/game_core.py` with cleaner Game class implementation
  - Improved `python/util.py` ConnectionManager functionality
  - Refined `python/main.py` with better routing and error handling
  - Updated `python/auth_google.py` and `python/auth_guest.py` for React integration

- **Asset Organization**
  - Moved images to `public/images/` directory
  - Moved audio files to `public/audio/` directory
  - Preserved old files in `old/` directory for reference

- **UI Improvements**
  - Player list refactoring and improvements
  - User list functionality
  - Connection status visualizer
  - Enhanced chat styling
  - Improved game room layout and interactions

### Removed
- **Deprecated Files**
  - Old vanilla JavaScript files moved to `old/javaScript/`
  - Old HTML files moved to `old/` directory
  - Legacy image files moved to `old/images/`

### Technical Details
- React 18.2.0 with functional components and hooks
- Vite 5.0 for fast development and optimized builds
- React Router DOM 6.20 for client-side routing
- Maintained WebSocket connection with React hooks
- State management through custom hooks and React context
- Component-based architecture for better maintainability

---

## [Previous] - UI Redesign & Layout Improvements

### Added
- **New Assets**
  - Added 4 new background images (`shutterstock_2447343523.jpg`, `shutterstock_2460491637.jpg`, `shutterstock_2493413181.jpg`, `shutterstock_2503971441.jpg`)

- **Chat Filtering System**
  - Added chat filter checkboxes (All, System, Chat, Story) in room interface
  - Filter controls for different message types

- **Layout Components**
  - New left menu bar with Google sign-in button
  - New right menu bar placeholder
  - Restructured game screen with grid-based layout

### Changed
- **Room Page Layout**
  - Restructured `room.html` with new menu system
  - Moved Google sign-in button to left menu bar
  - Changed default display states: waiting room visible, floor-3d hidden
  - Updated vomit-box styling and positioning
  - Improved right panel layout and spacing

- **Styling Updates**
  - Major `room.css` overhaul with grid-based layout system
  - Added full-screen game screen with background image (`sky2.jpg`)
  - Updated button color scheme in `global.css` (black background, white text)
  - Enhanced chat log container styling with black background
  - Improved right panel styling with new color scheme
  - Better z-index management for menu overlays

- **Game Frontend**
  - Commented out BGM autoplay functionality in `game_front.js`
  - Removed autoplay fallback event listeners

### Technical Details
- Full viewport grid layout for game screen
- Fixed positioning for menu bars
- Improved overflow handling for chat and game containers
- Better visual hierarchy with z-index layering

---

## [Previous] - Critical Bug Fix: Multi-Tab Game ID Management

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
