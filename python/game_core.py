"""
Game Logic - Game session management and initialization
"""
    #create a newGame object.
    #object contains: player character, ally characters, enemy characters, game board, turn order, etc.
    #each character has a name, profile image, token image, stats, type, skills, current hp.

from .temp_character import player, ally_A, enemy_A, enemy_B
import re

class Game():
    def __init__(self, id):
        self.id = id
        self.players = [None, None, None, None]  # 플레이어 캐릭터 목록 (4 slots: 0-3 for slots 1-4)
        self.users = [] #접속자 목록
        # Initialize game board as 4x4 grid (4 rows, 4 columns)
        # Row 0: Y1, Y2, Y3, Y4
        # Row 1: X1, X2, X3, X4
        # Row 2: A1, A2, A3, A4
        # Row 3: B1, B2, B3, B4
        self.game_board = [[{"occupy": None} for _ in range(4)] for _ in range(4)]
        self.current_round = 0

    def add_player_to_slot(self, slot_num: int, user_info: dict):
        """Add a player to a specific slot (1-4)"""
        if slot_num < 1 or slot_num > 4:
            return {"success": False, "message": "Invalid slot number. Must be 1-4."}
        slot_index = slot_num - 1
        if self.players[slot_index] is not None:
            return {"success": False, "message": f"Slot {slot_num} is already occupied."}
        
        # Create player object with user_info and slot number
        player_obj = {
            **user_info,
            "slot": slot_num
        }
        self.players[slot_index] = player_obj
        return {"success": True, "message": f"Player added to slot {slot_num}."}
    
    def remove_player_from_slot(self, slot_num: int):
        """Remove a player from a specific slot (1-4)"""
        if slot_num < 1 or slot_num > 4:
            return {"success": False, "message": "Invalid slot number. Must be 1-4."}
        slot_index = slot_num - 1
        if self.players[slot_index] is None:
            return {"success": False, "message": f"Slot {slot_num} is already empty."}
        
        self.players[slot_index] = None
        return {"success": True, "message": f"Player removed from slot {slot_num}."}
    
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

