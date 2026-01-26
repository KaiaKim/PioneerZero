# Server File Structure & Dependencies

## Overview
This document maps all Python files in the `server/` directory, their dependencies, and their relationships.

**Current Structure (Option 1 - Domain-Driven):**
- **`routers/`** - All route handlers organized by domain (auth, lobby, game)
- **`services/`** - Business logic and core game functionality
- **`util.py`** - Shared utilities (ConnectionManager, DatabaseManager, TimeManager)
- **`main.py`** - FastAPI app setup and configuration

**Note:** 
- This structure follows FastAPI best practices for scalable applications
- Routes/handlers are grouped by feature/domain rather than by file type
- Business logic is separated from routing/handling logic

---

## File Index
```
server/
├── main.py              # App setup only
├── config.py            # Settings
├── util.py              # Shared utilities
├── routers/             # All route handlers
│   ├── __init__.py
│   ├── websocket.py     # WebSocket routing
│   ├── auth.py          # auth_google + auth_user merged
│   ├── lobby.py         # handle_lobby
│   └── game/            # Game-specific handlers
│       ├── __init__.py
│       ├── chat.py
│       ├── flow.py
│       └── slot.py
├── services/            # Business logic
│   ├── __init__.py
│   └── game/
│       ├── __init__.py
│       ├── core.py      # Game class only
│       ├── slot.py      # Slot management functions
│       ├── position.py  # Position management functions
│       └── characters.py # Character data constants
└── models/              # Data models (optional. Do not implement yet.)
    └── __init__.py
```

### Core Files

#### `main.py`
**Purpose:** FastAPI application setup and configuration  
**External Dependencies:**
- `fastapi` (FastAPI)
- `dotenv` (load_dotenv)

**Internal Dependencies:**
- `routers.websocket` - WebSocket routing logic
- `routers.auth` - Authentication router
- `util` (conM, dbM)

**Key Exports:**
- `app` (FastAPI instance)

**Key Functions:**
- `startup_event()` - Background tasks on server startup

---

#### `util.py`
**Purpose:** Utility functions and classes for the FastAPI server  
**External Dependencies:**
- `fastapi` (WebSocket)
- `sqlite3`
- `os`
- `datetime`
- `asyncio`
- `json`
- `time`

**Internal Dependencies:**
- None (local import of `Game` from `services.game.core` only in `load_game_session` method)

**Key Classes:**
- `ConnectionManager` (conM) - WebSocket connection management
- `DatabaseManager` (dbM) - SQLite database operations
- `TimeManager` (timeM) - Timer management for game phases

**Key Exports:**
- `conM` - ConnectionManager instance
- `dbM` - DatabaseManager instance
- `timeM` - TimeManager instance

---

### Router Files (`routers/`)

#### `routers/websocket.py`
**Purpose:** WebSocket endpoint routing and message handling  
**External Dependencies:**
- `fastapi` (WebSocket)
- `uuid`
- `traceback`
- `asyncio`

**Internal Dependencies:**
- `routers.auth` - Authentication handlers
- `routers.lobby` - Lobby handlers
- `routers.game.chat` - Chat handlers
- `routers.game.flow` - Flow handlers
- `routers.game.slot` - Slot handlers
- `services.game.core` (Game class)
- `util` (conM, dbM)

**Key Functions:**
- `websocket_endpoint()` - Main WebSocket endpoint routing

**Key Variables:**
- `rooms` - Global game sessions dictionary

---

#### `routers/auth.py`
**Purpose:** Authentication handlers (Google OAuth + guest sessions)  
**External Dependencies:**
- `fastapi` (APIRouter, Request, Response, WebSocket)
- `fastapi.responses` (RedirectResponse, HTMLResponse)
- `google_auth_oauthlib.flow` (Flow)
- `google.oauth2.credentials` (Credentials)
- `os`
- `secrets`
- `typing` (Dict, Optional)
- `dotenv` (load_dotenv)

**Internal Dependencies:**
- `util` (conM)

**Key Exports:**
- `router` - FastAPI router for OAuth endpoints

**Key Functions:**
- `google_login()` - Initiate Google OAuth login
- `google_callback()` - Handle OAuth callback
- `handle_google_login()` - Handle Google auth via WebSocket
- `handle_user_auth()` - Handle guest authentication
- `verify_google_token()` - Verify token data
- `get_user_info_from_token()` - Get user info from token

---

#### `routers/lobby.py`
**Purpose:** Lobby WebSocket handlers and endpoints  
**External Dependencies:**
- `fastapi` (WebSocket)

**Internal Dependencies:**
- `util` (conM, dbM)
- `services.game.core` (Game)

**Key Functions:**
- `handle_list_rooms()` - Return list of active game sessions
- `handle_create_room()` - Create new game session
- `handle_join_room()` - Join client to existing game
- `handle_load_room()` - Load room data for client

---

### Game Router Files (`routers/game/`)

#### `routers/game/chat.py`
**Purpose:** Chat message and command handling  
**External Dependencies:**
- `fastapi` (WebSocket)

**Internal Dependencies:**
- `util` (conM, dbM)
- `services.game.position` (for position management functions)

**Key Functions:**
- `handle_chat()` - Handle chat messages and commands

---

#### `routers/game/flow.py`
**Purpose:** Game phase flow management  
**External Dependencies:**
- `asyncio`

**Internal Dependencies:**
- `util` (conM, dbM, timeM)

**Key Functions:**
- `handle_phase()` - Phase wrapper/entry point
- `_phase_flow()` - Main phase flow logic
- `kickoff()` - Start combat
- `position_declaration()` - Position declaration phase
- `position_resolution()` - Position resolution phase
- `start_round()` - Start new round
- `action_declaration()` - Action declaration phase
- `action_resolution()` - Action resolution phase
- `end_round()` - End round and check win conditions
- `wrap_up()` - Combat wrap-up phase

---

#### `routers/game/slot.py`
**Purpose:** Game WebSocket handlers for player slot management  
**External Dependencies:**
- `fastapi` (WebSocket)
- `asyncio`

**Internal Dependencies:**
- `util` (conM)

**Key Functions:**
- `handle_join_player_slot()` - Add player to waiting room slot
- `handle_add_bot_to_slot()` - Add bot to waiting room slot
- `handle_leave_player_slot()` - Remove player from slot
- `handle_set_ready()` - Toggle ready state for player
- `run_connection_lost_timeout_checks()` - Background task for connection-lost timeouts

---

### Service Files (`services/`)

#### `services/game/core.py`
**Purpose:** Core Game class and game state management  
**External Dependencies:**
- `json`

**Internal Dependencies:**
- `services.game.slot` - Slot management functions
- `services.game.position` - Position management functions

**Key Classes:**
- `Game` - Main game state class

**Key Methods:**
- `declare_attack()` - Handle attack declarations
- `declare_skill()` - Handle skill declarations
- `dict_to_json()` - Serialize game state
- `json_to_dict()` - Deserialize game state
- `vomit()` - Export game data
- `check_all_players_defeated()` - Check win conditions

---

#### `services/game/slot.py`
**Purpose:** Slot management functions for player slot operations  
**External Dependencies:**
- `time`

**Internal Dependencies:**
- `services.game.characters` (default_character, bots)

**Key Functions:**
- `player_factory()` - Create new player slot dict
- `add_player()` - Add human player to slot
- `add_bot()` - Add bot player to slot
- `remove_player()` - Remove player from slot
- `set_player_connection_lost()` - Mark player as connection-lost
- `clear_expired_connection_lost_slots()` - Cleanup expired connection-lost slots
- `get_player_by_user_id()` - Find player slot by user ID
- `set_player_ready()` - Set player ready state
- `are_all_players_ready()` - Check if all players are ready

---

#### `services/game/position.py`
**Purpose:** Position management functions for coordinate operations  
**External Dependencies:**
- `re`

**Internal Dependencies:**
- `services.game.slot` (local import in `declare_position`)

**Key Functions:**
- `declare_position()` - Declare position for a player
- `move_player()` - Legacy move command handler
- `pos_to_rc()` - Convert position string to (row_idx, col_idx)
- `rc_to_pos()` - Convert (row_idx, col_idx) to position string
- `is_front_row()` - Check if position is front row
- `is_back_row()` - Check if position is back row
- `check_move_validity()` - Validate move destination

**Key Constants:**
- `ROW_MAP` - Row mapping dictionary
- `REV_ROW_MAP` - Reverse row mapping dictionary

---

#### `services/game/characters.py`
**Purpose:** Character data constants  
**External Dependencies:**
- None

**Internal Dependencies:**
- None

**Key Data:**
- `default_character` - Default character template
- `bots` - List of bot character definitions

---


## Dependency Graph

```
main.py
├── routers/websocket.py
│   ├── routers/auth.py
│   │   └── util.py (conM)
│   ├── routers/lobby.py
│   │   ├── util.py (conM, dbM)
│   │   └── services/game/core.py (Game)
│   ├── routers/game/chat.py
│   │   ├── util.py (conM, dbM)
│   │   └── services/game/position.py
│   ├── routers/game/flow.py
│   │   ├── util.py (conM, dbM, timeM)
│   │   └── services/game/slot.py
│   ├── routers/game/slot.py
│   │   ├── util.py (conM)
│   │   └── services/game/slot.py
│   ├── services/game/core.py (Game)
│   │   ├── services/game/slot.py
│   │   └── services/game/position.py
│   └── util.py (conM, dbM)
├── routers/auth.py
│   └── util.py (conM)
├── services/game/core.py
│   ├── services/game/slot.py
│   │   └── services/game/characters.py
│   └── services/game/position.py
│       └── services/game/slot.py (local import)
└── util.py (no module-level dependencies)
```

## Dependency Categories

### External Libraries
- **Web Framework:** `fastapi`
- **Database:** `sqlite3`
- **OAuth:** `google_auth_oauthlib`, `google.oauth2.credentials`, `googleapiclient.discovery`
- **Utilities:** `uuid`, `traceback`, `asyncio`, `dotenv`, `os`, `secrets`, `datetime`, `time`, `json`, `re`, `typing`

### Internal Module Dependencies

**Most Dependent Modules:**
1. `util.py` - Used by almost all modules
2. `services/game/core.py` - Used by routers (websocket, lobby) and util

**Most Independent Modules:**
1. `services/game/characters.py` - No dependencies (character data constants)
2. `services/game/position.py` - Only depends on slot (local import)
3. `routers/auth.py` - Only depends on util

## Key Design Patterns

1. **Domain-Driven Structure:** Routes organized by feature/domain (auth, lobby, game) rather than by file type
2. **Separation of Concerns:** 
   - `routers/` - Routing and request/response handling
   - `services/` - Business logic and core functionality
   - `util.py` - Shared utilities and infrastructure
3. **Singleton Managers:** `conM`, `dbM`, `timeM` are singleton instances in `util.py`
4. **Function-Based Architecture:** Slot and position management are module-level functions (not classes) that take `game` as first parameter
5. **WebSocket Handlers:** All handler functions follow pattern `handle_<action>()`
6. **Game State:** Centralized in `Game` class, managed through `rooms` dict in `routers/websocket.py`

## Notes

### Structure Overview

**Option 1 - Domain-Driven Structure (Current):**
- **`routers/`** - All route handlers organized by domain:
  - `routers/auth.py` - Combined authentication (Google OAuth + guest sessions)
  - `routers/lobby.py` - Lobby operations (room listing, creation, joining)
  - `routers/game/` - Game-specific handlers:
    - `routers/game/chat.py` - Chat message and command handling
    - `routers/game/flow.py` - Game phase flow management
    - `routers/game/slot.py` - Player slot management handlers
  - `routers/websocket.py` - Main WebSocket endpoint routing
- **`services/`** - Business logic and core functionality:
  - `services/game/core.py` - Core game logic (Game class only)
  - `services/game/slot.py` - Slot management functions
  - `services/game/position.py` - Position management functions
  - `services/game/characters.py` - Character data constants
- **`util.py`** - Shared utilities (ConnectionManager, DatabaseManager, TimeManager)
- **`main.py`** - FastAPI app setup and configuration

### Key Benefits

1. **Scalability:** Easy to add new domains/features by creating new router modules
2. **Maintainability:** Clear separation between routing, business logic, and utilities
3. **Testability:** Services can be tested independently of routing logic
4. **Consistency:** Follows FastAPI best practices for larger applications
5. **Organization:** Related handlers grouped together by domain

### Module Details

- `util.py` contains singleton manager classes (ConnectionManager, DatabaseManager, TimeManager) and is the most central dependency
- `services/game/core.py` defines the core `Game` class only (reduced from 582 to 240 lines)
- `services/game/slot.py` contains slot management functions (converted from `_Slot` class)
- `services/game/position.py` contains position management functions (converted from `_Pos` class)
- `services/game/characters.py` contains character data constants (`default_character`, `bots`)
- Authentication is combined in `routers/auth.py` (both OAuth and guest sessions)
- All WebSocket routing is centralized in `routers/websocket.py` for easier maintenance
- Slot and position functions are called as `slot.function(game, ...)` and `position.function(game, ...)` instead of `game.Slot.method(...)`

---

## Previous File Structure (Commit d379d30763c003cca8a23f9156816dea3631f684)

For comparison, here is the file structure from commit `d379d30763c003cca8a23f9156816dea3631f684` (before the domain-driven refactoring):

```
server/
├── __init__.py
├── main.py              # WebSocket routing + app setup
├── util.py              # Shared utilities (conM, dbM, timeM)
├── google_login.py      # Google OAuth authentication
├── auth_user.py         # Guest authentication
├── lobby_ws.py          # Lobby WebSocket handlers
├── game_core.py         # Game class + _Slot + _Pos classes + character data (582 lines)
├── game_bot.py          # Bot character data (later merged into game_core.py)
└── game_ws.py           # Game WebSocket handlers (temporary, later moved)
```

### Key Differences

**Before (Commit d379d307):**
- Flat structure with all files in `server/` root
- `game_core.py` was a monolithic 582-line file containing:
  - `Game` class
  - `_Slot` class (player slot management)
  - `_Pos` class (position management)
  - Character data (`default_character`, `bots`)
- Separate files: `google_login.py`, `auth_user.py`, `lobby_ws.py`
- No separation between routing and business logic

**After (Current):**
- Domain-driven structure with `routers/` and `services/` folders
- `services/game/core.py` reduced to 240 lines (Game class only)
- Separated into domain modules:
  - `services/game/slot.py` - Slot management functions
  - `services/game/position.py` - Position management functions
  - `services/game/characters.py` - Character data
- Merged authentication: `routers/auth.py` (Google OAuth + guest)
- Organized handlers: `routers/game/` (chat, flow, slot)
- Function-based architecture: Slot and position are now functions, not classes
- Added `config.py` for centralized configuration
