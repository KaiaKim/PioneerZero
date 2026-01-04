# Time Counter System - Architecture & Implementation Plan

## Overview

This document outlines the file structure, data models, and implementation plan for a flexible time counter system in the game room. The timer is designed to support multiple use cases:
- Session timer (total time in room)
- Round timer (per round time limit)
- Turn timer (per turn time limit)
- Phase timer (different game phases)
- Idle timer (time since last action)

---

## Data Structure

### Backend: `server/game_core.py` - Game Class

Add the following attributes to the `Game` class:

```python
class Game():
    def __init__(self, id, player_num = 4):
        # ... existing code ...
        
        # Timer state
        self.timer = {
            'type': 'session',  # 'session', 'round', 'turn', 'phase', 'idle'
            'start_time': None,  # Unix timestamp when timer started
            'duration': None,    # Duration in seconds (None for count-up, number for countdown)
            'is_running': False, # Whether timer is currently running
            'paused_at': None,   # Unix timestamp when paused (for resume functionality)
            'elapsed_before_pause': 0  # Accumulated elapsed time before pause
        }
```

**Timer Methods to Add:**

```python
def start_timer(self, timer_type='session', duration=None):
    """Start a timer with optional countdown duration"""
    
def stop_timer(self):
    """Stop the timer"""
    
def pause_timer(self):
    """Pause the timer (preserves elapsed time)"""
    
def resume_timer(self):
    """Resume a paused timer"""
    
def reset_timer(self):
    """Reset timer to initial state"""
    
def get_timer_state(self):
    """Get current timer state (elapsed time, remaining time if countdown)"""
    
def update_timer_type(self, timer_type, duration=None):
    """Change timer type and optionally set new duration"""
```

### Backend: `server/game_ws.py` - WebSocket Handlers

Add new message handlers:

```python
async def handle_start_timer(websocket: WebSocket, message: dict, game):
    """Handle start_timer action"""
    
async def handle_stop_timer(websocket: WebSocket, message: dict, game):
    """Handle stop_timer action"""
    
async def handle_pause_timer(websocket: WebSocket, message: dict, game):
    """Handle pause_timer action"""
    
async def handle_resume_timer(websocket: WebSocket, message: dict, game):
    """Handle resume_timer action"""
    
async def handle_reset_timer(websocket: WebSocket, message: dict, game):
    """Handle reset_timer action"""
    
async def handle_timer_state_request(websocket: WebSocket, message: dict, game):
    """Send current timer state to requesting client"""
```

**Timer Broadcast Function:**

Add a periodic broadcast function (called by background task):
```python
async def broadcast_timer_update(game):
    """Broadcast timer state to all clients in the game"""
```

### Backend: `server/main.py` - Background Task

Add a background task to periodically broadcast timer updates:

```python
async def timer_broadcast_task():
    """Background task that broadcasts timer updates every second"""
```

---

## Frontend Data Structure

### `src/hooks/useGame.js` - State & Methods

Add to the hook's state:

```javascript
const [timerState, setTimerState] = useState({
  type: 'session',      // 'session', 'round', 'turn', 'phase', 'idle'
  elapsed: 0,           // Elapsed time in seconds
  remaining: null,      // Remaining time for countdown (null if count-up)
  isRunning: false,     // Whether timer is running
  duration: null        // Duration for countdown timers (null if count-up)
});
```

**Methods to Add:**

```javascript
const startTimer = (timerType = 'session', duration = null) => {
  messageGameWS({
    action: 'start_timer',
    timer_type: timerType,
    duration: duration
  });
};

const stopTimer = () => {
  messageGameWS({
    action: 'stop_timer'
  });
};

const pauseTimer = () => {
  messageGameWS({
    action: 'pause_timer'
  });
};

const resumeTimer = () => {
  messageGameWS({
    action: 'resume_timer'
  });
};

const resetTimer = () => {
  messageGameWS({
    action: 'reset_timer'
  });
};
```

**WebSocket Message Handler:**

Add to `ws.onmessage`:

```javascript
else if (msg.type === "timer_update") {
  setTimerState({
    type: msg.timer_type,
    elapsed: msg.elapsed,
    remaining: msg.remaining,
    isRunning: msg.is_running,
    duration: msg.duration
  });
}
```

### `src/components/room/Room.jsx` - Timer Display

Update the timer display element:

```javascript
// Format time helper function
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// In JSX:
<h1 className="timer">
  {timerState.isRunning 
    ? (timerState.remaining !== null 
        ? formatTime(timerState.remaining) 
        : formatTime(timerState.elapsed))
    : formatTime(timerState.elapsed)
  }
</h1>
```

---

## WebSocket Message Types

### Client → Server Messages

```json
// Start Timer
{
  "action": "start_timer",
  "game_id": "game123",
  "timer_type": "session",  // optional, defaults to "session"
  "duration": 300            // optional, null for count-up, number for countdown
}

// Stop Timer
{
  "action": "stop_timer",
  "game_id": "game123"
}

// Pause Timer
{
  "action": "pause_timer",
  "game_id": "game123"
}

// Resume Timer
{
  "action": "resume_timer",
  "game_id": "game123"
}

// Reset Timer
{
  "action": "reset_timer",
  "game_id": "game123"
}

// Request Timer State
{
  "action": "timer_state_request",
  "game_id": "game123"
}
```

### Server → Client Messages

```json
// Timer Update (broadcast)
{
  "type": "timer_update",
  "timer_type": "session",
  "elapsed": 125,
  "remaining": null,     // null for count-up, number for countdown
  "is_running": true,
  "duration": null       // null for count-up, number for countdown
}

// Timer State Response (single client)
{
  "type": "timer_state",
  "timer_type": "session",
  "elapsed": 125,
  "remaining": null,
  "is_running": true,
  "duration": null
}
```

---

## File Changes Summary

### Backend Files

1. **`server/game_core.py`**
   - Add `timer` dictionary to `__init__`
   - Implement timer methods: `start_timer()`, `stop_timer()`, `pause_timer()`, `resume_timer()`, `reset_timer()`, `get_timer_state()`, `update_timer_type()`
   - Include timer state in `vomit()` method

2. **`server/game_ws.py`**
   - Add handler functions: `handle_start_timer()`, `handle_stop_timer()`, `handle_pause_timer()`, `handle_resume_timer()`, `handle_reset_timer()`, `handle_timer_state_request()`
   - Add `broadcast_timer_update()` function
   - Update `handle_load_game()` to include timer state
   - Wire handlers in main WebSocket router (in `server/main.py`)

3. **`server/main.py`**
   - Add background task `timer_broadcast_task()` to periodically broadcast timer updates
   - Register timer action handlers in WebSocket router
   - Start background task when application starts

### Frontend Files

1. **`src/hooks/useGame.js`**
   - Add `timerState` to useState
   - Add timer action methods: `startTimer()`, `stopTimer()`, `pauseTimer()`, `resumeTimer()`, `resetTimer()`
   - Add message handler for `timer_update` and `timer_state` message types
   - Export timer state and methods

2. **`src/components/room/Room.jsx`**
   - Import timer state and methods from `useGame()` hook
   - Update timer display element to use `timerState`
   - Add `formatTime()` helper function

3. **`style/room.css`** (optional enhancements)
   - Enhance `.timer` styling if needed
   - Add classes for different timer states (e.g., `.timer-running`, `.timer-paused`, `.timer-warning`)

---

## Implementation Steps

### Phase 1: Backend Core Logic

1. **Update `server/game_core.py`**
   - Add timer data structure to `Game.__init__()`
   - Implement `get_timer_state()` method first (used by other methods)
   - Implement `start_timer()`, `stop_timer()`, `pause_timer()`, `resume_timer()`, `reset_timer()`
   - Update `vomit()` to include timer state

2. **Update `server/game_ws.py`**
   - Implement `handle_start_timer()`, `handle_stop_timer()`, `handle_pause_timer()`, `handle_resume_timer()`, `handle_reset_timer()`, `handle_timer_state_request()`
   - Implement `broadcast_timer_update()` function
   - Update `handle_load_game()` to send timer state

3. **Update `server/main.py`**
   - Add timer action handlers to WebSocket router
   - Implement `timer_broadcast_task()` background task
   - Start background task on application startup

### Phase 2: Frontend Integration

1. **Update `src/hooks/useGame.js`**
   - Add `timerState` state
   - Add timer action methods
   - Add message handlers for timer updates
   - Export timer state and methods

2. **Update `src/components/room/Room.jsx`**
   - Import timer state/methods from hook
   - Update timer display to use state
   - Add formatting helper

### Phase 3: Testing & Polish

1. Test timer start/stop/pause/resume/reset
2. Test count-up vs countdown modes
3. Test timer state persistence on page refresh
4. Test timer synchronization across multiple clients
5. Add visual indicators for timer states (running, paused, warning)
6. Add timer type labels if displaying multiple timer types

---

## Timer Behavior Details

### Count-Up Timer (session timer)
- `duration` is `None`
- `remaining` is `None`
- Display shows elapsed time
- Timer continues until manually stopped

### Countdown Timer (round/turn/phase timer)
- `duration` is set (e.g., 300 seconds)
- `remaining` is calculated: `duration - elapsed`
- Display shows remaining time
- When `remaining` reaches 0, timer stops (can trigger events)

### Pause/Resume
- When paused, `elapsed_before_pause` stores current elapsed time
- `paused_at` stores timestamp
- On resume, accumulated time is restored
- Total elapsed = `elapsed_before_pause + (current_time - paused_at)`

### Timer Synchronization
- Server is the source of truth
- Server broadcasts timer state every 1 second to all clients
- Clients display server-provided values
- Timer state is included in `vomit_data` on game load

---

## Future Enhancements (Optional)

1. **Multiple Concurrent Timers**
   - Support multiple timer types running simultaneously
   - Store timers as dictionary: `self.timers = {'session': {...}, 'turn': {...}}`

2. **Timer Events/Callbacks**
   - Trigger events when countdown reaches 0
   - Support timer callbacks for game logic integration

3. **Timer Configuration**
   - Allow per-game timer settings
   - Configurable update intervals
   - Custom timer durations per game type

4. **Timer History**
   - Track timer start/stop events
   - Log timer state changes for debugging/analytics

5. **Visual Enhancements**
   - Progress bar for countdown timers
   - Color changes (green → yellow → red) as time runs out
   - Animation effects for timer transitions

---

## Notes

- Timer uses Unix timestamps for accuracy
- Server-side timer prevents client-side manipulation
- Timer state is included in game state, so it persists with game data
- Background broadcast task ensures all clients stay synchronized
- Timer can be extended for game-specific logic (e.g., auto-end turn when countdown reaches 0)

