# React Migration Plan

## Current State Analysis

### ✅ Checked Status
- **React is NOT installed** - No `package.json` found
- **Project Structure:**
  - Classic HTML files: `index.html`, `room.html`
  - Vanilla JavaScript in `javaScript/` folder
  - CSS files in `style/` folder
  - Python backend (unchanged)

### Current Features
1. **Lobby Page (`index.html`):**
   - Google OAuth authentication
   - Game session list display
   - Create new game
   - Kill DB (admin function)
   - WebSocket connection for real-time updates

2. **Game Room Page (`room.html`):**
   - Game interface with 3D floor grid
   - Waiting room with player slots
   - Chat system
   - Audio player
   - Timer display
   - WebSocket connection for game state

3. **JavaScript Modules:**
   - `auth_front.js` - Authentication UI logic
   - `auth_ws.js` - Authentication WebSocket handling
   - `lobby_front.js` - Lobby UI logic
   - `lobby_ws.js` - Lobby WebSocket handling
   - `game_front.js` - Game UI logic
   - `game_ws.js` - Game WebSocket handling
   - `util.js` - Utility functions

---

## Migration Strategy

### Phase 1: Setup & Configuration

#### 1.1 Install React and Build Tools
- **Recommended:** Use **Vite** (faster, modern, better DX)
- Alternative: Create React App (CRA)

**Dependencies to install:**
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.20.0"  // For routing between lobby and room
}
```

**Dev Dependencies:**
```json
{
  "@vitejs/plugin-react": "^4.2.0",
  "vite": "^5.0.0"
}
```

#### 1.2 Project Structure
```
PioneerZero/
├── src/
│   ├── components/
│   │   ├── auth.jsx          (authentication UI + logic)
│   │   ├── lobby.jsx         (lobby page with session list)
│   │   ├── gameRoom.jsx      (game room with all game features)
│   │   └── webSocketProvider.jsx  (WebSocket context provider)
│   ├── hooks/
│   │   ├── useWebSocket.js   (generic WebSocket hook)
│   │   ├── useAuth.js        (auth WebSocket logic)
│   │   ├── useLobby.js       (lobby WebSocket logic)
│   │   └── useGame.js        (game WebSocket logic)
│   ├── util.js               (migrated utility functions)
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── public/
│   ├── images/
│   ├── audio/
│   └── index.html (entry point)
├── style/ (keep existing CSS, import in components)
│   ├── global.css
│   ├── lobby.css
│   └── room.css
├── package.json
├── vite.config.js
└── .gitignore (update)
```

---

### Phase 2: Component Migration

#### 2.1 Core Setup
1. **Create `src/main.jsx`** - React entry point
2. **Create `src/App.jsx`** - Main app component with routing
3. **Set up React Router** - Route `/` to Lobby, `/room/:gameId` to GameRoom

#### 2.2 Authentication Component
**Files to migrate:**
- `javaScript/auth_front.js` + `javaScript/auth_ws.js` → `src/components/auth.jsx`
- WebSocket logic → `src/hooks/useAuth.js`

**Component:**
- `auth.jsx` - Contains login button, user display, and all auth UI/logic

**Key changes:**
- Convert DOM manipulation to React state
- Use `useEffect` for WebSocket connection
- Use `useState` for user data
- Convert `localStorage` access to React state with persistence

#### 2.3 Lobby Component
**Files to migrate:**
- `javaScript/lobby_front.js` + `javaScript/lobby_ws.js` → `src/components/lobby.jsx`
- WebSocket logic → `src/hooks/useLobby.js`

**Component:**
- `lobby.jsx` - Complete lobby page with session list, create game button, etc.

**Key changes:**
- Replace `document.getElementById` with React refs/state
- Convert `innerHTML` manipulation to JSX rendering
- Use `useEffect` for WebSocket lifecycle
- Convert `onclick` handlers to React event handlers
- Include session list rendering directly in the component

#### 2.4 Game Room Component
**Files to migrate:**
- `javaScript/game_front.js` + `javaScript/game_ws.js` → `src/components/gameRoom.jsx`
- WebSocket logic → `src/hooks/useGame.js`

**Component:**
- `gameRoom.jsx` - Complete game room with waiting room, floor 3D, chat, timer, etc.

**Key changes:**
- Combine all game UI sections into one component
- Use React state for game state management
- Integrate all game features (waiting room, floor grid, chat) in one file

#### 2.5 Utility Functions
- `javaScript/util.js` → `src/util.js`
- Keep functions as-is (they're already pure functions)
- Export for use in React components

---

### Phase 3: WebSocket Integration

#### 3.1 Custom Hooks Pattern
Create reusable WebSocket hooks:
- `useWebSocket.js` - Generic WebSocket hook
- `useAuth.js` - Authentication WebSocket logic
- `useLobby.js` - Lobby WebSocket logic
- `useGame.js` - Game WebSocket logic

**Example pattern:**
```javascript
function useLobbyWebSocket() {
  const [sessions, setSessions] = useState([]);
  const [ws, setWs] = useState(null);
  
  useEffect(() => {
    // WebSocket connection logic
    // Message handling
    // Cleanup on unmount
  }, []);
  
  return { sessions, createGame, listGames, killDB };
}
```

#### 3.2 State Management
- Use React `useState` for local component state
- Use `useContext` if shared state needed (e.g., auth state)
- Consider `useReducer` for complex state logic (game state)

---

### Phase 4: Styling Migration

#### 4.1 CSS Import Strategy
- Keep existing CSS files in `style/` folder
- Import in components: `import '../style/global.css'`
- Or move to `src/styles/` and import as needed

#### 4.2 CSS Modules (Optional)
- Consider converting to CSS Modules for scoped styles
- Or use styled-components (if preferred)

---

### Phase 5: Build Configuration

#### 5.1 Vite Configuration
```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
});
```

#### 5.2 Public Assets
- Move static assets to `public/` folder
- Update image/audio paths in components

---

## Migration Steps (Execution Order)

### Step 1: Initialize React Project
1. Create `package.json`
2. Install React, ReactDOM, React Router, Vite
3. Create `vite.config.js`
4. Create `public/index.html` (minimal entry point)
5. Create `src/main.jsx` and `src/App.jsx`

### Step 2: Migrate Utilities
1. Copy `javaScript/util.js` → `src/util.js`
2. Update exports to ES6 modules

### Step 3: Create WebSocket Provider and Hooks
1. Create `src/components/webSocketProvider.jsx` (WebSocket context provider)
2. Create `src/hooks/useWebSocket.js` (base hook)
3. Create `src/hooks/useAuth.js`
4. Create `src/hooks/useLobby.js`
5. Test WebSocket connections

### Step 4: Migrate Lobby Page
1. Create `src/components/auth.jsx` (includes login button and user display)
2. Create `src/components/lobby.jsx` (complete lobby page with session list)
3. Test lobby functionality

### Step 5: Migrate Game Room Page
1. Create `src/components/gameRoom.jsx` (complete game room with all features)
2. Create `src/hooks/useGame.js`
3. Test game room functionality

### Step 6: Set Up Routing
1. Install and configure React Router
2. Set up routes: `/` → Lobby, `/room/:gameId` → GameRoom
3. Update navigation (replace `window.open` with `useNavigate`)

### Step 7: Styling
1. Import CSS files in components
2. Test visual appearance
3. Fix any styling issues

### Step 8: Testing & Cleanup
1. Test all functionality
2. Remove old HTML/JS files (or keep as backup)
3. Update `.gitignore`
4. Update documentation

---

## Key Considerations

### ✅ What to Preserve
- All existing functionality
- WebSocket connections and message handling
- CSS styling (visual appearance)
- Backend API compatibility
- localStorage usage patterns
- Google OAuth flow

### 🔄 What Changes
- DOM manipulation → React state/render
- `onclick` attributes → React event handlers
- `document.getElementById` → React refs/state
- `innerHTML` → JSX
- Global functions → React hooks/components
- Multiple HTML files → Single-page app with routing

### ⚠️ Potential Challenges
1. **WebSocket Lifecycle** - Ensure proper cleanup on component unmount
2. **State Synchronization** - WebSocket messages need to update React state
3. **Routing** - Replace `window.open` with React Router navigation
4. **OAuth Popup** - May need adjustments for React context
5. **Timer/Real-time Updates** - Use `useEffect` with intervals

---

## Testing Checklist

- [ ] Lobby page loads correctly
- [ ] Google OAuth login works
- [ ] Session list displays and updates
- [ ] Create game button works
- [ ] Join game navigates to room
- [ ] Game room loads with correct game_id
- [ ] WebSocket connections work in both pages
- [ ] Chat functionality works
- [ ] Timer displays correctly
- [ ] CSS styling preserved
- [ ] All buttons and interactions work

---

## Timeline Estimate

- **Phase 1 (Setup):** 1-2 hours
- **Phase 2 (Components):** 3-4 hours (simplified structure)
- **Phase 3 (WebSocket):** 2-3 hours
- **Phase 4 (Styling):** 1 hour
- **Phase 5 (Build):** 1 hour
- **Testing & Polish:** 2-3 hours

**Total: ~10-14 hours** (simplified component structure reduces complexity)

---

## Next Steps

1. Review and approve this migration plan
2. Start with Phase 1: Setup & Configuration
3. Proceed step-by-step through each phase
4. Test thoroughly at each stage

