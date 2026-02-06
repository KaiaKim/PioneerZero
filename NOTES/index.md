# Server File Structure & Dependencies

## Overview
This document maps all Python files in the `server/` directory, their dependencies, and their relationships.

**Current Structure (Domain-Driven):**
- **`routers/`** - Route handlers by domain: auth, lobby, websocket, chat_router, game_router
- **`services/game_core/`** - Business logic: session (Game), join (slot/player), position, characters
- **`util.py`** - Shared utilities (ConnectionManager, DatabaseManager, TimeManager)
- **`main.py`** - FastAPI app setup and configuration

**Note:**
- Routes/handlers are grouped by feature/domain
- Business logic is separated from routing/handling logic

---

## File Index
```
server/
├── main.py                    # App setup only
├── config.py                  # Settings
├── util.py                    # Shared utilities
├── routers/
│   ├── __init__.py
│   ├── websocket.py           # WebSocket endpoint and action routing
│   ├── auth.py                # Google OAuth + guest auth
│   ├── lobby.py               # Lobby handlers (list, create, join, load room)
│   ├── chat_router/           # Chat and slash-command handling
│   │   ├── __init__.py
│   │   ├── chat.py            # handle_chat entry point
│   │   ├── context.py         # CommandContext
│   │   ├── input.py           # parse_input
│   │   ├── router.py          # CommandRouter
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── attack.py       # Attack command handler
│   │       ├── position.py    # Position command handler
│   │       ├── preparation.py # Preparation (참여, 관전) handler
│   │       └── skill.py        # Skill command handler
│   └── game_router/           # Game flow and slot handlers
│       ├── __init__.py
│       ├── flow.py            # Phase flow (handle_phase, kickoff, etc.)
│       └── slot.py            # Slot handlers (join, add_bot, leave, set_ready, timeout checks)
├── services/
│   ├── __init__.py
│   └── game_core/
│       ├── __init__.py
│       ├── session.py         # Game class
│       ├── join.py             # Slot/player management (player_factory, add_player, etc.)
│       ├── position.py         # Position/coordinate functions
│       └── characters.py      # Character data (default_character, bots)
└── (no models/ - optional, do not implement yet)
```

### Core Files

#### `main.py`
**Purpose:** FastAPI application setup and configuration  
**External Dependencies:** `fastapi`, (config via `settings`)  
**Internal Dependencies:**
- `config` (settings)
- `routers.auth`, `routers.websocket`
- `routers.game_router.slot` (for startup timeout checks)
- `util` (dbM)

**Key Exports:** `app` (FastAPI instance)  
**Key Functions:** `startup_event()` - Background tasks on server startup

---

#### `util.py`
**Purpose:** Shared utility classes for the server  
**External Dependencies:** `fastapi` (WebSocket), `sqlite3`, `os`, `datetime`, `asyncio`, `json`, `time`  
**Internal Dependencies:** Local import of `Game` from `services.game_core.session` only in `load_game_session`

**Key Classes:** `ConnectionManager` (conM), `DatabaseManager` (dbM), `TimeManager` (timeM)  
**Key Exports:** `conM`, `dbM`, `timeM`

---

### Router Files (`routers/`)

#### `routers/websocket.py`
**Purpose:** WebSocket endpoint and action routing  
**External Dependencies:** `fastapi` (WebSocket), `uuid`, `traceback`  
**Internal Dependencies:**
- `util` (conM, dbM)
- `services.game_core.session` (Game)
- `services.game_core.join`
- `auth`, `lobby`
- `game_router.flow`, `game_router.slot`
- `chat_router.chat`

**Key Functions:** `websocket_endpoint()`  
**Key Variables:** `rooms` - Global game sessions dict

---

#### `routers/auth.py`
**Purpose:** Authentication (Google OAuth + guest sessions)  
**External Dependencies:** `fastapi`, `google_auth_oauthlib`, `google.oauth2.credentials`, `os`, `secrets`, `typing`, `dotenv`  
**Internal Dependencies:** `util` (conM)  
**Key Exports:** `router`  
**Key Functions:** `google_login`, `google_callback`, `handle_google_login`, `handle_user_auth`, `verify_google_token`, `get_user_info_from_token`

---

#### `routers/lobby.py`
**Purpose:** Lobby WebSocket handlers  
**External Dependencies:** `fastapi` (WebSocket)  
**Internal Dependencies:** `util` (conM, dbM), `services.game_core.session` (Game)  
**Key Functions:** `handle_list_rooms`, `handle_create_room`, `handle_join_room`, `handle_load_room`

---

### Chat Router (`routers/chat_router/`)

#### `routers/chat_router/chat.py`
**Purpose:** Chat and slash-command entry point (parse → route → handler)  
**External Dependencies:** `fastapi` (WebSocket)  
**Internal Dependencies:** `util` (conM, dbM), `context`, `input`, `router`, `commands`  
**Key Functions:** `handle_chat()`

---

#### `routers/chat_router/context.py`
**Purpose:** Command context (dataclass)  
**External Dependencies:** `dataclasses`, `typing`  
**Internal Dependencies:** None

---

#### `routers/chat_router/input.py`
**Purpose:** Input parsing (e.g. parse_input)  
**External Dependencies:** `typing`  
**Internal Dependencies:** None

---

#### `routers/chat_router/router.py`
**Purpose:** Command router (register handlers by command name)  
**External Dependencies:** `typing`  
**Internal Dependencies:** `context`

---

#### `routers/chat_router/commands/` (attack, position, preparation, skill)
**Purpose:** Slash-command handlers per domain  
**Internal Dependencies:** `context`; `commands.attack` and `commands.skill` use `util` (conM); `commands.position` uses `services.game_core.position`

---

### Game Router (`routers/game_router/`)

#### `routers/game_router/flow.py`
**Purpose:** Game phase flow management  
**External Dependencies:** `asyncio`  
**Internal Dependencies:** `util` (conM, dbM, timeM), `services.game_core.join`  
**Key Functions:** `handle_phase`, `_phase_flow`, `kickoff`, `position_declaration`, `position_resolution`, `start_round`, `action_declaration`, `action_resolution`, `end_round`, `wrap_up`

---

#### `routers/game_router/slot.py`
**Purpose:** Player slot WebSocket handlers  
**External Dependencies:** `fastapi` (WebSocket), `asyncio`  
**Internal Dependencies:** `util` (conM), `services.game_core.join`  
**Key Functions:** `handle_join_player_slot`, `handle_add_bot_to_slot`, `handle_leave_player_slot`, `handle_set_ready`, `run_connection_lost_timeout_checks`

---

### Service Files (`services/game_core/`)

#### `services/game_core/session.py`
**Purpose:** Core Game class and game state  
**External Dependencies:** `json`  
**Internal Dependencies:** `join`, `position`  
**Key Classes:** `Game`  
**Key Methods:** `declare_attack`, `declare_skill`, `dict_to_json`, `json_to_dict`, `vomit`, `check_all_players_defeated`, etc.

---

#### `services/game_core/join.py`
**Purpose:** Slot/player management (join, leave, ready, connection-lost)  
**External Dependencies:** `time`  
**Internal Dependencies:** `characters` (default_character, bots)  
**Key Functions:** `player_factory`, `add_player`, `add_bot`, `remove_player`, `set_player_connection_lost`, `clear_expired_connection_lost_slots`, `get_player_by_user_id`, `set_player_ready`, `are_all_players_ready`, etc.

---

#### `services/game_core/position.py`
**Purpose:** Position/coordinate management  
**External Dependencies:** `re`  
**Internal Dependencies:** `join` (local import where needed)  
**Key Functions:** `declare_position`, `move_player`, `pos_to_rc`, `rc_to_pos`, `is_front_row`, `is_back_row`, `check_move_validity`  
**Key Constants:** `ROW_MAP`, `REV_ROW_MAP`

---

#### `services/game_core/characters.py`
**Purpose:** Character data constants  
**External Dependencies:** None  
**Internal Dependencies:** None  
**Key Data:** `default_character`, `bots`

---

## Dependency Graph

```
main.py
├── config (settings)
├── routers/websocket.py
│   ├── util (conM, dbM)
│   ├── services/game_core/session (Game)
│   ├── services/game_core/join
│   ├── routers/auth.py → util (conM)
│   ├── routers/lobby.py → util (conM, dbM), services/game_core/session (Game)
│   ├── routers/chat_router/chat.py → util (conM, dbM), chat_router (context, input, router, commands)
│   │   └── commands → services/game_core/position (position), util (conM) (attack, skill), context
│   ├── routers/game_router/flow.py → util (conM, dbM, timeM), services/game_core/join
│   ├── routers/game_router/slot.py → util (conM), services/game_core/join
│   └── (websocket uses join in finally block)
├── routers/game_router/slot (run_connection_lost_timeout_checks)
└── util.py
    └── load_game_session: local import services/game_core/session (Game)

services/game_core/session.py
├── join (player_factory, etc.)
└── position

services/game_core/join.py
└── characters (default_character, bots)

services/game_core/position.py
└── re (and local join where needed)
```

## Dependency Categories

### External Libraries
- **Web:** `fastapi`
- **Database:** `sqlite3`
- **OAuth:** `google_auth_oauthlib`, `google.oauth2.credentials`, `googleapiclient.discovery`
- **Utilities:** `uuid`, `traceback`, `asyncio`, `dotenv`, `os`, `secrets`, `datetime`, `time`, `json`, `re`, `typing`, `dataclasses`

### Internal Module Dependencies
- **Most used:** `util`, `services/game_core/session`, `services/game_core/join`
- **Most independent:** `services/game_core/characters`, `routers/chat_router/context`, `routers/chat_router/input`

## Key Design Patterns

1. **Domain-driven structure:** auth, lobby, chat_router, game_router under `routers/`.
2. **Separation of concerns:** routers handle HTTP/WS and delegation; `services/game_core` holds game and slot/position/character logic.
3. **Singleton managers:** `conM`, `dbM`, `timeM` in `util.py`.
4. **Function-based game logic:** Join and position are module-level functions taking `game` (and other args); no `game.Slot`/`game.Pos` classes.
5. **Chat commands:** Parse → CommandRouter → per-command handlers in `chat_router/commands/` (attack, position, preparation, skill).
6. **Game state:** Centralized in `Game` (`session.py`), with `rooms` in `websocket.py`.

## Notes

### Structure summary
- **`routers/chat_router/`** – Chat and slash-commands: `chat.py` entry, `context`, `input`, `router`, and `commands/` (attack, position, preparation, skill).
- **`routers/game_router/`** – Game flow and slots: `flow.py`, `slot.py`.
- **`services/game_core/`** – `session.py` (Game), `join.py` (slot/player), `position.py`, `characters.py`.
- **`util.py`** – ConnectionManager, DatabaseManager, TimeManager.
- **`main.py`** – App and startup (e.g. slot timeout checks, loading saved rooms).

### Module details
- `util.py`: singleton managers; `load_game_session` imports `Game` from `services.game_core.session` locally.
- `services/game_core/session.py`: `Game` class only; uses `join` and `position`.
- `services/game_core/join.py`: slot/player management (replaces previous slot module).
- `services/game_core/position.py`: position/coordinate logic.
- `services/game_core/characters.py`: `default_character`, `bots`.
- Chat: single entry `handle_chat` in `chat_router`; commands registered in `chat.py` and implemented in `commands/`.
- WebSocket routing and `rooms` live in `routers/websocket.py`.

---

## Previous File Structure (Commit d379d30763c003cca8a23f9156816dea3631f684)

For comparison, the file structure before domain-driven refactoring:

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
└── game_ws.py          # Game WebSocket handlers (temporary, later moved)
```

### Key Differences

**Before (Commit d379d307):** Flat layout; single large `game_core.py`; separate auth files; no routers/services split.

**After (Current):** Domain-driven; `routers/` (auth, lobby, websocket, chat_router, game_router); `services/game_core/` (session, join, position, characters); chat split into chat_router with command submodules; `config.py` for settings.
