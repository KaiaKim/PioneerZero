"""
Game WebSocket handlers
"""
from fastapi import WebSocket
import asyncio
from .util import conM, dbM, timeM
import time

skill_list = ["스킬1", "스킬2", "스킬3", "스킬4"]

async def handle_load_room(websocket: WebSocket, game):
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
            'in_combat': game.in_combat,
            'current_round': game.current_round,
            'phase': game.phase,
            'action_submission_status': game.get_action_submission_status(),
            'resolved_actions': game.resolved_actions
        }
    })
    
    # Load and send chat history to the requesting client
    user_info = conM.get_user_info(websocket)
    viewer_id = user_info.get('id') if user_info else None
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

async def handle_join_player_slot(websocket: WebSocket, message: dict, game):
    """Handle join_player_slot action - adds a player to a waiting room slot"""    
    slot = message.get("slot")
    user_info = conM.get_user_info(websocket)

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
        await conM.broadcast_to_game(game.id, {
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
        await conM.broadcast_to_game(game.id, {
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
    user_info = conM.get_user_info(websocket)
    
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
        await conM.broadcast_to_game(game.id, {
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
    user_info = conM.get_user_info(websocket)
    
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
        await conM.broadcast_to_game(game.id, {
            "type": "players_list",
            "players": game.players
        })
    else:
        await websocket.send_json({
            "type": "set_ready_failed",
            "message": result["message"]
        })


async def handle_chat(websocket: WebSocket, message: dict, game):
    """Handle chat messages and commands"""
    content = message.get("content", "")
    sender = message.get("sender")
    user_info = conM.get_user_info(websocket)
    user_id = user_info.get('id')
    msg = None
    secret_msg = None

    if content[0] == "/": #we've already checked if content is not empty
        # Save the user's command as secret (only visible to the user)
        secret_msg = dbM.save_chat(game.id, content, sender=sender, sort="secret", user_id=user_id)
        
        # Handle commands
        command = content[1:].split()
        result = None
        err = None
        if game.in_combat == False:
            if command[0] == "참여" or command[0] == "join":
                pass
            elif command[0] == "관전" or command[0] == "leave":
                pass
            else:
                err = "사용 가능한 준비 명령어: 참여, 관전."

        elif game.in_combat == True:
            player_ids = [player['info']['id'] for player in game.players]
            if user_id in player_ids:
                if game.phase == "position_declaration":
                    if command[0] == "위치" or command[0] == "pos":
                        result, err = game.posM.declare_position(user_id, command)
                elif game.phase == "action_declaration":
                    if command[0] in ["근거리공격", "원거리공격", "대기"]:
                        submit, err = game.declare_attack(user_id, command)
                        if submit and not err:
                            result = '행동 선언 완료'
                            await websocket.send_json({
                                "type": "declared_attack",
                                "attack_info": submit
                            })
                            await conM.broadcast_to_game(game.id, {
                                "type": "action_submission_update",
                                "action_submission_status": game.get_action_submission_status()
                            })
                    elif command[0] in skill_list:
                        result, err = game.declare_skill(user_id, command)
                        if result and not err:
                            await conM.broadcast_to_game(game.id, {
                                "type": "action_submission_update",
                                "action_submission_status": game.get_action_submission_status()
                            })

                    else:
                        err = "사용 가능한 전투 명령어가 아닙니다."
            else:
                err = "전투 명령어는 전투 참여자만 사용할 수 있습니다."
        
        # Save and broadcast the result as system message (visible to all)
        if result:
            msg = dbM.save_chat(game.id, result, user_id=user_id)
        if err:
            msg = dbM.save_chat(game.id, err, sort="error", user_id=user_id)
        if not result and not err:
            err = "명령어를 잘못 입력했습니다. 다시 시도해주세요."
            msg = dbM.save_chat(game.id, err, sort="error", user_id=user_id)
    else:
        # Regular chat message
        msg = dbM.save_chat(game.id, content, sender=sender, sort="user", user_id=user_id)
    
    if secret_msg:
        await conM.broadcast_to_game(game.id, secret_msg)

    await conM.broadcast_to_game(game.id, msg)

### phase flow functions
async def phase_wrapper(game):
    phase_task = getattr(game, "phase_task", None)
    if phase_task and not phase_task.done():
        return
    game.phase_task = asyncio.create_task(_phase_flow(game))

async def _phase_flow(game):
    try:
        await timeM.offset_timer(game)
        if not await kickoff(game):
            return

        game.in_combat = True
        await timeM.offset_timer(game)
        await position_declaration(game)
        await timeM.phase_timer(game)
        await position_resolution(game)
        
        defeated_team = None
        for _ in range(game.max_rounds):
            await timeM.offset_timer(game)
            await start_round(game)
            await timeM.offset_timer(game)
            await action_declaration(game)
            await timeM.phase_timer(game)

            await timeM.offset_timer(game)
            await action_resolution(game)

            defeated_team = await end_round(game)
            if defeated_team is not None:
                break

        if defeated_team is None:
            defeated_team = game.check_all_players_defeated()[1]

        await timeM.offset_timer(game)
        await wrap_up(game, defeated_team)
        game.in_combat = False

    except asyncio.CancelledError:
        pass
    except Exception as exc:
        print(f"Phase flow error: {exc}")
    finally:
        if getattr(game, "phase_task", None) is asyncio.current_task():
            game.phase_task = None

async def kickoff(game):
    if not game.SlotM.are_all_players_ready():
        return False

    # Save initial combat snapshot (one-time backup)
    dbM.save_game_session(game)
    
    result = f"전투 {game.id}를 시작합니다."
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)
    
    await conM.broadcast_to_game(game.id, {
        "type": "combat_started"
    })
    return True
    
async def position_declaration(game):
    game.phase = 'position_declaration'
    result = '위치 선언 페이즈입니다. 시작 위치를 선언해주세요.'
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)

async def position_resolution(game):
    for player in game.players:
        if player['character']['pos'] is None:
            game.posM.assign_random_pos(player)

    # while players are in same cell:
    # assign random pos to one of the players
    pos_list = [
        f"{p['character']['name']}: {p['character']['pos']}, " for p in game.players]
    result = f'위치 선언이 종료되었습니다. 시작 위치는 {pos_list} 입니다.'
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)

async def start_round(game):
    game.current_round += 1
    result = f'라운드 {game.current_round} 선언 페이즈입니다.'
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)

async def action_declaration(game):
    game.phase = 'action_declaration'
    game.action_queue = []
    result = f'스킬과 행동을 선언해주세요.'
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)
    await conM.broadcast_to_game(game.id, {
        "type": "action_submission_update",
        "action_submission_status": game.get_action_submission_status()
    })

async def action_resolution(game):
    game.phase = 'resolution'
    result = f'라운드 {game.current_round} 해결 페이즈입니다. 계산을 시작합니다.'
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)

async def end_round(game):
    """라운드 종료 방송"""
    is_team_defeated, defeated_team = game.check_all_players_defeated()
    
    if is_team_defeated:
        return defeated_team

    return None

async def wrap_up(game, defeated_team: int):
    """전투 종료 단계 처리"""
    game.phase = 'wrap-up'
    game.in_combat = False
    winner = 'white' if defeated_team == 0 else 'blue'
    return '전투가 종료되었습니다. {} 팀이 승리했습니다.'.format(winner)
