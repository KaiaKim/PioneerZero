from dataclasses import asdict
from fastapi import WebSocket
import asyncio
from ...util import conM
from ...services.game_core import join as join_funcs

async def handle_join_player_slot(websocket: WebSocket, message: dict, game):
    """Handle join_player_slot action - adds a player to a waiting room slot (slotIndex 0-based)"""
    slot_idx = message.get("slotIndex")
    if slot_idx is None:
        slot_idx = message.get("slot")
        if slot_idx is not None:
            slot_idx = slot_idx - 1  # Legacy: client sent 1-based
    user_info = conM.get_user_info(websocket)

    if slot_idx is None or slot_idx < 0 or slot_idx >= game.player_num:
        await websocket.send_json({
            "type": "join_slot_failed",
            "message": "Invalid slot index"
        })
        return
    
    existing_slot_idx = join_funcs.get_player_by_user_id(game, user_info.get('id'))
    if existing_slot_idx is not None and existing_slot_idx != slot_idx:
        await websocket.send_json({
            "type": "join_slot_failed",
            "message": f"You are already in slot {existing_slot_idx + 1}"
        })
        return
    
    result = join_funcs.add_player(game, slot_idx, user_info)
    
    if result["success"]:
        await conM.broadcast_to_game(game.id, {
            "type": "players_list",
            "players": [asdict(p) for p in game.players]
        })
    else:
        await websocket.send_json({
            "type": "join_slot_failed",
            "message": result["message"]
        })


async def handle_add_bot_to_slot(websocket: WebSocket, message: dict, game):
    """Handle add_bot_to_slot action - adds a bot to a waiting room slot (slotIndex 0-based)"""
    slot_idx = message.get("slotIndex")
    if slot_idx is None:
        slot_idx = message.get("slot")
        if slot_idx is not None:
            slot_idx = slot_idx - 1  # Legacy: client sent 1-based

    if slot_idx is None or slot_idx < 0 or slot_idx >= game.player_num:
        await websocket.send_json({
            "type": "add_bot_failed",
            "message": "Invalid slot index"
        })
        return
    
    result = join_funcs.add_bot(game, slot_idx)
    
    if result["success"]:
        await conM.broadcast_to_game(game.id, {
            "type": "players_list",
            "players": [asdict(p) for p in game.players]
        })
    else:
        await websocket.send_json({
            "type": "add_bot_failed",
            "message": result["message"]
        })


async def handle_leave_player_slot(websocket: WebSocket, message: dict, game):
    """Handle leave_player_slot action - removes a player from a waiting room slot (slotIndex 0-based)"""
    
    slot_idx = message.get("slotIndex")
    if slot_idx is None:
        slot_idx = message.get("slot")
        if slot_idx is not None:
            slot_idx = slot_idx - 1  # Legacy: client sent 1-based
    user_info = conM.get_user_info(websocket)
    
    if slot_idx is None:
        slot_idx = game.get_player_by_user_id(user_info.get('id'))
        if slot_idx is None:
            await websocket.send_json({
                "type": "leave_slot_failed",
                "message": "You are not in any slot"
            })
            return
    elif slot_idx < 0 or slot_idx >= game.player_num:
        await websocket.send_json({
            "type": "leave_slot_failed",
            "message": "Invalid slot index"
        })
        return
    
    info = game.players[slot_idx].info
    is_bot = info and (info.get('is_bot') is True or (info.get('id') and str(info.get('id')).startswith('bot_')))
    if not is_bot:
        if not info or info.get('id') != user_info.get('id'):
            await websocket.send_json({
                "type": "leave_slot_failed",
                "message": "You don't own this slot"
            })
            return
    
    result = join_funcs.remove_player(game, slot_idx)
    
    if result["success"]:
        await conM.broadcast_to_game(game.id, {
            "type": "players_list",
            "players": [asdict(p) for p in game.players]
        })
    else:
        await websocket.send_json({
            "type": "leave_slot_failed",
            "message": result["message"]
        })


async def handle_set_ready(websocket: WebSocket, message: dict, game):
    """Handle set_ready action - toggles ready state for a player (slotIndex 0-based)"""
    slot_idx = message.get("slotIndex")
    if slot_idx is None:
        slot_idx = message.get("slot")
        if slot_idx is not None:
            slot_idx = slot_idx - 1  # Legacy: client sent 1-based
    ready = message.get("ready")  # boolean: True or False
    user_info = conM.get_user_info(websocket)
    
    if slot_idx is None or slot_idx < 0 or slot_idx >= game.player_num:
        await websocket.send_json({
            "type": "set_ready_failed",
            "message": "Invalid slot index"
        })
        return
    
    if ready is None:
        await websocket.send_json({
            "type": "set_ready_failed",
            "message": "Ready state not provided"
        })
        return
    
    result = join_funcs.set_player_ready(game, slot_idx, user_info, ready)
    
    if result["success"]:
        await conM.broadcast_to_game(game.id, {
            "type": "players_list",
            "players": [asdict(p) for p in game.players]
        })
    else:
        await websocket.send_json({
            "type": "set_ready_failed",
            "message": result["message"]
        })




# Background task to periodically check for connection-lost timeouts
async def run_connection_lost_timeout_checks(rooms):
    """Periodically runs connection-lost timeout checks for all games"""
    while True:
        try:
            for game_id, game in rooms.items():
                if join_funcs.clear_expired_connection_lost_slots(game):
                    await conM.broadcast_to_game(game_id, {
                        'type': 'players_list',
                        'players': [asdict(p) for p in game.players]
                    })
            await asyncio.sleep(1)  # Check every second
        except Exception as e:
            print(f"Error in connection-lost timeout check: {e}")
            await asyncio.sleep(1)
