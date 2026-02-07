[6 tools called]


Here are the spots that are most worth turning into a Context (or similar) type:

**1. Player slot (best candidate)**  
`game.players[i]` is a dict with a fixed shape: `info`, `character`, `slot`, `ready`, `team`, `occupy`, `pos`. It’s created in `join.player_factory()` and read with `.get()` in `session.py`, `join.py`, `position.py`, `slot.py`, and `commands/base.py` (`_is_combat_participant`).  
Giving it a type (e.g. `PlayerSlot` or `PlayerState`) would give you one place that defines the shape, better typing, and fewer `.get()` bugs. Impact is larger because it’s core game state.

**2. Incoming chat message**  
In `handle_chat(websocket, message: dict, game)` you immediately do `message.get("content", "")`, `message.get("sender")`, `message.get("chat_type", "dialogue")`. That’s a clear, small shape. A small `ChatMessage` (or `IncomingChatMessage`) would make the handler signature clearer and the payload explicit. Low effort, good clarity.

**3. WebSocket message (per action)**  
The generic `message` in `websocket_endpoint` has different fields depending on `action` (e.g. `game_id`, `player_num`, `slot`, `ready`). You could either keep one dict and document it, or introduce small payload types per action (e.g. `CreateRoomPayload` with `player_num`) and parse once after `action` is known. Worth it if you add more actions and want type safety per branch.

**4. Auth message**  
`auth_message` with `action`, `session_id`, `user_info`, `guest_id` is used in auth handlers. An `AuthMessage` (or `AuthPayload`) type would make the expected keys and types explicit. Moderate value, small change.

**Summary**  
- **Highest value:** Player slot dict → `PlayerSlot` (or similar) in game_core.  
- **Quick wins:** Incoming chat message → `ChatMessage`; auth payload → `AuthMessage`.  
- **Optional:** WebSocket action payloads as small types when you add more actions.

If you say which of these you want to do first (e.g. “only chat message” or “player slot and chat”), I can outline the exact types and call-site changes step by step.