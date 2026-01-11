# Changelog

## [Current] - React Migration Complete

### Added
- **React Frontend Architecture**
  - Complete migration from vanilla JavaScript to React 18.2.0
  - React Router DOM 6.20 for client-side routing
  - Vite 5.0 build system for modern development workflow
  - Component-based architecture with reusable React components

- **React Components**
  - `src/components/auth.jsx` - Authentication component with Google OAuth integration
  - `src/components/lobby.jsx` - Lobby/session selection component
  - `src/components/gameRoom.jsx` - Complete game room component with full game functionality

- **Custom React Hooks**
  - `src/hooks/useAuth.js` - Authentication state management and OAuth flow
  - `src/hooks/useGame.js` - Game state, WebSocket management, and game actions
  - `src/hooks/useLobby.js` - Lobby state, session management, and game creation

- **Project Infrastructure**
  - `src/App.jsx` - Main React application with React Router setup
  - `src/main.jsx` - React entry point and DOM mounting
  - `vite.config.js` - Vite configuration for React development
  - `package.json` - React dependencies, build scripts, and project metadata
  - `public/` directory structure for static assets (images, audio)

- **Documentation**
  - `NOTES/ARCHITECTURE_DIAGRAMS.md` - System architecture and component diagrams
  - `NOTES/MIGRATION_PLAN.md` - Detailed migration planning documentation
  - `NOTES/SETUP_INSTRUCTIONS.md` - Setup, installation, and development guide

### Changed
- **Frontend Architecture**
  - Migrated from vanilla JavaScript to React functional components
  - Replaced direct DOM manipulation with React state management
  - Implemented React Router for navigation (`/` for lobby, `/room/:gameId` for game rooms)
  - Moved all frontend code from `javaScript/` to `src/` directory structure
  - Converted HTML-based pages to React component-based single-page application

- **Backend Enhancements**
  - Enhanced `python/game_ws.py` with improved WebSocket message handling
  - Updated `python/game_core.py` with cleaner Game class implementation
  - Improved `python/util.py` ConnectionManager with better connection tracking
  - Refined `python/main.py` with better routing, error handling, and API organization
  - Updated `python/auth_google.py` and `python/auth_guest.py` for React integration

- **Asset Organization**
  - Moved images to `public/images/` directory for Vite asset handling
  - Moved audio files to `public/audio/` directory
  - Preserved legacy files in `old/` directory for reference and rollback capability

- **UI and User Experience**
  - Player list refactoring with improved state management
  - User list functionality with real-time updates
  - Connection status visualizer for WebSocket connectivity
  - Enhanced chat styling and message display
  - Improved game room layout and user interactions
  - Better error handling and user feedback

### Removed
- **Deprecated Frontend Files**
  - Old vanilla JavaScript files moved to `old/javaScript/` directory
  - Legacy HTML files (`room.html`, `index.html`) moved to `old/` directory
  - Legacy image and audio files moved to `old/images/` and `old/audio/`

### Technical Details
- React 18.2.0 with functional components and hooks pattern
- Vite 5.0 for fast HMR (Hot Module Replacement) and optimized production builds
- React Router DOM 6.20 for declarative client-side routing
- Maintained WebSocket connection management through React hooks
- State management through custom hooks and React component state
- Component-based architecture for improved code reusability and maintainability
- Modern ES6+ JavaScript with JSX syntax

---

## [Previous] - UI Redesign & Layout Improvements

### Added
- **New Visual Assets**
  - Added 4 new background images for game environments
  - Enhanced visual library with Shutterstock stock images

- **Chat Filtering System**
  - Added chat filter checkboxes (All, System, Chat, Story) in room interface
  - Filter controls for different message types and categories
  - Improved message organization and readability

- **Layout Components**
  - New left menu bar with Google sign-in button integration
  - New right menu bar placeholder for future features
  - Restructured game screen with CSS Grid-based layout system

### Changed
- **Room Page Layout**
  - Restructured `room.html` with new menu system architecture
  - Moved Google sign-in button to dedicated left menu bar
  - Changed default display states: waiting room visible, floor-3d hidden by default
  - Updated vomit-box styling and positioning for better visibility
  - Improved right panel layout and spacing for better UX

- **Styling Updates**
  - Major `room.css` overhaul with modern grid-based layout system
  - Added full-screen game screen with background image (`sky2.jpg`)
  - Updated button color scheme in `global.css` (black background, white text)
  - Enhanced chat log container styling with black background for contrast
  - Improved right panel styling with new color scheme
  - Better z-index management for menu overlays and layering

- **Game Frontend**
  - Commented out BGM autoplay functionality in `game_front.js`
  - Removed autoplay fallback event listeners for browser compatibility

### Technical Details
- Full viewport grid layout for game screen
- Fixed positioning for menu bars with proper z-index stacking
- Improved overflow handling for chat and game containers
- Better visual hierarchy with z-index layering system

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
