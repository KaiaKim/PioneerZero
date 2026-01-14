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
                    result, err = game.posM.declare_position(sender, command)
                elif command[0] == "이동" or command[0] == "move":
                    result, err = game.posM.move_player(sender, command)
                elif command[0] == "스킬" or command[0] == "skill":
                    result, err = game.use_skill(sender, command)
                elif command[0] == "행동" or command[0] == "act":
                    result, err = game.perform_action(sender, command)
                else:
                    err = "사용 가능한 전투 명령어: 위치, 이동, 스킬, 행동."
            else:
                err = "전투 명령어는 전투 참여자만 사용할 수 있습니다."
        
        # Save and broadcast the result as system message (visible to all)
        if result:
            msg = dbmanager.save_chat(game.id, result, user_id=user_id)
        if err:
            msg = dbmanager.save_chat(game.id, err, sort="error", user_id=user_id)

        if not result and not err:
            err = "명령어를 잘못 입력했습니다. 다시 시도해주세요."
            msg = dbmanager.save_chat(game.id, err, sort="error", user_id=user_id)
    else:
        # Regular chat message
        msg = dbmanager.save_chat(game.id, content, sender=sender, sort="user", user_id=user_id)
    
    if secret_msg:
        await conmanager.broadcast_to_game(game.id, secret_msg)

    await conmanager.broadcast_to_game(game.id, msg)

class PhaseManager():
    def __init__(self, game):
        self.game = game

        # 전투 상태
        self.in_combat = False
        self.current_round = 0
        self.phase = 'preparation'  # 'preparation', 'kickoff', 'position_declaration', 'action_declaration', 'resolution', 'wrap-up'
        self.action_queue = []
        self.resolved_actions = []

    async def kickoff(self):
    # Check if all players are ready
        if not self.game.SlotM.are_all_players_ready():
            return
        
        # Start combat by advancing to preparation phase
        result = f"전투 {self.game.id}를 시작작합니다."
        msg = dbmanager.save_chat(self.game.id, result)
        await conmanager.broadcast_to_game(self.game.id, msg)
        
        # Start 3 second countdown
        for countdown in [3, 2, 1]:
            await conmanager.broadcast_to_game(self.game.id, {
                "type": "combat_countdown",
                "seconds": countdown
            })
            await asyncio.sleep(1)

        msg = dbmanager.save_chat(self.game.id, result)
        await conmanager.broadcast_to_game(self.game.id, msg)
        # After countdown, broadcast combat started
        await conmanager.broadcast_to_game(self.game.id, {
            "type": "combat_started"
        })
    
        self.position_declaration()
        
    async def position_declaration(self):
        """위치 선언 단계 처리"""
        self.phase = 'position_declaration'
        result = '위치 선언 페이즈입니다. 시작 위치를 선언해주세요.'
        msg = dbmanager.save_chat(self.game.id, result)
        await conmanager.broadcast_to_game(self.game.id, msg)

        #60 sec countdown
        for i in range(60):
            await asyncio.sleep(1)
            if i % 10 == 0:
                await conmanager.broadcast_to_game(self.game.id, {
                    "type": "position_declaration_timer",
                    "seconds": 60 - i
                })

        for player in self.game.players:
            if player['character']['position'] is None:
                self.posM.assign_random_pos(player)
        
        #while players are in same cell:
            #assign random pos to one of the players
        '''
        pos_list = [
            f'{p['character']['name']}: {p['character']['position']}, ' for p in self.game.players]
'''
        result = f'위치 선언이 종료되었습니다. 시작 위치는 temp 입니다.'
        msg = dbmanager.save_chat(self.game.id, result)
        await conmanager.broadcast_to_game(self.game.id, msg)
        
        self.start_round(1) # 1st round
        
    def start_round(self):
        """라운드 시작 방송"""
        self.current_round += 1
        self.phase = 'action_declaration'
        return '라운드 {} 선언 페이즈입니다. 스킬과 행동을 선언해주세요.'.format(self.current_round)
    
    def action_declaration(self):
        """행동 선언 단계 처리"""
        self.phase = 'action_declaration'
        # 타이머 시작 (60초)
        self.game.timer = {
            'type': 'action_declaration',
            'start_time': time.time(),
            'duration': 60,
            'is_running': True,
            'paused_at': None,
            'elapsed_before_pause': 0
        }
        return '라운드 {} 선언 페이즈입니다. 스킬과 행동을 선언해주세요.'.format(self.current_round)
    
    def resolution(self):
        """해결 단계 처리"""
        self.phase = 'resolution'
        
        # 타이머 정지
        if self.game.timer.get('is_running'):
            self.game.timer['is_running'] = False
            self.game.timer['elapsed_before_pause'] = time.time() - self.game.timer['start_time']
        
        return '라운드 {} 선언이 끝났습니다. 계산을 시작합니다.'.format(self.current_round)

    def end_round(self):
        """라운드 종료 방송"""
        is_team_defeated, defeated_team = self.check_all_players_defeated()
        
        if is_team_defeated:
            self.wrap_up(defeated_team)
        else:
            self.current_round += 1
            self.action_declaration()

    def wrap_up(self, defeated_team: int):
        """전투 종료 단계 처리"""
        self.phase = 'wrap-up'
        self.in_combat = False
        winner = 'white' if defeated_team == 0 else 'blue'
        return '전투가 종료되었습니다. {} 팀이 승리했습니다.'.format(winner)

    def check_all_players_defeated(self):
        """
        한 팀의 모든 플레이어가 전투불능인지 확인
        
        Returns:
            tuple: (is_team_defeated: bool, defeated_team: int or None)
                - is_team_defeated: 한 팀이 전투불능인지 여부
                - defeated_team: 0=white team defeated, 1=blue team defeated, None=no team defeated
        """
        white_team_defeated = True
        blue_team_defeated = True
        
        for player in self.game.players:
            if player.get('occupy') != 1:
                continue
            if not player.get('character'):
                continue
            
            team = player.get('team')
            current_hp = player['character'].get('current_hp', 0)
            
            if team == 0:
                if current_hp > 0:
                    white_team_defeated = False
            elif team == 1:
                if current_hp > 0:
                    blue_team_defeated = False
        
        if white_team_defeated:
            return True, 0
        elif blue_team_defeated:
            return True, 1
        else:
            return False, None