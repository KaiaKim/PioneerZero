"""
Game Logic - Game session management and initialization
"""
    #create a newGame object.
    #object contains: player character, ally characters, enemy characters, game board, turn order, etc.
    #each character has a name, profile image, token image, stats, type, skills, current hp.

from .temp_character import player, ally_A, enemy_A, enemy_B
import re
import time

class Game():
    def __init__(self, id, player_num = 4):
        self.id = id
        self.player_num = player_num #default 4, max 8
        self.p_init = {
                'info': None,
                'character': None,
                'slot': 0,
                'team': 0, # 0=white,1=blue
                'occupy': 0,  # 0=empty, 1=occupied, 2=connection-lost
                'pos': None # position on the game board
            }
        self.players = [
            self.p_init
            for _ in range(self.player_num)
        ]  # player list (slots)

        self.connection_lost_timers = {}  # {slot_num: timestamp} for tracking connection-lost duration
        self.users = [] #접속자 목록
        # Initialize game board as 4x4 grid (4 rows, 4 columns)
        # Row 0: Y1, Y2, Y3, Y4
        # Row 1: X1, X2, X3, X4
        # Row 2: A1, A2, A3, A4
        # Row 3: B1, B2, B3, B4
        self.game_board = [['cell' for _ in range(4)] for _ in range(4)]
        self.current_round = 0

    def add_player_to_slot(self, slot_num: int, slot_index: int, user_info: dict):
        """Add a player to a specific slot"""
        existing_player_info = self.players[slot_index]['info']
        occupy = self.players[slot_index]['occupy']
        
        # Check if it's the same user trying to rejoin
        is_same_user = existing_player_info and existing_player_info.get('id') == user_info.get('id')
        
        # Check if slot is occupied (status 1)
        if occupy == 1:
            if is_same_user:
                # Same user rejoining - already occupied by them, no change needed
                return {"success": True, "message": f"Player already in slot {slot_num}."}
            return {"success": False, "message": f"Slot {slot_num} is already occupied."}
        
        # Check if slot is connection-lost (status 2)
        if occupy == 2:
            if is_same_user:
                # Same user rejoining - update status to occupied
                self.players[slot_index]['occupy'] = 1
                self.connection_lost_timers.pop(slot_num, None)
                return {"success": True, "message": f"Player rejoined slot {slot_num}."}
            return {"success": False, "message": f"Slot {slot_num} is connection-lost. Please wait."}
        
        # Slot is empty (status 0) - add player
        # Create player object with user_info and slot number
        player_obj = {
            'info': user_info,
            'character': None,
            "slot": slot_num,
            'team': slot_num % 2, # 0=white,1=blue
            'occupy': 1  # 0=empty, 1=occupied, 2=connection-lost
        }
        self.players[slot_index] = player_obj
        self.connection_lost_timers.pop(slot_num, None)  # Clear any connection-lost timer
        return {"success": True, "message": f"Player added to slot {slot_num}."}
    
    def remove_player_from_slot(self, slot_num: int, slot_index: int):
        """Remove a player from a specific slot - sets status to empty"""
        if self.players[slot_index]['occupy'] == 0:
            return {"success": False, "message": f"Slot {slot_num} is already empty."}
        
        self.players[slot_index] = self.p_init
        self.connection_lost_timers.pop(slot_num, None)  # Clear any connection-lost timer
        return {"success": True, "message": f"Player removed from slot {slot_num}."}
    
    def set_player_connection_lost(self, slot_num: int):
        """Set a player slot to connection-lost status (2)"""
        slot_index = slot_num - 1
        if self.players[slot_index]['occupy'] == 0:
            return {"success": False, "message": f"Slot {slot_num} is already empty."}
        
        self.players[slot_index]['occupy'] = 2  # Set status to connection-lost
        self.connection_lost_timers[slot_num] = time.time()  # Record timestamp
        return {"success": True, "message": f"Player slot {slot_num} set to connection-lost."}
    
    def check_connection_lost_timeouts(self, duration = 5.0):
        """Check for connection-lost slots that have exceeded 5 seconds and clear them"""
        current_time = time.time()
        slots_to_clear = []
        
        for slot_num, timestamp in self.connection_lost_timers.items():
            if current_time - timestamp >= duration:  # default 5 seconds timeout
                slot_index = slot_num - 1
                if self.players[slot_index]['occupy'] == 2:  # Still connection-lost
                    self.players[slot_index] = self.p_init
                    self.players[slot_index]['occupy'] = 0  # Set to empty
                    slots_to_clear.append(slot_num)
        
        # Remove cleared slots from timers
        for slot_num in slots_to_clear:
            self.connection_lost_timers.pop(slot_num, None)
        
        return len(slots_to_clear) > 0  # Return True if any slots were cleared
    
    def get_player_by_user_id(self, user_id: str):
        """Get the slot number for a user_id, or None if not found"""
        for i, player in enumerate(self.players):
            if player and player.get('id') == user_id:
                return i + 1  # Return slot number (1-4)
        return None
    
    def add_player_character(self, player):
        # Legacy method - kept for compatibility
        self.players.append(player)
        return f"Player character added."

    def remove_player_character(self, player):
        # Legacy method - kept for compatibility
        if player in self.players:
            self.players.remove(player)
            return f"Player character removed."
    
    def vomit(self):
        # Filter out None values for legacy compatibility
        active_players = [p for p in self.players if p is not None]
        data = {
            "type": "vomit_data",
            "id": self.id,
            "names": [char["name"] for char in active_players if char.get("name")],
            "characters": active_players,
            "players": self.players,  # Include full slots array (with None values)
            "player_status": self.player_status,  # Include status array
            "game_board": self.game_board,
            "current_round": self.current_round
        }
        return data

    def move_player(self, name, command):
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

