"""
Preparation-phase commands: /참여, /관전, /join, /leave
"""
from ..context import CommandContext
from .base import BaseCommand


class PreparationCommand(BaseCommand):
    async def run(self, ctx: CommandContext) -> None:
        if ctx.game.in_combat:
            self.error = "현재 단계에서 사용할 수 없는 명령어입니다."
            return

        command = ctx.command
        if command in ("참여", "join"):
            # TODO: Implement join logic
            return
        if command in ("관전", "leave"):
            # TODO: Implement leave logic
            return

        self.error = "사용 가능한 준비 명령어: 참여, 관전."
