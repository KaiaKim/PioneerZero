"""
Lobby WebSocket handlers and endpoints
"""
from fastapi import WebSocket
from datetime import datetime
import uuid
from .util import conmanager, dbmanager
from .game_core import Game
from .main import sessions

# HTTP endpoint for listing active sessions
async def handle_list_sessions(websocket: WebSocket, chat_tables: list[str]):
    """Return list of active game sessions for the lobby"""
    # Convert list of game IDs to list of session objects
    session_list = [{"game_id": game_id} for game_id in chat_tables]
    await websocket.send_json({
        "type": "list_games",
        "session_ids": session_list
    })


# WebSocket message handlers for lobby operations
async def handle_create_game(websocket: WebSocket):
    """Handle create_game action - creates a new game session"""
    game_id = uuid.uuid4().hex[:10].upper()  # generate a random session id
    sessions[game_id] = Game(game_id)  # create a new game session
    dbmanager.create_chat_table(game_id)
    
    # Auto-join creator to the game
    await conmanager.join_game(websocket, game_id)
    
    now = datetime.now().isoformat()
    msg = dbmanager.save_chat(game_id, "System", now, f"Game {game_id} started.", "system")
    await conmanager.broadcast_to_game(game_id, msg)
    await websocket.send_json({
        'type': 'game_created',
        'game_id': game_id
    })


async def handle_join_game(websocket: WebSocket, message: dict):
    """Handle join_game action - joins a client to an existing game"""
    game_id = message.get("game_id")
    if not game_id:
        await websocket.send_json({
            'type': 'join_failed',
            'message': 'Game ID not provided'
        })
        return
    
    # Load game from database if not in sessions (lazy loading)
    if game_id not in sessions:
        # Check if game exists in database
        chat_tables = dbmanager.get_chat_tables()
        if game_id in chat_tables:
            # Load game from database
            sessions[game_id] = dbmanager.load_game_from_chat(game_id)
        else:
            await websocket.send_json({
                'type': 'join_failed',
                'message': 'Game not found'
            })
            return
    
    await conmanager.join_game(websocket, game_id)
    await websocket.send_json({
        'type': 'joined_game',
        'game_id': game_id
    })

