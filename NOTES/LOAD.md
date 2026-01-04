How to start your development servers:

Since this project uses React (with Vite) for the frontend and FastAPI for the backend, you need to run **two separate servers** in different terminal windows.

---

## Step 1: Start the FastAPI Backend Server

Open a terminal in `F:\2025\Pioneer_Zero\newGame` and run:
```bash
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

What each part means:
- `python -m uvicorn` — runs uvicorn using Python
- `python.main:app` — module path (`python/main.py`) and the FastAPI app instance (`app`)
- `--host 0.0.0.0` — listen on all network interfaces (accessible from other devices on your network)
- `--port 8000` — use port 8000
- `--reload` — auto-restart on code changes (development only)

Alternative (localhost only):
```bash
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## Step 2: Start the React Frontend Server

**Open a separate terminal** in `F:\2025\Pioneer_Zero\newGame` and run:
```bash
npm run dev
```

This will start the Vite development server on port 3000.

What this does:
- Starts the Vite dev server for React
- Serves the frontend application on `http://localhost:3000`
- Auto-reloads the browser when you save React/JSX files
- Proxies WebSocket connections (`/ws`) and API requests (`/api`) to the FastAPI backend on port 8000

---

## Accessing Your Application

Once both servers are running:
- **Frontend (React app):** Open your browser to `http://localhost:3000`
- **Backend API:** Available at `http://localhost:8000`

---

## Stopping the Servers

To stop either server:
- Press `Ctrl+C` in the terminal where it's running

**Note:** You need to keep both terminal windows open while developing. If you close either one, that part of the application will stop working.

---

## Quick Reference Card

**Start Backend (Terminal 1):**
```bash
python -m uvicorn python.main:app --host 0.0.0.0 --port 8000 --reload
```

**Start Frontend (Terminal 2):**
```bash
npm run dev
```

**Stop either server:**
- Press `Ctrl+C` in the terminal

**Check if backend is running:**
```bash
netstat -ano | findstr :8000 | findstr LISTENING
```

**Check if frontend is running:**
```bash
netstat -ano | findstr :3000 | findstr LISTENING
```

**Access your site:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

---

## Tips

- Keep both terminal windows open while the servers run
- With `--reload` on the backend, it auto-restarts when you save Python files
- The React dev server auto-reloads when you save React/JSX files
- If port 8000 is busy, use `--port 8001` (and update the proxy in `vite.config.js` if needed)
- If port 3000 is busy, Vite will automatically try the next available port
- Error messages appear in the respective terminal windows

---

## Common Issues

**Backend:**
- "Address already in use" → Port 8000 is taken; stop other servers or use a different port
- "Module not found" → Make sure you're in the project root directory
- Import errors → Check that all dependencies are installed (`pip install -r requirements.txt`)

**Frontend:**
- "Port 3000 is already in use" → Stop other applications using port 3000, or Vite will auto-select another port
- "Cannot find module" → Make sure you've installed dependencies (`npm install`)
- Connection errors → Make sure the backend server is running on port 8000
