"""
Attack commands: /근거리공격 <대상>, /원거리공격 <대상>, /대기
Target defaults to "자신" per USER_GUIDE.
"""
from ....util import conM
from ..context import CommandContext

ATTACK_COMMANDS = ["근거리공격", "원거리공격", "대기"]


def _is_combat_participant(game, user_id: str) -> bool:
    player_ids = [p.get("info", {}).get("id") for p in game.players if p.get("info")]
    return user_id in player_ids


async def attack_command(ctx: CommandContext) -> tuple[str | None, str | None, dict | None]:
    game = ctx.game
    if not game.in_combat:
        return None, "현재 단계에서 사용할 수 없는 명령어입니다.", None
    if game.phase != "action_declaration":
        return None, "현재 단계에서 사용할 수 없는 명령어입니다.", None
    if not _is_combat_participant(game, ctx.user_id):
        return None, "전투 명령어는 전투 참여자만 사용할 수 있습니다.", None

    target = ctx.args[0].strip() if ctx.args else "자신"
    action_data, err = game.declare_attack(ctx.user_id, ctx.command, target)

    if not action_data or err:
        return None, err, None

    result = f'행동 선언 완료: {ctx.command}' + (f" {target}" if ctx.args else "")

    if ctx.websocket:
        await ctx.websocket.send_json({
            "type": "declared_attack",
            "attack_info": action_data,
        })
    await conM.broadcast_to_game(game.id, {
        "type": "action_submission_update",
        "submitted": game.get_action_submission_status(),
    })

    return result, None, action_data
