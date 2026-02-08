"""
Position declaration: /위치 <cell>, /pos <cell> (e.g. A2)
"""
from ....util.models import CommandContext
from .base import BaseCommand


POSITION_COMMANDS = ["위치", "pos"]

class PositionCommand(BaseCommand):
    async def run(self, ctx: CommandContext) -> str:
        ctx.game.declare_position(ctx)
        
        #I can add custom feedback to clients via websocket here.
        #game commands might not need one, but other commands might need it.

        return "위치 선언이 완료되었습니다."
