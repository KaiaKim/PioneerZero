How to start your FastAPI server:

Method 1: From your project root (recommended)
Open a terminal in `F:\2025\Pioneer_Zero\newGame` and run:
```bash
python -m uvicorn python._global:app --host 0.0.0.0 --port 8000 --reload
```

What each part means:
- `python -m uvicorn` — runs uvicorn using Python
- `python._global:app` — module path (`python/_global.py`) and the FastAPI app instance (`app`)
- `--host 0.0.0.0` — listen on all network interfaces (accessible from other devices on your network)
- `--port 8000` — use port 8000
- `--reload` — auto-restart on code changes (development only)

Alternative (localhost only):
```bash
python -m uvicorn python._global:app --host 127.0.0.1 --port 8000 --reload
```

To stop the server:
Press `Ctrl+C` in the terminal where it's running.

Verifying it's running:


[1 tool called]


Server is currently running (PID: 2404).

**Quick reference card:**

**Start server:**
```bash
python -m uvicorn python._global:app --host 0.0.0.0 --port 8000 --reload
```

**Stop server:**
- Press `Ctrl+C` in the terminal

**Check if running:**
```bash
netstat -ano | findstr :8000 | findstr LISTENING
```

**Access your site:**
- Open browser to: `http://localhost:8000`

**Tips:**
- Keep the terminal window open while the server runs
- With `--reload`, it auto-restarts when you save Python files
- If port 8000 is busy, use `--port 8001` (or another port)
- Error messages appear in the terminal

**Common issues:**
- "Address already in use" → Port is taken; stop other servers or use a different port
- "Module not found" → Make sure you're in the project root directory
- Import errors → Check that all dependencies are installed (`pip install -r requirements.txt`)

Need help with anything specific about running the server?