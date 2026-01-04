"""
Game WebSocket handlers
"""
from fastapi import WebSocket
from datetime import datetime
from .util import conmanager, dbmanager


async def handle_load_game(websocket: WebSocket, game):
    """Handle load_game action - loads game state and chat history"""
    vomit_data = game.vomit()
    # Send to requesting client only
    await websocket.send_json(vomit_data)
    
    # Send users list to the requesting client
    await websocket.send_json({
        "type": "users_list",
        "users": game.users
    })
    
    # Send players list to the requesting client
    await websocket.send_json({
        "type": "players_list",
        "players": game.players
    })
    
    # Load and send chat history to the requesting client
    chat_history_rows = dbmanager.get_chat_history(game.id)
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


async def handle_end_game(websocket: WebSocket, game_id: str):
    """Send end game message to all clients in the game. Do not delete data or remove connections."""
    now = datetime.now().isoformat()
    msg = dbmanager.save_chat(game_id, "System", now, f"Game {game_id} ended.", "system", None)
    await conmanager.broadcast_to_game(game_id, msg)


async def handle_join_player_slot(websocket: WebSocket, message: dict, game):
    """Handle join_player_slot action - adds a player to a waiting room slot"""    
    slot = message.get("slot")
    user_info = conmanager.get_user_info(websocket)

    if not slot or slot < 1 or slot > game.player_num:
        await websocket.send_json({
            "type": "join_slot_failed",
            "message": "Invalid slot number"
        })
        return
    
    slot_idx = slot - 1
    
    # Check if user is already in a different slot
    existing_slot = game.get_player_by_user_id(user_info.get('id'))
    if existing_slot and existing_slot != slot:
        await websocket.send_json({
            "type": "join_slot_failed",
            "message": f"You are already in slot {existing_slot}"
        })
        return
    
    result = game.add_player_to_slot(slot, slot_idx, user_info)
    
    if result["success"]:
        # Broadcast updated players list to all clients
        await conmanager.broadcast_to_game(game.id, {
            "type": "players_list",
            "players": game.players
        })
    else:
        await websocket.send_json({
            "type": "join_slot_failed",
            "message": result["message"]
        })


async def handle_add_bot_to_slot(websocket: WebSocket, message: dict, game):
    """Handle add_bot_to_slot action - adds a bot to a waiting room slot"""
    slot = message.get("slot")

    if not slot or slot < 1 or slot > game.player_num:
        await websocket.send_json({
            "type": "add_bot_failed",
            "message": "Invalid slot number"
        })
        return
    
    slot_idx = slot - 1
    
    result = game.add_bot_to_slot(slot, slot_idx)
    
    if result["success"]:
        # Broadcast updated players list to all clients
        await conmanager.broadcast_to_game(game.id, {
            "type": "players_list",
            "players": game.players
        })
    else:
        await websocket.send_json({
            "type": "add_bot_failed",
            "message": result["message"]
        })


async def handle_leave_player_slot(websocket: WebSocket, message: dict, game):
    """Handle leave_player_slot action - removes a player from a waiting room slot"""
    
    slot = message.get("slot")
    user_info = conmanager.get_user_info(websocket)
    
    # If slot_num not provided, find the user's slot
    if not slot:
        slot = game.get_player_by_user_id(user_info.get('id'))
        if not slot:
            await websocket.send_json({
                "type": "leave_slot_failed",
                "message": "You are not in any slot"
            })
            return
    elif slot < 1 or slot > game.player_num:
        await websocket.send_json({
            "type": "leave_slot_failed",
            "message": "Invalid slot number"
        })
        return
    
    slot_idx = slot - 1
    
    # Check if slot has a bot - anyone can remove bots
    player = game.players[slot_idx]['info']
    is_bot = player and (player.get('is_bot') == True or (player.get('id') and player.get('id').startswith('bot_')))
    
    # If not a bot, verify the user owns this slot
    if not is_bot:
        if not player or player['id'] != user_info.get('id'):
            await websocket.send_json({
                "type": "leave_slot_failed",
                "message": "You don't own this slot"
            })
            return
    
    result = game.remove_player_from_slot(slot, slot_idx)
    
    if result["success"]:
        # Broadcast updated players list to all clients
        await conmanager.broadcast_to_game(game.id, {
            "type": "players_list",
            "players": game.players
        })
    else:
        await websocket.send_json({
            "type": "leave_slot_failed",
            "message": result["message"]
        })


async def handle_chat(websocket: WebSocket, message: dict, game):
    """Handle chat messages and commands"""
    now = datetime.now().isoformat()
    content = message.get("content", "")
    sender = message.get("sender")
    user_info = conmanager.get_user_info(websocket)
    user_id = user_info.get('id')
    
    if content and content[0] == "/":
        # Handle commands
        command = content[1:]
        result = "unknown command"
        if "이동" in command:
            result = game.move_player(sender, command)
        elif "스킬" in command:
            result = "스킬 사용함"
        elif "행동" in command:
            result = "행동함"
        msg = dbmanager.save_chat(game.id, "System", now, result, "system", None)
    else:
        # Regular chat message
        msg = dbmanager.save_chat(game.id, sender, now, content, "user", user_id)
    
    await conmanager.broadcast_to_game(game.id, msg)

