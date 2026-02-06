"""
FastAPI application setup and configuration
"""
from fastapi import FastAPI
import asyncio
from .config import settings
from .routers import auth, websocket
from .routers.game_router import slot
from .util import dbM

# FastAPI app instance
app = FastAPI()

# Include OAuth router
app.include_router(auth.router)

# Setup WebSocket endpoint
app.websocket("/ws")(websocket.websocket_endpoint)

# Setup startup event handler
@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup"""
    asyncio.create_task(slot.run_connection_lost_timeout_checks(websocket.rooms))
    # Prototype: load all saved rooms from snapshot
    for game_id in dbM.get_room_ids():
        game = dbM.load_game_session(game_id)
        if game:
            websocket.rooms[game_id] = game
