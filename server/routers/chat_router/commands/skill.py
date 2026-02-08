"""
Skill commands: /스킬1, /스킬2, /스킬3, /스킬4 (and e.g. /순간가속 A2, /컨토션 자신 per USER_GUIDE)
"""
from ....util import conM
from ....util.models import CommandContext
from .base import BaseCommand

SKILL_COMMANDS = ["스킬1", "스킬2", "스킬3", "스킬4"]


class SkillCommand(BaseCommand):
    async def validate(self, ctx: CommandContext) -> None:
        game = ctx.game
        if not game.in_combat:
            self.error = "현재 단계에서 사용할 수 없는 명령어입니다."
            return
        if game.phase != "action_declaration":
            self.error = "현재 단계에서 사용할 수 없는 명령어입니다."
            return
        if not self._is_combat_participant(game, ctx.user_id):
            self.error = "전투 명령어는 전투 참여자만 사용할 수 있습니다."
            return

    async def run(self, ctx: CommandContext) -> None:
        game = ctx.game
        result, err = game.declare_skill(ctx.user_id, [ctx.command] + (ctx.args or []))
        self.result = result
        self.error = err

        if result and not err:
            await conM.broadcast_to_game(game.id, {
                "type": "action_submission_update",
                "submitted": game.get_action_submission_status(),
            })
