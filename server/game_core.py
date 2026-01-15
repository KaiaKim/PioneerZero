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
    def __init__(self, game):
        self.game = game

        self.ROW_MAP = {"Y": 0, "X": 1, "A": 2, "B": 3}
        self.REV_ROW_MAP = {v: k for k, v in self.ROW_MAP.items()}

    def declare_position(self, sender, command):
        result = None
        err = None

        position = command[1].strip().upper()
        player = self.game.players[sender]

        if command[1][0] in self.ROW_MAP:
            err = "유효하지 않은 열 번호입니다."
        
        if int(command[1][1]) not in (1, 2, 3, 4):
            err = "유효하지 않은 행 번호입니다."

        # Validate position using parse_position_declaration_from_chat logic
        player_team = player.get('team', 0)
        r, c = self.pos_to_rc(position)
        
        if r < 0 or c < 0 or c > 3:
            err = "유효하지 않은 위치입니다."
        
        # Check if position is in player's team area
        # Row 0-1 (Y, X) = team 1 (blue), Row 2-3 (A, B) = team 0 (white)
        position_team = 1 if r <= 1 else 0
        if position_team != player_team:
            err = "자신의 진영만 선택할 수 있습니다."
        
        result = f"위치 {position} 선언 완료"

        return result, err

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


    def pos_to_rc(self, pos: str) -> tuple[int, int]:
        r = self.ROW_MAP.get(pos[0], -1)
        c = int(pos[1]) - 1
        return r, c

    def rc_to_pos(self, r: int, c: int) -> str:
        return f"{self.REV_ROW_MAP.get(r, '?')}{c + 1}"

    def is_front_row(self, pos: str) -> bool:
        r, _ = self.pos_to_rc(pos)
        return r == 1 or r == 2

    def is_back_row(self, pos: str) -> bool:
        r, _ = self.pos_to_rc(pos)
        return r == 0 or r == 3

    def check_move_validity(self, from_pos: str, to_pos: str, player_team: int) -> tuple[bool, str]:
        fr, fc = self.pos_to_rc(from_pos)
        tr, tc = self.pos_to_rc(to_pos)
        
        row_dist = abs(fr - tr)
        col_dist = abs(fc - tc)
        
        if row_dist > 1 or col_dist > 1:
            return False, "이동 거리 초과"
        if row_dist == 0 and col_dist == 0:
            return False, "같은 위치"
        
        to_team = 1 if tr <= 1 else 0
        if to_team != player_team:
            return False, "다른 팀 셀"
        
        if self.game.combat_board.get(to_pos) is not None:
            return False, "이미 차지됨"
        
        return True, None

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
        self.posM = PosManager(self)
        
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

        self.in_combat = False
        self.current_round = 0
        self.phase = 'preparation'  # 'preparation', 'kickoff', 'position_declaration', 'action_declaration', 'resolution', 'wrap-up'
        self.action_queue = []
        self.resolved_actions = []

    # ============================================
    # SECTION 3: Combat Calculations
    # ============================================
    # TODO: calculate_priority()
    # TODO: calculate_attack_power()
    # TODO: calculate_max_hp()
    # TODO: initialize_character_hp()
    
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
        
        for player in self.players:
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