"""
Position declaration: /위치 <cell>, /pos <cell> (e.g. A2)
"""
from ....services.game_core import position
from ..context import CommandContext

POSITION_COMMANDS = ["위치", "pos"]


def _is_combat_participant(game, user_id: str) -> bool:
    player_ids = [p.get("info", {}).get("id") for p in game.players if p.get("info")]
    return user_id in player_ids


async def position_command(ctx: CommandContext) -> tuple[str | None, str | None, dict | None]:
    game = ctx.game
    if not game.in_combat:
        return None, "현재 단계에서 사용할 수 없는 명령어입니다.", None
    if game.phase != "position_declaration":
        return None, "현재 단계에서 사용할 수 없는 명령어입니다.", None
    if not _is_combat_participant(game, ctx.user_id):
        return None, "전투 명령어는 전투 참여자만 사용할 수 있습니다.", None

    result, err = position.declare_position(game, ctx.user_id, [ctx.command] + ctx.args)
    return result, err, None
