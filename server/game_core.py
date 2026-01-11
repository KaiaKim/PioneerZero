from . import game_bot
import re
import time

class SlotManager():
    """
    Player Slot Management:
    -----------------------
    ✓ player_factory() - Create new player slot dict
    ✓ add_player_to_slot() - Add human player to slot
    ✓ add_bot_to_slot() - Add bot player to slot
    ✓ remove_player_from_slot() - Remove player from slot
    ✓ set_player_connection_lost() - Mark player as connection-lost
    ✓ clear_expired_connection_lost_slots() - Cleanup expired connection-lost slots
    ✓ get_player_by_user_id() - Find player slot by user ID
    ✓ set_player_ready() - Set player ready state
    ✓ are_all_players_ready() - Check if all players are ready
    """
    pass

class PhaseManager():
    """
    Combat State Management:
    ------------------------
    ✓ start_combat() - Start combat session
    ✓ end_combat() - End combat session
    [TODO] parse_position_declaration_from_chat() - Parse and validate position declaration from chat
    [TODO] resolve_position_declarations() - Resolve position declarations and handle butting
    [TODO] get_adjacent_empty_positions() - Get adjacent empty positions for butted players
    [TODO] get_empty_team_positions() - Get all empty team positions
    [TODO] check_all_positions_declared() - Check if all positions are declared (parsing from chat)
    [TODO] start_action_declaration_phase() - Start action declaration phase with timer
    [TODO] handle_timeout() - Handle action declaration timeout
    [TODO] check_all_declarations_complete() - Check if all actions declared
    [TODO] end_round() - End round and check win conditions
    """
    pass

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
        self.players = [
            self.player_factory()
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

        # 전투 상태
        self.combat_state = {
            'in_combat': False,
            'current_round': 0,
            'phase': 'preparation',  # 'preparation', 'position_declaration', 'action_declaration', 'resolution', 'end'
            'action_queue': [],
            'resolved_actions': []
        }

        self.phase_system_strings = [
            '전투를 시작합니다.', 
            '위치 선언 페이즈입니다. 시작 위치를 선언해주세요.', 
            '라운드 n 선언 페이즈입니다. 스킬과 행동을 선언해주세요.', 
            '라운드 n 선언이 끝났습니다. 계산을 시작합니다.', 
            '라운드 n 결과를 요약합니다.',
            '전투가 종료되었습니다.'
            ]

        self.SlotM = SlotManager(self)
        self.phaseM = PhaseManager(self)
        self.posM = PosManager(self)

    # ============================================
    # SECTION 1: Player Slot Management
    # ============================================
    
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

    def add_player_to_slot(self, slot: int, slot_idx: int, user_info: dict):
        """Add a player to a specific slot"""
        existing_player_info = self.players[slot_idx]['info']
        occupy = self.players[slot_idx]['occupy']
        
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
                self.players[slot_idx]['occupy'] = 1
                self.connection_lost_timers.pop(slot, None)
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
        self.players[slot_idx] = player_obj
        self.connection_lost_timers.pop(slot, None)  # Clear any connection-lost timer
        return {"success": True, "message": f"Player added to slot {slot}."}
    
    def add_bot_to_slot(self, slot: int, slot_idx: int):
        """Add a bot to a specific slot"""
        occupy = self.players[slot_idx]['occupy']
        
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
        self.players[slot_idx] = player_obj
        self.connection_lost_timers.pop(slot, None)  # Clear any connection-lost timer
        return {"success": True, "message": f"Bot added to slot {slot}."}
    
    def remove_player_from_slot(self, slot: int, slot_idx: int):
        """Remove a player from a specific slot - sets status to empty"""
        if self.players[slot_idx]['occupy'] == 0:
            return {"success": False, "message": f"Slot {slot} is already empty."}
        
        self.players[slot_idx] = self.player_factory(slot)
        self.connection_lost_timers.pop(slot, None)  # Clear any connection-lost timer
        return {"success": True, "message": f"Player removed from slot {slot}."}
    
    def set_player_connection_lost(self, slot: int):
        """Set a player slot to connection-lost status (2) and set ready to False"""
        slot_idx = slot - 1
        if self.players[slot_idx]['occupy'] == 0:
            return {"success": False, "message": f"Slot {slot} is already empty."}
        
        self.players[slot_idx]['occupy'] = 2  # Set status to connection-lost
        self.players[slot_idx]['ready'] = False  # Set ready to False when connection is lost
        self.connection_lost_timers[slot] = time.time()  # Record timestamp
        return {"success": True, "message": f"Player slot {slot} set to connection-lost."}
    
    def clear_expired_connection_lost_slots(self, duration = 5.0):
        """
        Clear connection-lost slots that have exceeded the timeout duration.
        
        Behavior:
        - Combat NOT started: Clear slots after duration (default 5 seconds)
        - Combat started: Never clear slots (wait infinitely for player to rejoin)
        """
        # If combat has started, don't clear any connection-lost slots
        if self.combat_state['in_combat']:
            return False
        
        # Combat not started - clear expired slots after timeout
        current_time = time.time()
        slots_to_clear = []
        
        for slot, timestamp in self.connection_lost_timers.items():
            if current_time - timestamp >= duration:  # default 5 seconds timeout
                slot_idx = slot - 1
                if self.players[slot_idx]['occupy'] == 2:  # Still connection-lost
                    self.players[slot_idx] = self.player_factory(slot)
                    slots_to_clear.append(slot)
        
        # Remove cleared slots from timers
        for slot in slots_to_clear:
            self.connection_lost_timers.pop(slot, None)
        
        return len(slots_to_clear) > 0  # Return True if any slots were cleared
    
    def get_player_by_user_id(self, user_id: str):
        """Get the slot number for a user_id, or None if not found"""
        for i, player in enumerate(self.players):
            if player.get('info') and player['info'].get('id') == user_id:
                return i + 1  # Return slot number (1-based)
        return None
    
    def set_player_ready(self, slot: int, slot_idx: int, user_info: dict, ready: bool):
        """Set ready state for a player. Only the player themselves can toggle their ready state."""
        # Verify the slot belongs to the user
        player = self.players[slot_idx]
        if not player.get('info') or player['info'].get('id') != user_info.get('id'):
            return {"success": False, "message": "You don't own this slot."}
        
        # Check if slot is occupied or connection-lost (can set ready in both states)
        if player['occupy'] not in [1, 2]:
            return {"success": False, "message": f"Slot {slot} is not occupied."}
        
        # Check if it's a bot (bots are always ready, can't be changed)
        if player['info'].get('is_bot') == True or (player['info'].get('id') and player['info'].get('id').startswith('bot_')):
            return {"success": False, "message": "Bots are always ready."}
        
        # Set ready state
        self.players[slot_idx]['ready'] = ready
        return {"success": True, "message": f"Ready state set to {ready}."}
    
    def are_all_players_ready(self):
        """
        Check if all slots are filled AND all players are ready.
        - All slots must have characters (occupy == 1 and character is not None)
        - All players must be ready (ready == True)
        - Bots are always considered ready
        """
        for player in self.players:
            # Check if slot is filled with a character
            if player['occupy'] != 1 or player['character'] is None:
                return False
            
            # Check if player is ready (bots are always ready by design, so we only check non-bots)
            is_bot = player.get('info') and (player['info'].get('is_bot') == True or 
                                            (player['info'].get('id') and player['info'].get('id').startswith('bot_')))
            
            if not is_bot and not player.get('ready', False):
                return False
        
        return True
    
    # ============================================
    # SECTION 2: Combat State Management
    # ============================================
    
    def start_combat(self):
        self.combat_state['in_combat'] = True
        self.combat_state['phase'] = 'preparation'
        return f"전투 {self.id}를 시작합니다."
    
    def end_combat(self):
        self.combat_state['in_combat'] = False
        self.combat_state['phase'] = 'end'
    
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