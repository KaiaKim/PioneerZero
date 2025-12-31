# Architecture Connection Diagrams

## Old Architecture (Before React Migration)

### Connection Flow
```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Port 8000)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Static File Server (app.mount)                      │  │
│  │  - /style → style/                                   │  │
│  │  - /images → images/                                 │  │
│  │  - /audio → audio/                                   │  │
│  │  - /javaScript → javaScript/                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  HTML Endpoints                                       │  │
│  │  - GET / → index.html                                │  │
│  │  - GET /room.html → room.html                        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  WebSocket Endpoint                                    │  │
│  │  - WS /ws → Game/Lobby logic                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
                            │ HTTP (HTML, CSS, JS, Images)
                            │ WebSocket (Real-time data)
                            │
┌───────────────────────────┴───────────────────────────────┐
│                    Browser Client                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  index.html                                          │  │
│  │  ├── <script src="/javaScript/util.js">              │  │
│  │  ├── <script src="/javaScript/auth_front.js">       │  │
│  │  ├── <script src="/javaScript/auth_ws.js">          │  │
│  │  ├── <script src="/javaScript/lobby_front.js">      │  │
│  │  └── <script src="/javaScript/lobby_ws.js">          │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  room.html                                           │  │
│  │  ├── <script src="/javaScript/util.js">             │  │
│  │  ├── <script src="/javaScript/game_front.js">       │  │
│  │  └── <script src="/javaScript/game_ws.js">          │  │
│  └────────────────────────────────────────────────────┘  │
│                                                            │
│  • All files served by FastAPI                            │
│  • Vanilla JavaScript with DOM manipulation               │
│  • Direct WebSocket connection to backend                │
└────────────────────────────────────────────────────────────┘
```

### Characteristics
- **Single Server**: FastAPI serves everything (HTML, CSS, JS, images, WebSocket)
- **File Structure**: 
  - `index.html` - Lobby page
  - `room.html` - Game room page
  - `javaScript/` - All client-side logic
  - `style/` - CSS files
  - `images/`, `audio/` - Static assets
- **Communication**: 
  - HTTP for static files
  - WebSocket for real-time game data
- **Rendering**: Server-rendered HTML with client-side JavaScript

---

## New Architecture (After React Migration)

### Connection Flow
```
┌─────────────────────────────────────────────────────────────┐
│              Vite Dev Server (Port 3000)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  React Application                                    │  │
│  │  ├── src/components/                                  │  │
│  │  │   ├── auth.jsx                                     │  │
│  │  │   ├── lobby.jsx                                    │  │
│  │  │   └── gameRoom.jsx                                 │  │
│  │  ├── src/hooks/                                       │  │
│  │  │   ├── useAuth.js                                   │  │
│  │  │   ├── useLobby.js                                  │  │
│  │  │   └── useGame.js                                   │  │
│  │  └── React Router (SPA)                               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Static Assets (public/)                              │  │
│  │  - /images → public/images/                           │  │
│  │  - /audio → public/audio/                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WebSocket (ws://localhost:8000/ws)
                            │ HTTP API (if needed)
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  WebSocket Endpoint (Primary Communication)            │  │
│  │  - WS /ws → Game/Lobby/Auth logic                      │  │
│  │    • authenticate_guest                                │  │
│  │    • authenticate_google                                │  │
│  │    • create_game                                        │  │
│  │    • list_games                                         │  │
│  │    • join_game                                          │  │
│  │    • load_game                                          │  │
│  │    • chat                                               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  OAuth Router                                           │  │
│  │  - GET /auth/google/login → Google OAuth               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Optional Static Files (Legacy Support)                 │  │
│  │  - /style → style/ (optional)                          │  │
│  │  - /images → images/ (optional)                         │  │
│  │  - /audio → audio/ (optional)                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Characteristics
- **Two Servers**: 
  - Vite (port 3000) - Serves React app
  - FastAPI (port 8000) - API/WebSocket server
- **File Structure**:
  - `src/` - React source code
  - `public/` - Static assets (served by Vite)
  - `old/` - Legacy HTML/JS files (archived)
- **Communication**: 
  - WebSocket for real-time game data (primary)
  - HTTP API for OAuth and other endpoints
  - Vite proxy can forward `/ws` and `/api` to backend
- **Rendering**: Client-side React (SPA) with React Router

---

## Key Differences

| Aspect | Old Architecture | New Architecture |
|--------|------------------|------------------|
| **Servers** | 1 (FastAPI only) | 2 (Vite + FastAPI) |
| **Frontend** | Vanilla JS + HTML | React (SPA) |
| **File Serving** | FastAPI serves all | Vite serves frontend |
| **WebSocket** | Direct to FastAPI | Direct to FastAPI |
| **Routing** | Multiple HTML pages | React Router (SPA) |
| **State Management** | Global variables | React hooks/state |
| **Build Tool** | None (direct files) | Vite (bundling) |
| **Development** | Refresh page | Hot Module Replacement |

---

## Connection Details

### Old: Direct File Serving
```
Browser → http://localhost:8000/ → FastAPI serves index.html
Browser → http://localhost:8000/javaScript/lobby_ws.js → FastAPI serves file
Browser → ws://localhost:8000/ws → FastAPI WebSocket
```

### New: Separated Frontend/Backend
```
Browser → http://localhost:3000/ → Vite serves React app
Browser → ws://localhost:8000/ws → FastAPI WebSocket (direct)
Browser → http://localhost:8000/auth/google/login → FastAPI OAuth
```

### Vite Proxy (Optional)
The `vite.config.js` can proxy requests:
```javascript
proxy: {
  '/ws': { target: 'ws://localhost:8000', ws: true },
  '/api': { target: 'http://localhost:8000' }
}
```
This allows using relative URLs like `/ws` instead of `ws://localhost:8000/ws`, but direct connection works too.

---

## Migration Benefits

1. **Separation of Concerns**: Frontend and backend are independent
2. **Modern Development**: Hot reload, better tooling, component-based
3. **Better State Management**: React hooks vs global variables
4. **Type Safety**: Can add TypeScript later
5. **Performance**: Vite's fast builds and optimized bundling
6. **Scalability**: Frontend can be deployed separately from backend

