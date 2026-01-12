from . import game_bot
import re
import time

class SlotManager():
    """
    Player Slot Management:
    -----------------------
    ✓ player_factory() - Create new player slot dict
    ✓ add_player() - Add human player to slot
    ✓ add_bot() - Add bot player to slot
    ✓ remove_player() - Remove player from slot
    ✓ set_player_connection_lost() - Mark player as connection-lost
    ✓ clear_expired_connection_lost_slots() - Cleanup expired connection-lost slots
    ✓ get_player_by_user_id() - Find player slot by user ID
    ✓ set_player_ready() - Set player ready state
    ✓ are_all_players_ready() - Check if all players are ready
    """
    def __init__(self, game):
        self.game = game
    
    def player_factory(self, slot: int = 0):
        """Factory function to create a new player slot dict. Each call returns a fresh dict."""
        return {
            'info': None,
            'character': None,
            'slot': slot,
            'ready': False,
            'team': 0,  # 0=white, 1=blue
            'occupy': 0,  # 0=empty, 1=occupied, 2=connection-lost
            'pos': None  # position on the game board
        }

    def add_player(self, slot: int, slot_idx: int, user_info: dict):
        """Add a player to a specific slot"""
        existing_player_info = self.game.players[slot_idx]['info']
        occupy = self.game.players[slot_idx]['occupy']
        
        # Check if it's the same user trying to rejoin
        is_same_user = existing_player_info and existing_player_info.get('id') == user_info.get('id')
        
        # Check if slot is occupied (status 1)
        if occupy == 1:
            if is_same_user:
                # Same user rejoining - already occupied by them, no change needed
                return {"success": True, "message": f"Player already in slot {slot}."}
            return {"success": False, "message": f"Slot {slot} is already occupied."}
        
        # Check if slot is connection-lost (status 2)
        if occupy == 2:
            if is_same_user:
                # Same user rejoining - update status to occupied
                self.game.players[slot_idx]['occupy'] = 1
                self.game.connection_lost_timers.pop(slot, None)
                return {"success": True, "message": f"Player rejoined slot {slot}."}
            return {"success": False, "message": f"Slot {slot} is connection-lost. Please wait."}
        
        # Slot is empty (status 0) - add player
        # Create player object with user_info and slot number
        player_obj = {
            'info': user_info,
            'character': game_bot.default_character,
            "slot": slot,
            'ready': False,  # Players must check ready checkbox
            'team': slot % 2, # 0=white,1=blue
            'occupy': 1  # 0=empty, 1=occupied, 2=connection-lost
        }
        self.game.players[slot_idx] = player_obj
        self.game.connection_lost_timers.pop(slot, None)  # Clear any connection-lost timer
        return {"success": True, "message": f"Player added to slot {slot}."}
    
    def add_bot(self, slot: int, slot_idx: int):
        """Add a bot to a specific slot"""
        occupy = self.game.players[slot_idx]['occupy']
        
        # Check if slot is occupied (status 1) or connection-lost (status 2)
        if occupy != 0:
            return {"success": False, "message": f"Slot {slot} is not empty."}
        
        # Slot is empty (status 0) - add bot
        # Get a bot from the bots array (use first available bot, or cycle if needed)
        bot_index = slot_idx % len(game_bot.bots) if game_bot.bots else 0
        bot_character = game_bot.bots[bot_index] if game_bot.bots else game_bot.default_character
        
        # Create bot info similar to user_info structure
        bot_info = {
            'id': f'bot_{slot}',  # Unique bot ID based on slot
            'name': bot_character.get('name', f'Bot_{slot}'),
            'is_bot': True
        }
        
        # Create player object with bot info and bot character
        player_obj = {
            'info': bot_info,
            'character': bot_character,
            'slot': slot,
            'ready': True, #bots are always ready
            'team': slot % 2,  # 0=white, 1=blue
            'occupy': 1  # 0=empty, 1=occupied, 2=connection-lost
        }
        self.game.players[slot_idx] = player_obj
        self.game.connection_lost_timers.pop(slot, None)  # Clear any connection-lost timer
        return {"success": True, "message": f"Bot added to slot {slot}."}
    
    def remove_player(self, slot: int, slot_idx: int):
        """Remove a player from a specific slot - sets status to empty"""
        if self.game.players[slot_idx]['occupy'] == 0:
            return {"success": False, "message": f"Slot {slot} is already empty."}
        
        self.game.players[slot_idx] = self.player_factory(slot)
        self.game.connection_lost_timers.pop(slot, None)  # Clear any connection-lost timer
        return {"success": True, "message": f"Player removed from slot {slot}."}
    
    def set_player_connection_lost(self, slot: int):
        """Set a player slot to connection-lost status (2) and set ready to False"""
        slot_idx = slot - 1
        if self.game.players[slot_idx]['occupy'] == 0:
            return {"success": False, "message": f"Slot {slot} is already empty."}
        
        self.game.players[slot_idx]['occupy'] = 2  # Set status to connection-lost
        self.game.players[slot_idx]['ready'] = False  # Set ready to False when connection is lost
        self.game.connection_lost_timers[slot] = time.time()  # Record timestamp
        return {"success": True, "message": f"Player slot {slot} set to connection-lost."}
    
    def clear_expired_connection_lost_slots(self, duration = 5.0):
        """
        Clear connection-lost slots that have exceeded the timeout duration.
        
        Behavior:
        - Combat NOT started: Clear slots after duration (default 5 seconds)
        - Combat started: Never clear slots (wait infinitely for player to rejoin)
        """
        # If combat has started, don't clear any connection-lost slots
        if self.game.phaseM.in_combat:
            return False
        
        # Combat not started - clear expired slots after timeout
        current_time = time.time()
        slots_to_clear = []
        
        for slot, timestamp in self.game.connection_lost_timers.items():
            if current_time - timestamp >= duration:  # default 5 seconds timeout
                slot_idx = slot - 1
                if self.game.players[slot_idx]['occupy'] == 2:  # Still connection-lost
                    self.game.players[slot_idx] = self.player_factory(slot)
                    slots_to_clear.append(slot)
        
        # Remove cleared slots from timers
        for slot in slots_to_clear:
            self.game.connection_lost_timers.pop(slot, None)
        
        return len(slots_to_clear) > 0  # Return True if any slots were cleared
    
    def get_player_by_user_id(self, user_id: str):
        """Get the slot number for a user_id, or None if not found"""
        for i, player in enumerate(self.game.players):
            if player.get('info') and player['info'].get('id') == user_id:
                return i + 1  # Return slot number (1-based)
        return None
    
    def set_player_ready(self, slot: int, slot_idx: int, user_info: dict, ready: bool):
        """Set ready state for a player. Only the player themselves can toggle their ready state."""
        # Verify the slot belongs to the user
        player = self.game.players[slot_idx]
        if not player.get('info') or player['info'].get('id') != user_info.get('id'):
            return {"success": False, "message": "You don't own this slot."}
        
        # Check if slot is occupied or connection-lost (can set ready in both states)
        if player['occupy'] not in [1, 2]:
            return {"success": False, "message": f"Slot {slot} is not occupied."}
        
        # Check if it's a bot (bots are always ready, can't be changed)
        if player['info'].get('is_bot') == True or (player['info'].get('id') and player['info'].get('id').startswith('bot_')):
            return {"success": False, "message": "Bots are always ready."}
        
        # Set ready state
        self.game.players[slot_idx]['ready'] = ready
        return {"success": True, "message": f"Ready state set to {ready}."}
    
    def are_all_players_ready(self):
        """
        Check if all slots are filled AND all players are ready.
        - All slots must have characters (occupy == 1 and character is not None)
        - All players must be ready (ready == True)
        - Bots are always considered ready
        """
        for player in self.game.players:
            # Check if slot is filled with a character
            if player['occupy'] != 1 or player['character'] is None:
                return False
            
            # Check if player is ready (bots are always ready by design, so we only check non-bots)
            is_bot = player.get('info') and (player['info'].get('is_bot') == True or 
                                            (player['info'].get('id') and player['info'].get('id').startswith('bot_')))
            
            if not is_bot and not player.get('ready', False):
                return False
        
        return True

class PhaseManager():
    """
    전투 단계 관리를 담당하는 클래스.
    Game 인스턴스를 받아 Game의 상태에 접근합니다.
    
    PhaseManager manages combat phase transitions. Takes a Game instance to access game state.
    """
    
    # Phase 상수 정의
    PHASE_PREPARATION = 'preparation'
    PHASE_POSITION_DECLARATION = 'position_declaration'
    PHASE_ACTION_DECLARATION = 'action_declaration'
    PHASE_RESOLUTION = 'resolution'
    PHASE_WRAP_UP = 'wrap-up'
    
    def __init__(self, game):
        """
        Args:
            game: Game 인스턴스 (combat_state, timer, players에 접근하기 위해)
        """
        self.game = game

        # 전투 상태
        self.in_combat = False
        self.current_round = 0
        self.phase = self.PHASE_PREPARATION  # 'preparation', 'position_declaration', 'action_declaration', 'resolution', 'end'
        self.action_queue = []
        self.resolved_actions = []
    
    @property
    def combat_state(self):
        """
        Backward compatibility property that returns combat state as a dict.
        This allows existing code to access combat_state as a dictionary.
        """
        return {
            'in_combat': self.in_combat,
            'current_round': self.current_round,
            'phase': self.phase,
            'action_queue': self.action_queue,
            'resolved_actions': self.resolved_actions
        }
    
    def advance_combat_phase(self, to_phase=None):
        """
        전투 단계를 전환하고 플레이어에게 알림 메시지를 반환하는 마스터 함수.
        실제 WebSocket 전송은 game_ws.py에서 처리 (PLAN_WEBSOCKET.md 참고).
        
        Args:
            to_phase: 전환할 단계. None이면 현재 단계에 따라 자동 전환.
                가능한 값: 'position_declaration', 'action_declaration', 'resolution', 'wrap-up'
                
        Returns:
            {
                "success": bool,
                "phase": str,  # 새로운 단계
                "round": int,  # 현재 라운드
                "message": str,  # 플레이어에게 보낼 메시지
                "notification_type": str,  # WebSocket 메시지 타입
                "additional_data": dict  # 추가 데이터 (combat_board, timer 등)
            }
        """
        # to_phase가 지정되지 않으면 현재 단계에 따라 자동 전환
        # Flow: preparation → position_declaration → action_declaration → resolution → (loop) → wrap-up
        if to_phase is None:
            if self.phase == self.PHASE_PREPARATION:
                to_phase = self.PHASE_POSITION_DECLARATION
            elif self.phase == self.PHASE_POSITION_DECLARATION:
                to_phase = self.PHASE_ACTION_DECLARATION
            elif self.phase == self.PHASE_ACTION_DECLARATION:
                to_phase = self.PHASE_RESOLUTION
            elif self.phase == self.PHASE_RESOLUTION:
                to_phase = self.PHASE_ACTION_DECLARATION
            else:
                return {"success": False, "message": "유효하지 않은 단계 전환"}
        
        additional_data = {}
        
        if to_phase == self.PHASE_POSITION_DECLARATION:
            return self._handle_position_declaration_phase(additional_data)
        
        elif to_phase == self.PHASE_ACTION_DECLARATION:
            return self._handle_action_declaration_phase(additional_data)
        
        elif to_phase == self.PHASE_RESOLUTION:
            return self._handle_resolution_phase(additional_data)
        
        elif to_phase == self.PHASE_WRAP_UP:
            return self._handle_wrap_up_phase(additional_data)
        
        return {"success": False, "message": "알 수 없는 단계"}
    
    def _handle_position_declaration_phase(self, additional_data):
        """위치 선언 단계 처리"""
        self.phase = self.PHASE_POSITION_DECLARATION
        self.in_combat = True
        self.current_round = 0
        message = '위치 선언 페이즈입니다. 시작 위치를 선언해주세요.'
        notification_type = 'position_declaration_phase'
        
        return {
            "success": True,
            "phase": self.phase,
            "round": self.current_round,
            "message": message,
            "notification_type": notification_type,
            "additional_data": additional_data
        }
    
    def _handle_action_declaration_phase(self, additional_data):
        """행동 선언 단계 처리"""
        self.phase = self.PHASE_ACTION_DECLARATION
        if self.current_round == 0:
            self.current_round = 1
        message = '라운드 {} 선언 페이즈입니다. 스킬과 행동을 선언해주세요.'.format(self.current_round)
        notification_type = 'action_declaration_phase'
        
        # 타이머 시작 (60초)
        self.game.timer = {
            'type': 'action_declaration',
            'start_time': time.time(),
            'duration': 60,
            'is_running': True,
            'paused_at': None,
            'elapsed_before_pause': 0
        }
        additional_data['timer'] = self.game.timer
        
        return {
            "success": True,
            "phase": self.phase,
            "round": self.current_round,
            "message": message,
            "notification_type": notification_type,
            "additional_data": additional_data
        }
    
    def _handle_resolution_phase(self, additional_data):
        """해결 단계 처리"""
        self.phase = self.PHASE_RESOLUTION
        message = '라운드 {} 선언이 끝났습니다. 계산을 시작합니다.'.format(self.current_round)
        notification_type = 'resolution_phase'
        
        # 타이머 정지
        if self.game.timer.get('is_running'):
            self.game.timer['is_running'] = False
            self.game.timer['elapsed_before_pause'] = time.time() - self.game.timer['start_time']
        
        return {
            "success": True,
            "phase": self.phase,
            "round": self.current_round,
            "message": message,
            "notification_type": notification_type,
            "additional_data": additional_data
        }
    
    def _handle_wrap_up_phase(self, additional_data):
        """전투 종료 단계 처리"""
        self.phase = self.PHASE_WRAP_UP
        self.in_combat = False
        message = '전투가 종료되었습니다.'
        notification_type = 'combat_ended'
        
        return {
            "success": True,
            "phase": self.phase,
            "round": self.current_round,
            "message": message,
            "notification_type": notification_type,
            "additional_data": additional_data
        }
    
    def get_combat_start_message(self):
        """전투 시작 메시지 반환"""
        return {
            "success": True,
            "phase": self.phase,
            "round": self.current_round,
            "message": '전투를 시작합니다.',
            "notification_type": "combat_starting"
        }
    
    def start_combat(self):
        """전투 시작 - combat_state를 초기화하고 preparation 단계로 설정"""
        self.in_combat = True
        self.phase = self.PHASE_PREPARATION
        return f"전투 {self.game.id}를 시작합니다."
    
    def end_combat(self):
        """전투 종료 - combat_state를 종료 상태로 설정"""
        self.in_combat = False
        self.phase = 'end'
    
    def start_position_declaration_phase(self):
        """위치 선언 단계 시작 (전투 시작 후 호출)"""
        return self.advance_combat_phase(self.PHASE_POSITION_DECLARATION)
    
    def start_action_declaration_phase(self):
        """행동 선언 단계 시작 (위치 선언 완료 후 호출)"""
        return self.advance_combat_phase(self.PHASE_ACTION_DECLARATION)
    
    def start_resolution_phase(self):
        """해결 단계 시작 (행동 선언 완료 후 호출)"""
        return self.advance_combat_phase(self.PHASE_RESOLUTION)
    
    def get_round_summary_message(self):
        """라운드 요약 메시지 반환 (phase는 변경하지 않음)"""
        return {
            "success": True,
            "phase": self.phase,
            "round": self.current_round,
            "message": '라운드 {} 결과를 요약합니다.'.format(self.current_round),
            "notification_type": "round_summary"
        }
    
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
    
    def end_round(self):
        """
        라운드 종료 처리 및 다음 단계로 전환
        
        Returns:
            dict: {
                "success": bool,
                "phase": str,
                "round": int,
                "message": str,
                "notification_type": str,
                "next_phase": dict or None
            }
        """
        summary_result = self.get_round_summary_message()
        is_team_defeated, defeated_team = self.check_all_players_defeated()
        
        if is_team_defeated:
            wrap_up_result = self.advance_combat_phase(self.PHASE_WRAP_UP)
            return {
                **summary_result,
                "next_phase": wrap_up_result
            }
        else:
            self.current_round += 1
            action_decl_result = self.start_action_declaration_phase()
            return {
                **summary_result,
                "next_phase": action_decl_result
            }

class PosManager():
    """
    Coordinate & Position Helpers:
    -------------------------------
    [TODO] pos_to_rc() - Convert position string ("Y1") to (row_idx, col_idx)
    [TODO] rc_to_pos() - Convert (row_idx, col_idx) to position string ("Y1")
    [TODO] is_front_row() - Check if position is front row (X or A)
    [TODO] is_back_row() - Check if position is back row (Y or B)
    [TODO] check_move_validity() - Validate move destination (distance, team, occupancy)
    """
    pass
    def __init__(self, game):
        self.game = game


class Game():
    """
    METHOD INDEX:
    =============
    Combat Calculations:
    ---------------------
    [TODO] calculate_priority() - Calculate action priority (sen*10+mst, per*10+mst, etc.)
    [TODO] calculate_attack_power() - Calculate attack power based on stats
    [TODO] calculate_max_hp() - Calculate max HP (vtl*5+10)
    [TODO] initialize_character_hp() - Initialize character HP
    [TODO] calculate_all_priorities() - Calculate priorities for all actions
    
    Combat Validation:
    ------------------
    [TODO] check_range() - Check if attack is within valid range
    [TODO] check_covering() - Check covering for ranged attacks
    [TODO] get_valid_attack_tiles() - Get list of valid attack target tiles
    [TODO] get_valid_move_tiles() - Get list of valid move destination tiles
    [TODO] get_tile_feedback() - Get tile feedback info (attack/move valid tiles)
    
    Action Resolution:
    ------------------
    [TODO] declare_action() - Handle action declaration from player
    [TODO] resolve_action() - Resolve and execute a single action
    [TODO] resolve_all_actions() - Resolve all actions in action_queue
    
    Utility & Data Export:
    ----------------------
    ✓ vomit() - Export game state as dict
    ✓ move_player() - Legacy move command handler (chat command)
    """
    
    def __init__(self, id, player_num = 4):
        self.id = id
        self.player_num = player_num #default 4, max 8
        
        self.SlotM = SlotManager(self)
        
        self.players = [
            self.SlotM.player_factory()
            for _ in range(self.player_num)
        ]  # player list (slots)

        self.connection_lost_timers = {}  # {slot: timestamp} for tracking connection-lost duration
        self.users = [] #접속자 목록
        # Initialize game board as 4x4 grid (4 rows, 4 columns)
        # Row 0: Y1, Y2, Y3, Y4
        # Row 1: X1, X2, X3, X4
        # Row 2: A1, A2, A3, A4
        # Row 3: B1, B2, B3, B4
        self.game_board = [['cell' for _ in range(4)] for _ in range(4)]

        # 타이머 초기화
        self.timer = {
            'type': None,
            'start_time': None,
            'duration': None,
            'is_running': False,
            'paused_at': None,
            'elapsed_before_pause': 0
        }

        self.phaseM = PhaseManager(self)
        self.posM = PosManager(self)

    # ============================================
    # SECTION 2: Combat State Management
    # ============================================
    # Note: start_combat() and end_combat() are now in PhaseManager
    # Use: self.phaseM.start_combat() and self.phaseM.end_combat()
    
    # ============================================
    # SECTION 3: Combat Calculations
    # ============================================
    # TODO: calculate_priority()
    # TODO: calculate_attack_power()
    # TODO: calculate_max_hp()
    # TODO: initialize_character_hp()
    
    # ============================================
    # SECTION 4: Coordinate & Position Helpers
    # ============================================
    # TODO: pos_to_rc() - Convert position string to (row_idx, col_idx)
    # TODO: rc_to_pos() - Convert (row_idx, col_idx) to position string
    # TODO: is_front_row() - Check if position is front row
    # TODO: is_back_row() - Check if position is back row
    # TODO: check_move_validity() - Validate move destination
    
    # ============================================
    # SECTION 5: Combat Validation
    # ============================================
    # TODO: check_range() - Check attack range validity
    # TODO: check_covering() - Check covering for ranged attacks
    # TODO: get_valid_attack_tiles() - Get valid attack targets
    # TODO: get_valid_move_tiles() - Get valid move destinations
    # TODO: get_tile_feedback() - Get tile feedback info
    
    # ============================================
    # SECTION 6: Action Resolution
    # ============================================
    # TODO: resolve_action() - Resolve and execute action
    # TODO: start_action_declaration_phase() - Start action declaration
    # TODO: declare_action() - Handle action declaration
    # TODO: check_all_declarations_complete() - Check if all declared
    # TODO: calculate_all_priorities() - Calculate all action priorities
    # TODO: end_round() - End round and check win conditions
    
    # ============================================
    # SECTION 7: Utility & Data Export
    # ============================================
    
    def vomit(self):
        data = {
            "type": "vomit_data",
            "id": self.id, # game id
            "players": self.players,  # player list (slots)
            "game_board": self.game_board
        }
        return data

    def move_player(self, name, command):
        """
        Legacy move command handler (chat command).
        TODO: Replace with proper combat movement system.
        """
        # Row 0: Y1, Y2, Y3, Y4
        # Row 1: X1, X2, X3, X4
        # Row 2: A1, A2, A3, A4
        # Row 3: B1, B2, B3, B4
        # Find the character object in self.characters that matches the sender's name
        character_obj = next((c for c in self.players if c['name'] == name), None)
        current_pos = character_obj['pos'] if character_obj and 'pos' in character_obj else None

        match = re.search(r'\b([YXAB][1-4])\b', command)
        target_pos = match.group(1) if match else None
        if target_pos:
            character_obj["pos"] = target_pos
            return f"{name} moved from {current_pos} to {target_pos}"
        else:
            return f"{name} move failed."