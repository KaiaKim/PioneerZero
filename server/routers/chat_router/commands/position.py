"""
Position declaration: /위치 <cell>, /pos <cell> (e.g. A2)
"""
from ....util.models import CommandContext
from .base import BaseCommand


POSITION_COMMANDS = ["위치", "pos"]

class PositionCommand(BaseCommand):
    async def validate(self, ctx: CommandContext) -> str:
        if not ctx.game.in_combat:
            return "현재 단계에서 사용할 수 없는 명령어입니다."
        if ctx.game.phase != "position_declaration":
            return "현재 단계에서 사용할 수 없는 명령어입니다."
        if not self._is_combat_participant(ctx.game, ctx.user_id):
            return "전투 명령어는 전투 참여자만 사용할 수 있습니다."
        ctx.slot_idx = ctx.game.get_player_by_user_id(ctx.user_id)
        if ctx.slot_idx is None:
            return "플레이어 슬롯을 찾을 수 없습니다."
        cell = ctx.args[0].strip().upper()
        ROW_MAP = {"Y": 0, "X": 1, "A": 2, "B": 3}
        if cell[0] not in ROW_MAP:
            return "유효하지 않은 열 번호입니다."
        if int(cell[1]) not in (1, 2, 3, 4):
            return "유효하지 않은 행 번호입니다."

        # Row 0-1 (Y, X) = team 1 (blue), Row 2-3 (A, B) = team 0 (white)
        called_team = 1 if cell[0] in ["Y", "X"] else 0
        my_team = ctx.game.player_slots[ctx.slot_idx].team
        if called_team != my_team:
            return "자신의 진영만 선택할 수 있습니다."

        return None

    async def run(self, ctx: CommandContext) -> str:
        ctx.game.declare_position(ctx)
        
        #I can add custom feedback to clients via websocket here.
        #game commands might not need one, but other commands might need it.

        return "위치 선언이 완료되었습니다."
