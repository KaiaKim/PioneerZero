"""
Position declaration: /위치 <cell>, /pos <cell> (e.g. A2)
"""
from ....services.game_core import position
from ....util.context import CommandContext
from .base import BaseCommand
from ....services.game_core import join


POSITION_COMMANDS = ["위치", "pos"]

class PositionCommand(BaseCommand):
    async def validate(self, ctx: CommandContext) -> None:
        if not ctx.game.in_combat:
            self.error = "현재 단계에서 사용할 수 없는 명령어입니다."
            return
        if ctx.game.phase != "position_declaration":
            self.error = "현재 단계에서 사용할 수 없는 명령어입니다."
            return
        if not self._is_combat_participant(ctx.game, ctx.user_id):
            self.error = "전투 명령어는 전투 참여자만 사용할 수 있습니다."
            return
        slot_num = join.get_player_by_user_id(ctx.game, ctx.user_id)
        if not slot_num:
            self.error = "플레이어 슬롯을 찾을 수 없습니다."
            return

        position = ctx.args[0].strip().upper()
        ROW_MAP = {"Y": 0, "X": 1, "A": 2, "B": 3}
        if position[0] not in ROW_MAP:
            self.error = "유효하지 않은 열 번호입니다."
            return
        if int(position[1]) not in (1, 2, 3, 4):
            self.error = "유효하지 않은 행 번호입니다."
            return

        # Row 0-1 (Y, X) = team 1 (blue), Row 2-3 (A, B) = team 0 (white)
        r, c = position.pos_to_rc(position)
        position_team = 1 if r <= 1 else 0
        if position_team != ctx.game.players[slot_num].team:
            self.error = "자신의 진영만 선택할 수 있습니다."
            return

    async def run(self, ctx: CommandContext) -> None:
        result = position.declare_position(ctx)
        self.result = result
