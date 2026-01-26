import json
from . import slot, position

class Game():
    def __init__(self, id, player_num = 4):
        self.id = id
        self.player_num = player_num #default 4, max 8
        
        self.players = [
            slot.player_factory()
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

        self.phase_task = None

        self.offset_sec = 3
        self.phase_sec = 10
        self.max_rounds = 100

        self.in_combat = False
        self.current_round = 0
        self.phase = 'preparation'  # 'preparation', 'kickoff', 'position_declaration', 'action_declaration', 'resolution', 'wrap-up'
        self.action_queue = []
        self.resolved_actions = []

        
    def _build_action_data(self, slot, action_type, skill_chain=None, target="자신"):
        return {
            "slot": slot,
            "action_type": action_type,
            "skill_chain": skill_chain,
            "target": target,
            "target_slot": None,
            "priority": None,
            "attack_power": None,
            "resolved": False
        }

    def _upsert_action_queue(self, action_data):
        slot = action_data.get("slot")
        if slot is None:
            return
        self.action_queue = [
            action for action in self.action_queue if action.get("slot") != slot
        ]
        self.action_queue.append(action_data)

    def get_action_submission_status(self):
        submitted_slots = {action.get("slot") for action in self.action_queue}
        status_list = []
        for idx in range(self.player_num):
            slot = idx + 1
            status_list.append({
                "slot": slot,
                "submitted": slot in submitted_slots
            })
        return status_list


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

    def declare_attack(self, sender, action_type, target="자신"):
        """
        Declare an attack action for a player.
        
        Args:
            sender: User ID of the player declaring the attack
            action_type: Type of attack ("근거리공격", "원거리공격", "대기")
            target: Target of the attack (default: "자신")
        
        Returns:
            tuple: (action_data, err) where action_data is the action dictionary and err is an error message if any
        """
        err = None
        
        slot_num = slot.get_player_by_user_id(self, sender)
        if not slot_num:
            return None, "플레이어 슬롯을 찾을 수 없습니다."

        action_data = self._build_action_data(slot_num, action_type, target=target)
        self._upsert_action_queue(action_data)

        # action_data is expected to be a dictionary containing the declared action's details,
        # such as the player's slot, action type, target, and other action-specific data.
        # For example:
        # {
        #   "slot": <player_slot_number>,
        #   "type": "근거리공격" | "원거리공격" | "대기",
        #   "target": <target_id_or_name>,
        #   ... (other fields as needed)
        # }
        return action_data, err
    
    def declare_skill(self, sender, command):
        result = None
        err = None

        result = "행동 선언 완료"
        return result, err
    # ============================================
    # SECTION 7: Utility & Data Export
    # ============================================

    def dict_to_json(self):
        """Serialize the initial combat snapshot to JSON."""
        def serialize_player(player, slot_num):
            if not player:
                return None
            return {
                "info": player.get("info"),
                "character": player.get("character"),
                "slot": player.get("slot", slot_num),
                "team": player.get("team", slot_num % 2),
                "occupy": player.get("occupy", 0),
                "pos": player.get("pos")
            }

        payload = {
            "id": self.id,
            "player_num": self.player_num,
            "players": [
                serialize_player(player, idx + 1) for idx, player in enumerate(self.players)
            ],
            "game_board": self.game_board,
            "current_round": self.current_round,
            "connection_lost_timers": self.connection_lost_timers
        }
        return json.dumps(payload)

    @classmethod
    def json_to_dict(cls, json_blob):
        """Deserialize initial combat snapshot JSON into a Game instance."""
        data = json.loads(json_blob) if isinstance(json_blob, str) else json_blob
        game_id = data.get("id")
        player_num = data.get("player_num", 4)
        game = cls(game_id, player_num)

        players_data = data.get("players", [])
        players = []
        for idx in range(player_num):
            slot_num = idx + 1
            base_player = slot.player_factory(slot_num)
            if idx < len(players_data) and players_data[idx]:
                stored = players_data[idx]
                base_player["info"] = stored.get("info")
                base_player["character"] = stored.get("character")
                base_player["slot"] = stored.get("slot", slot_num)
                base_player["team"] = stored.get("team", slot_num % 2)
                base_player["occupy"] = stored.get("occupy", 0)
                base_player["pos"] = stored.get("pos")

                info = base_player.get("info") or {}
                is_bot = info.get("is_bot") or (
                    info.get("id") and str(info.get("id")).startswith("bot_")
                )
                base_player["ready"] = True if is_bot else False
            players.append(base_player)

        game.players = players
        game.game_board = data.get("game_board", game.game_board)
        game.current_round = data.get("current_round", 0)
        game.connection_lost_timers = data.get("connection_lost_timers", {})
        return game
    
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
