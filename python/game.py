"""
Game Logic - Game session management and initialization
"""
    #create a newGame object.
    #object contains: player character, ally characters, enemy characters, game board, turn order, etc.
    #each character has a name, profile image, token image, stats, type, skills, current hp.

from .temp_char import player, ally_A, enemy_A, enemy_B
import re

class Game():
    def __init__(self, session_id):
        self.session_id = session_id
        self.characters = [player, ally_A, enemy_A, enemy_B]
        # Initialize game board as 4x4 grid (4 rows, 4 columns)
        # Row 0: Y1, Y2, Y3, Y4
        # Row 1: X1, X2, X3, X4
        # Row 2: A1, A2, A3, A4
        # Row 3: B1, B2, B3, B4
        self.game_board = [[{"occupy": None} for _ in range(4)] for _ in range(4)]
        self.current_round = 0

    def vomit(self):
        data = {
            "type": "vomit_data",
            "session_id": self.session_id,
            "names": [char["name"] for char in self.characters],
            "characters": self.characters,
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
        character_obj = next((c for c in self.characters if c['name'] == name), None)
        current_pos = character_obj['pos'] if character_obj and 'pos' in character_obj else None

        match = re.search(r'\b([YXAB][1-4])\b', command)
        target_pos = match.group(1) if match else None
        if target_pos:
            character_obj["pos"] = target_pos
            return f"{name} moved from {current_pos} to {target_pos}"
        else:
            return f"{name} move failed."

