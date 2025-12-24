"""
Lobby WebSocket handlers and endpoints
"""
from fastapi import WebSocket
from datetime import datetime
import uuid
from .util import manager
from .main import sessions
from .game_core import Game
from .game_chat import create_chat_table, save_chat


# HTTP endpoint for listing active sessions
async def list_sessions():
    """Return list of active game sessions for the lobby"""
    return {
        "type": "list_games",
        "sessions": [
            {
                "game_id": game_id,
                "player_count": len(manager.get_game_connections(game_id)),
                "status": "active"
            }
            for game_id, game in sessions.items()
        ]
    }


# WebSocket message handlers for lobby operations
async def handle_create_game(websocket: WebSocket):
    """Handle create_game action - creates a new game session"""
    game_id = uuid.uuid4().hex[:10].upper()  # generate a random session id
    sessions[game_id] = Game(game_id)  # create a new game session
    create_chat_table(game_id)
    
    # Auto-join creator to the game
    await manager.join_game(websocket, game_id)
    
    now = datetime.now().isoformat()
    msg = save_chat(game_id, "System", now, f"Game {game_id} started.", "system")
    await manager.broadcast_to_game(game_id, msg)
    await websocket.send_json({
        'type': 'game_created',
        'game_id': game_id
    })


async def handle_join_game(websocket: WebSocket, message: dict):
    """Handle join_game action - joins a client to an existing game"""
    game_id = message.get("game_id")
    if game_id and game_id in sessions:
        await manager.join_game(websocket, game_id)
        await websocket.send_json({
            'type': 'joined_game',
            'game_id': game_id
        })
    else:
        await websocket.send_json({
            'type': 'join_failed',
            'message': 'Game not found'
        })

