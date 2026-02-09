"""
Lobby WebSocket handlers and endpoints
"""
from dataclasses import asdict
from fastapi import WebSocket
from ..util import conM, dbM
from ..services.game_core.session import Game

# HTTP endpoint for listing active sessions
async def handle_list_rooms(websocket: WebSocket, chat_tables: list[str]):
    """Return list of active game sessions for the lobby"""
    # Convert list of game IDs to list of session objects
    session_list = [{"game_id": game_id} for game_id in chat_tables]
    await websocket.send_json({
        "type": "list_rooms",
        "session_ids": session_list
    })


# WebSocket message handlers for lobby operations
async def handle_create_room(websocket: WebSocket, game_id: str, player_num: int):
    """Handle create_room action - creates a new game session"""
    dbM.create_chat_table(game_id)
    
    # Create game instance with specified player_num
    game = Game(game_id, player_num)
    
    # Auto-join creator to the game
    await conM.join_game(websocket, game_id)
    
    # Get user_info for this connection and add to game users list
    user_info = conM.get_user_info(websocket)
    game.users.append(user_info)
    # Broadcast updated users list to all clients in the game
    await conM.broadcast_to_game(game_id, {
        'type': 'users_list',
        'users': [asdict(u) for u in game.users]
    })

    result = f"방이 생성되었습니다.\n방 ID: {game_id}"
    msg = dbM.save_chat(game_id, result)
    await conM.broadcast_to_game(game_id, msg)
    await websocket.send_json({
        'type': 'game_created',
        'game_id': game_id
    })

    return game


async def handle_join_room(websocket: WebSocket, game_id: str, game):
    """Handle join_room action - joins a client to an existing game"""
    
    await conM.join_game(websocket, game_id)
    
    # Get user_info for this connection and add to game users list
    user_info = conM.get_user_info(websocket)
    if not any(u.id == user_info.id for u in game.users):
        game.users.append(user_info)
        await conM.broadcast_to_game(game_id, {
            'type': 'users_list',
            'users': [asdict(u) for u in game.users]
        })
    
    await websocket.send_json({
        'type': 'joined_game',
        'game_id': game_id
    })


async def handle_load_room(websocket: WebSocket, game):
    # Send users list to the requesting client
    await websocket.send_json({
        "type": "users_list",
        "users": [asdict(u) for u in game.users]
    })
    
    # Send players list to the requesting client
    await websocket.send_json({
        "type": "players_list",
        "players": [asdict(p) for p in game.players]
    })
    
    # Send combat state to the requesting client
    await websocket.send_json({
        "type": "combat_state",
        "combat_state": {
            'in_combat': game.in_combat,
            'current_round': game.current_round,
            'phase': game.phase,
            'submitted': game.count_submissions(),
        }
    }) ###combat state?? This is makeshift should refactor later
    
    # Load and send chat history to the requesting client
    user_info = conM.get_user_info(websocket)
    viewer_id = user_info.id if user_info else None
    chat_history_rows = dbM.get_chat_history(game.id, viewer_id=viewer_id)
    chat_messages = []
    for row in chat_history_rows:
        # row format: (chat_id, sender, time, content, sort, user_id)
        chat_messages.append({
            "type": "chat",
            "sender": row[1],
            "time": row[2],
            "content": row[3],
            "sort": row[4],
            "user_id": row[5]
        })
    
    # Send chat history only to the requesting client
    await websocket.send_json({
        "type": "chat_history",
        "messages": chat_messages
    })
