# Server File Structure & Dependencies

## Overview
This document maps all Python files in the `server/` directory, their dependencies, and their relationships.

**Note:** 
- Game-related modules are organized in the `server/game/` subdirectory
- WebSocket handlers use the `handle_` prefix to distinguish them from data and core modules

---

## File Index

### Core Files

#### `main.py`
**Purpose:** Global variables and core server setup for the FastAPI server  
**External Dependencies:**
- `fastapi` (FastAPI, WebSocket)
- `uuid`
- `traceback`
- `asyncio`
- `dotenv` (load_dotenv)

**Internal Dependencies:**
- `handle_lobby` (aliased as `lobby`)
- `auth_google`
- `auth_user`
- `game.core` (Game class imported directly)
- `game.handle_chat` (aliased as `chat`)
- `game.handle_flow` (aliased as `flow`)
- `game.handle_slot` (aliased as `slot`)
- `util` (conM, dbM)

**Key Exports:**
- `app` (FastAPI instance)
- `rooms` (global game sessions dictionary)

**Key Functions:**
- `startup_event()` - Background tasks on server startup
- `websocket_endpoint()` - Main WebSocket endpoint routing

---

#### `game/core.py`
**Purpose:** Core Game class and game state management  
**External Dependencies:**
- `re`
- `time`
- `json`

**Internal Dependencies:**
- None (character data merged from bot.py)

**Key Classes:**
- `Game` - Main game state class
- `_Slot` - Player slot management (private class)
- `_Pos` - Position/coordinate management (private class)

**Key Data:**
- `default_character` - Default character template
- `bots` - List of bot character definitions

**Key Methods:**
- `declare_attack()` - Handle attack declarations
- `declare_skill()` - Handle skill declarations
- `dict_to_json()` - Serialize game state
- `json_to_dict()` - Deserialize game state
- `vomit()` - Export game data
- `check_all_players_defeated()` - Check win conditions

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
- None (local import of `Game` from `game.core` only in `load_game_session` method)

**Key Classes:**
- `ConnectionManager` (conM) - WebSocket connection management
- `DatabaseManager` (dbM) - SQLite database operations
- `TimeManager` (timeM) - Timer management for game phases

**Key Exports:**
- `conM` - ConnectionManager instance
- `dbM` - DatabaseManager instance
- `timeM` - TimeManager instance

---

### Authentication Files

#### `auth_google.py`
**Purpose:** Google OAuth authentication handlers  
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
- `verify_google_token()` - Verify token data
- `get_user_info_from_token()` - Get user info from token

---

#### `auth_user.py`
**Purpose:** Authentication utility functions for guest session management  
**External Dependencies:**
- `fastapi` (WebSocket)

**Internal Dependencies:**
- `util` (conM)

**Key Functions:**
- `handle_user_auth()` - Handle guest authentication

---

### Game Handler Files

#### `game/handle_slot.py`
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

#### `game/handle_flow.py`
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

#### `game/handle_chat.py`
**Purpose:** Chat message and command handling  
**External Dependencies:**
- `fastapi` (WebSocket)
- `asyncio`
- `time`

**Internal Dependencies:**
- `util` (conM, dbM, timeM)

**Key Functions:**
- `handle_chat()` - Handle chat messages and commands

---

### Lobby Files

#### `handle_lobby.py`
**Purpose:** Lobby WebSocket handlers and endpoints  
**External Dependencies:**
- `fastapi` (WebSocket)

**Internal Dependencies:**
- `util` (conM, dbM)
- `game.core` (Game)

**Key Functions:**
- `handle_list_rooms()` - Return list of active game sessions
- `handle_create_room()` - Create new game session
- `handle_join_room()` - Join client to existing game
- `handle_load_room()` - Load room data for client

---

---

#### `__init__.py`
**Purpose:** Server package initialization  
**External Dependencies:**
- None

**Internal Dependencies:**
- None

---

## Dependency Graph

```
main.py
├── handle_lobby.py
│   ├── util.py (conM, dbM)
│   └── game/core.py (Game)
├── auth_google.py
│   └── util.py (conM)
├── auth_user.py
│   └── util.py (conM)
├── game/core.py
├── game/handle_chat.py
│   └── util.py (conM, dbM, timeM)
├── game/handle_flow.py
│   └── util.py (conM, dbM, timeM)
├── game/handle_slot.py
│   └── util.py (conM)
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
2. `game/core.py` - Used by 3 files (main, handle_lobby, util)

**Most Independent Modules:**
1. `game/core.py` - No internal dependencies (character data merged into core)
2. `auth_user.py` - Only depends on util
3. `game/handle_slot.py` - Only depends on util

## Key Design Patterns

1. **Singleton Managers:** `conM`, `dbM`, `timeM` are singleton instances in `util.py`
2. **Manager Classes:** `_Slot`, `_Pos` (private classes) are defined in `game/core.py` and instantiated per-game in `Game` class as `game.Slot` and `game.Pos`
3. **WebSocket Handlers:** All handler functions follow pattern `handle_<action>()`
4. **Game State:** Centralized in `Game` class, managed through `rooms` dict in `main.py`

## Notes

- `util.py` contains singleton manager classes (ConnectionManager, DatabaseManager, TimeManager) and is the most central dependency
- `game/core.py` defines the core `Game` class, `_Slot`, and `_Pos` managers, plus character data (`default_character`, `bots`) that was merged from `bot.py`
- Authentication is split into `auth_google.py` (OAuth) and `auth_user.py` (guest)
- Game-related modules are organized in the `game/` subdirectory:
  - **Core:** `game/core.py` - Core game logic (Game class, `_Slot`, `_Pos` managers, character data)
  - **Handlers:** WebSocket connection handlers with `handle_` prefix:
    - `game/handle_flow.py` - Game phase flow management
    - `game/handle_chat.py` - Chat message and command handling
    - `game/handle_slot.py` - Player slot management handlers
- WebSocket handlers use the `handle_` prefix to distinguish them from data and core modules:
  - `handle_lobby.py` - Lobby operations (room listing, creation, joining)
  - `game/handle_*.py` - Game-specific handlers (chat, slot, flow)
