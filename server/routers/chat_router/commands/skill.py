"""
Skill commands: /스킬1, /스킬2, /스킬3, /스킬4 (and e.g. /순간가속 A2, /컨토션 자신 per USER_GUIDE)
"""
from ....util import conM
from ..context import CommandContext

SKILL_COMMANDS = ["스킬1", "스킬2", "스킬3", "스킬4"]


def _is_combat_participant(game, user_id: str) -> bool:
    player_ids = [p.get("info", {}).get("id") for p in game.players if p.get("info")]
    return user_id in player_ids


async def skill_command(ctx: CommandContext) -> tuple[str | None, str | None, dict | None]:
    game = ctx.game
    if not game.in_combat:
        return None, "현재 단계에서 사용할 수 없는 명령어입니다.", None
    if game.phase != "action_declaration":
        return None, "현재 단계에서 사용할 수 없는 명령어입니다.", None
    if not _is_combat_participant(game, ctx.user_id):
        return None, "전투 명령어는 전투 참여자만 사용할 수 있습니다.", None

    result, err = game.declare_skill(ctx.user_id, [ctx.command] + ctx.args)

    if result and not err:
        await conM.broadcast_to_game(game.id, {
            "type": "action_submission_update",
            "submitted": game.get_action_submission_status(),
        })

    return result, err, None
