"""
Game WebSocket handlers
"""
from fastapi import WebSocket
import asyncio
from .util import conmanager, dbmanager

async def handle_load_room(websocket: WebSocket, game):
    """Handle load_room action - loads game state and chat history"""
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
    
    # Send combat state to the requesting client
    await websocket.send_json({
        "type": "combat_state",
        "combat_state": {
            'in_combat': game.phaseM.in_combat,
            'current_round': game.phaseM.current_round,
            'phase': game.phaseM.phase,
            'action_queue': game.phaseM.action_queue,
            'resolved_actions': game.phaseM.resolved_actions
        }
    })
    
    # Load and send chat history to the requesting client
    user_info = conmanager.get_user_info(websocket)
    viewer_id = user_info.get('id') if user_info else None
    chat_history_rows = dbmanager.get_chat_history(game.id, viewer_id=viewer_id)
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
    existing_slot = game.SlotM.get_player_by_user_id(user_info.get('id'))
    if existing_slot and existing_slot != slot:
        await websocket.send_json({
            "type": "join_slot_failed",
            "message": f"You are already in slot {existing_slot}"
        })
        return
    
    result = game.SlotM.add_player(slot, slot_idx, user_info)
    
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
    
    result = game.SlotM.add_bot(slot, slot_idx)
    
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
        slot = game.SlotM.get_player_by_user_id(user_info.get('id'))
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
    
    result = game.SlotM.remove_player(slot, slot_idx)
    
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


async def handle_set_ready(websocket: WebSocket, message: dict, game):
    """Handle set_ready action - toggles ready state for a player"""
    slot = message.get("slot")
    ready = message.get("ready")  # boolean: True or False
    user_info = conmanager.get_user_info(websocket)
    
    if slot is None or slot < 1 or slot > game.player_num:
        await websocket.send_json({
            "type": "set_ready_failed",
            "message": "Invalid slot number"
        })
        return
    
    if ready is None:
        await websocket.send_json({
            "type": "set_ready_failed",
            "message": "Ready state not provided"
        })
        return
    
    slot_idx = slot - 1
    result = game.SlotM.set_player_ready(slot, slot_idx, user_info, ready)
    
    if result["success"]:
        # Broadcast updated players list to all clients
        await conmanager.broadcast_to_game(game.id, {
            "type": "players_list",
            "players": game.players
        })
    else:
        await websocket.send_json({
            "type": "set_ready_failed",
            "message": result["message"]
        })


async def handle_start_combat(game):
    # Check if all players are ready
    if not game.SlotM.are_all_players_ready():
        return
    
    # Start combat by advancing to preparation phase
    result = game.phaseM.preperation()
    
    # Start 3 second countdown
    for countdown in [3, 2, 1]:
        await conmanager.broadcast_to_game(game.id, {
            "type": "combat_countdown",
            "seconds": countdown
        })
        await asyncio.sleep(1)

    msg = dbmanager.save_chat(game.id, result)
    await conmanager.broadcast_to_game(game.id, msg)
    # After countdown, broadcast combat started
    await conmanager.broadcast_to_game(game.id, {
        "type": "combat_started",
        "combat_state": {
            'in_combat': game.phaseM.in_combat,
            'current_round': game.phaseM.current_round,
            'phase': game.phaseM.phase,
            'action_queue': game.phaseM.action_queue,
            'resolved_actions': game.phaseM.resolved_actions
        }
    })
    
    result = game.phaseM.position_declaration()
    msg = dbmanager.save_chat(game.id, result)
    await conmanager.broadcast_to_game(game.id, msg)



async def handle_chat(websocket: WebSocket, message: dict, game):
    """Handle chat messages and commands"""
    content = message.get("content", "")
    sender = message.get("sender")
    user_info = conmanager.get_user_info(websocket)
    user_id = user_info.get('id')
    player_ids = [player['info']['id'] for player in game.players]
    msg = None
    if content[0] == "/": #we've already checked if content is not empty
        # Save the user's command as secret (only visible to the user)
        secret_msg = dbmanager.save_chat(game.id, content, sender=sender, sort="secret", user_id=user_id)
        await conmanager.broadcast_to_game(game.id, secret_msg)
        
        # Handle commands
        command = content[1:].split()
        result = None
        err = None
        if game.phaseM.in_combat == False:
            if command[0] == "참여" or command[0] == "join":
                pass
            elif command[0] == "관전" or command[0] == "leave":
                pass
            else:
                err = "사용 가능한 준비 명령어: 참여, 관전."

        elif game.phaseM.in_combat == True:
            if user_id in player_ids:
                if command[0] == "위치" or command[0] == "pos":
                    result = game.posM.declare_position(sender, command)
                elif command[0] == "이동" or command[0] == "move":
                    result = game.posM.move_player(sender, command)
                elif command[0] == "스킬" or command[0] == "skill":
                    result = game.use_skill(sender, command)
                elif command[0] == "행동" or command[0] == "act":
                    result = game.perform_action(sender, command)
                else:
                    err = "사용 가능한 전투 명령어: 위치, 이동, 스킬, 행동."
            else:
                err = "전투 명령어는 전투 참여자만 사용할 수 있습니다."
        
        # Save and broadcast the result as system message (visible to all)
        if result:
            msg = dbmanager.save_chat(game.id, result, user_id=user_id)
        else:
            err = "알 수 없는 명령어입니다."

        if err:
            msg = dbmanager.save_chat(game.id, err, sort="error", user_id=user_id)
    else:
        # Regular chat message
        msg = dbmanager.save_chat(game.id, content, sender=sender, sort="user", user_id=user_id)
    
    await conmanager.broadcast_to_game(game.id, msg)

