"""
Preparation-phase commands: /참여, /관전, /join, /leave
"""
from ..context import CommandContext


async def preparation_command(ctx: CommandContext) -> tuple[str | None, str | None, dict | None]:
    if ctx.game.in_combat:
        return None, "현재 단계에서 사용할 수 없는 명령어입니다.", None

    command = ctx.command
    if command in ("참여", "join"):
        # TODO: Implement join logic
        return None, None, None
    if command in ("관전", "leave"):
        # TODO: Implement leave logic
        return None, None, None

    return None, "사용 가능한 준비 명령어: 참여, 관전.", None
