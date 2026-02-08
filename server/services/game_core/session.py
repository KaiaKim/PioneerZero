import base64
import pickle
from dataclasses import asdict
from ...util.models import ActionContext, CommandContext, PlayerSlot
from . import join, position

class Game():
    def __init__(self, id, player_num = 4):
        self.id = id
        self.player_num = player_num #default 4, max 8
        
        self.players = [
            PlayerSlot(index=i)
            for i in range(self.player_num)
        ]  # player list (slots)

        self.connection_lost_timers = {}  # {slot_idx: timestamp} for tracking connection-lost duration
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

        
    def _upsert_action_queue(self, action: ActionContext) -> None:
        self.action_queue = [a for a in self.action_queue if a.slot_idx != action.slot_idx]
        self.action_queue.append(action)

    def get_action_submission_status(self):
        submitted = {action.slot_idx for action in self.action_queue}
        return [{"slot_idx": i, "submitted": i in submitted} for i in range(self.player_num)]

    def get_player_by_user_id(self, user_id: str) -> int | None:
        """Return slot_idx (0-based) for the given user_id, or None if not found."""
        for player in self.players:
            if player.info and player.info.get('id') == user_id:
                return player.index
        return None

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
    # TODO: declare_action() - Handle action declaration
    # TODO: check_all_declarations_complete() - Check if all declared
    # TODO: calculate_all_priorities() - Calculate all action priorities
    def declare_position(self, ctx: CommandContext) -> ActionContext:
        slot_idx = getattr(ctx, 'slot_idx', None) or self.get_player_by_user_id(ctx.user_id)
        if slot_idx is None:
            raise ValueError("Could not determine slot_idx for declare_position")
        pos_data = ActionContext(slot_idx=slot_idx, action_type="position")
        self._upsert_action_queue(pos_data)
        return pos_data

    def declare_attack(self, ctx: CommandContext) -> ActionContext:
        slot_idx = getattr(ctx, 'slot_idx', None) or self.get_player_by_user_id(ctx.user_id)
        if slot_idx is None:
            raise ValueError("Could not determine slot_idx for declare_attack")
        action_data = ActionContext(slot_idx=slot_idx, action_type=ctx.action_type, target=ctx.target)
        self._upsert_action_queue(action_data)
        return action_data
    
    def declare_skill(self):
        pass

    # ============================================
    # SECTION 7: Utility & Data Export
    # ============================================

    def serialize(self) -> str:
        """Serialize game state to base64-encoded pickle (for DB storage)."""
        return base64.b64encode(pickle.dumps(self)).decode()

    @classmethod
    def deserialize(cls, blob: str):
        """Deserialize game from base64-encoded pickle."""
        return pickle.loads(base64.b64decode(blob))
    
    def vomit(self):
        data = {
            "type": "vomit_data",
            "id": self.id,
            "players": [asdict(p) for p in self.players],
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
            if player.occupy != 1:
                continue
            if not player.character:
                continue
            team = player.team
            current_hp = player.character.current_hp
            
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
