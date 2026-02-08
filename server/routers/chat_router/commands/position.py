"""
Position declaration: /위치 <cell>, /pos <cell> (e.g. A2)
"""
from ....services.game_core import position
from ....util.context import CommandContext
from .base import BaseCommand
from ....services.game_core import join


POSITION_COMMANDS = ["위치", "pos"]

class PositionCommand(BaseCommand):
    async def validate(self, ctx: CommandContext) -> str:
        if not ctx.game.in_combat:
            return "현재 단계에서 사용할 수 없는 명령어입니다."
        if ctx.game.phase != "position_declaration":
            return "현재 단계에서 사용할 수 없는 명령어입니다."
        if not self._is_combat_participant(ctx.game, ctx.user_id):
            return "전투 명령어는 전투 참여자만 사용할 수 있습니다."
        slot_num = join.get_player_by_user_id(ctx.game, ctx.user_id)
        if not slot_num:
            return "플레이어 슬롯을 찾을 수 없습니다."
        slot_idx = slot_num - 1
        cell = ctx.args[0].strip().upper()
        ROW_MAP = {"Y": 0, "X": 1, "A": 2, "B": 3}
        if cell[0] not in ROW_MAP:
            return "유효하지 않은 열 번호입니다."
        if int(cell[1]) not in (1, 2, 3, 4):
            return "유효하지 않은 행 번호입니다."

        # Row 0-1 (Y, X) = team 1 (blue), Row 2-3 (A, B) = team 0 (white)
        r, c = position.pos_to_rc(cell)
        position_team = 1 if r <= 1 else 0
        if position_team != ctx.game.players[slot_idx].team:
            return "자신의 진영만 선택할 수 있습니다."

        return None

    async def run(self, ctx: CommandContext) -> str:
        position.declare_position(ctx)
        
        #I can add custom feedback to clients via websocket here.
        #game commands might not need one, but other commands might need it.

        return "위치 선언이 완료되었습니다."
