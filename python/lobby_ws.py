"""
Lobby WebSocket handlers and endpoints
"""
from fastapi import WebSocket
from datetime import datetime
from .util import conmanager, dbmanager
from .game_core import Game

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
async def handle_create_game(websocket: WebSocket, game_id: str):
    """Handle create_game action - creates a new game session"""
    dbmanager.create_chat_table(game_id)
    
    # Create game instance
    game = Game(game_id)
    
    # Auto-join creator to the game
    await conmanager.join_game(websocket, game_id)
    
    # Get user_info for this connection and add to game users list
    user_info = conmanager.get_user_info(websocket)
    if user_info:
        game.users.append(user_info)
        # Broadcast updated users list to all clients in the game
        await conmanager.broadcast_to_game(game_id, {
            'type': 'users_list',
            'users': game.users
        })
    
    now = datetime.now().isoformat()
    msg = dbmanager.save_chat(game_id, "System", now, f"Game {game_id} started.", "system", None)
    await conmanager.broadcast_to_game(game_id, msg)
    await websocket.send_json({
        'type': 'game_created',
        'game_id': game_id
    })

    return game


async def handle_join_game(websocket: WebSocket, game_id: str, game):
    """Handle join_game action - joins a client to an existing game"""
    
    await conmanager.join_game(websocket, game_id)
    
    # Get user_info for this connection and add to game users list
    user_info = conmanager.get_user_info(websocket)
    if user_info:
        # Check if user is already in the list (avoid duplicates)
        if not any(u.get('id') == user_info.get('id') for u in game.users):
            game.users.append(user_info)
            # Broadcast updated users list to all clients in the game
            await conmanager.broadcast_to_game(game_id, {
                'type': 'users_list',
                'users': game.users
            })
    
    await websocket.send_json({
        'type': 'joined_game',
        'game_id': game_id
    })

