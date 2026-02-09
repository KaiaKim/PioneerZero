import base64
import pickle
import random
from dataclasses import asdict
from ...util.models import ActionContext, CommandContext, PlayerSlot
from . import join, position

class Game():
    def __init__(self, id, player_num = 4):
        self.id = id
        self.player_num = player_num #default 4, max 8
        
        self.player_slots = [
            PlayerSlot(index=i)
            for i in range(self.player_num)
        ]  # player list (slots)
        self.players = self.player_slots  # alias for join, flow, etc.

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


    def auto_fill_action(self):
        """Ensure all combat participants have an action and fill empty destinations."""
        for p in self.player_slots:
            if not p.action:
                p.action = ActionContext(slot_idx=p.index, destination="")
            action = p.action
            if not action.destination:
                team = p.team
                if self.phase == "position_declaration":
                    cells = position.get_same_team_cells(team)
                    action.destination = random.choice(cells)
                elif self.phase == "action_declaration" and p.pos:
                    action.destination = p.pos

    def resolve_actions(self):
        # Collect all actions (caller must run auto_fill_action first)
        actions = [p.action for p in self.player_slots if p.action]
        result = []
        # Sort by priority (or shuffle if all 0)
        if actions and sum(a.priority for a in actions) == 0:
            random.shuffle(actions)
        else:
            actions.sort(key=lambda a: a.priority, reverse=True)

        # Destination resolution loop (butting)
        claimed_cells = {}  # cell -> slot_idx (who claimed it)
        for action in actions:
            slot_idx = action.slot_idx
            player = self.player_slots[slot_idx]
            team = player.team
            name = player.character.name

            if action.destination not in claimed_cells:
                final_dest = action.destination
                result.append(f"{name}은 {final_dest}로 이동합니다.")
            else:
                # Butting: pick adjacent same-team empty, or any same-team empty
                winner_slot = claimed_cells[action.destination]
                winner_name = self.player_slots[winner_slot].character.name
                same_team = set(position.get_same_team_cells(team))
                adjacent = [
                    c for c in position.get_adjacent_cells(action.destination)
                    if c in same_team and c not in claimed_cells
                ]
                empty_same_team = position.get_empty_same_team_cells(team, set(claimed_cells))
                if adjacent:
                    final_dest = random.choice(adjacent)
                else:
                    final_dest = random.choice(empty_same_team)
                result.append(
                    f"{winner_name}와 {name}의 {action.destination} 위치 중복. "
                    f"{name}는 {final_dest}로 밀려납니다."
                )

            claimed_cells[final_dest] = slot_idx
            player.pos = final_dest
            action.destination_resolved = True

        return result


    def declare_position(self, ctx: CommandContext) -> ActionContext:
        if not self.in_combat:
            return "위치 명령어는 전투 중에만 사용할 수 있습니다."
        if self.phase != "position_declaration":
            return "위치 명령어는 위치선언 단계에만 사용할 수 있습니다."
        slot_idx = self.get_player_by_user_id(ctx.user_id)
        if slot_idx is None: #meaning user is not in player_slots
            return "위치 명령어는 전투 참여자만 사용할 수 있습니다."
        cell = ctx.args[0].strip().upper()
        ROW_MAP = {"Y": 0, "X": 1, "A": 2, "B": 3}
        if cell[0] not in ROW_MAP:
            return "유효하지 않은 열 번호입니다."
        if int(cell[1]) not in (1, 2, 3, 4):
            return "유효하지 않은 행 번호입니다."

        # Row 0-1 (Y, X) = team 1 (blue), Row 2-3 (A, B) = team 0 (white)
        called_team = 1 if cell[0] in ["Y", "X"] else 0
        my_team = self.player_slots[slot_idx].team
        if called_team != my_team:
            return "자신의 진영만 선택할 수 있습니다."

        self.player_slots[slot_idx].action = ActionContext(
            slot_idx=slot_idx,
            destination=cell
            )

        return None

    def declare_attack(self, ctx: CommandContext) -> ActionContext:
        pass
    #finish this after position command is implemented
    '''
        slot_idx = getattr(ctx, 'slot_idx', None) or self.get_player_by_user_id(ctx.user_id)
        if slot_idx is None:
            raise ValueError("Could not determine slot_idx for declare_attack")
        action_data = ActionContext(slot_idx=slot_idx, action_type=ctx.action_type, target=ctx.target)
        self._upsert_action_queue(action_data)
        return action_data
        '''
    
    def declare_skill(self):
        pass

    # ============================================
    # SECTION 7: Utility & Data Export
    # ============================================

    def serialize(self) -> str:
        """Serialize game state to base64-encoded pickle (for DB storage).
        Excludes phase_task (asyncio.Task) since it is not pickleable."""
        phase_task = getattr(self, "phase_task", None)
        try:
            self.phase_task = None
            return base64.b64encode(pickle.dumps(self)).decode()
        finally:
            self.phase_task = phase_task

    @classmethod
    def deserialize(cls, blob: str):
        """Deserialize game from base64-encoded pickle."""
        return pickle.loads(base64.b64decode(blob))
    
    def vomit(self):
        data = {
            "type": "vomit_data",
            "id": self.id,
            "players": [asdict(p) for p in self.player_slots],
            "game_board": self.game_board
        }
        return data

    def get_player_by_user_id(self, user_id: str) -> int | None:
        """Return slot_idx (0-based) for the given user_id, or None if not found."""
        for player in self.player_slots:
            if player.info and player.info.id == user_id:
                return player.index
        return None

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
        
        for player in self.player_slots:
            if player.occupy != 1:
                continue
            if not player.character:
                continue
            team = player.team
            current_hp = player.current_hp
            
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

    def count_submissions(self):
        submissions = 0
        if self.in_combat:
            for player in self.player_slots:
                if player.action is not None:
                    submissions += 1
        return submissions

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