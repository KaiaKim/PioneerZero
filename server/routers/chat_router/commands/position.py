"""
Position declaration: /위치 <cell>, /pos <cell> (e.g. A2)
"""
from ....services.game_core import position
from ....util.context import CommandContext
from .base import BaseCommand

POSITION_COMMANDS = ["위치", "pos"]


class PositionCommand(BaseCommand):
    async def validate(self, ctx: CommandContext) -> None:
        game = ctx.game
        if not game.in_combat:
            self.error = "현재 단계에서 사용할 수 없는 명령어입니다."
            return
        if game.phase != "position_declaration":
            self.error = "현재 단계에서 사용할 수 없는 명령어입니다."
            return
        if not self._is_combat_participant(game, ctx.user_id):
            self.error = "전투 명령어는 전투 참여자만 사용할 수 있습니다."
            return

    async def run(self, ctx: CommandContext) -> None:
        result, err = position.declare_position(ctx.game, ctx.user_id, [ctx.command] + (ctx.args or []))
        self.result = result
        self.error = err
