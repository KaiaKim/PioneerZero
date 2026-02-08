"""
Attack commands: /근거리공격 <대상>, /원거리공격 <대상>, /대기
Target defaults to "자신" per USER_GUIDE.
"""
from dataclasses import asdict
from ....util import conM
from ....util.models import CommandContext
from .base import BaseCommand
ATTACK_COMMANDS = ["근거리공격", "원거리공격", "대기"]

class AttackCommand(BaseCommand):
    async def validate(self, ctx: CommandContext) -> None:
        if not ctx.game.in_combat:
            self.error = "현재 단계에서 사용할 수 없는 명령어입니다."
            return
        if ctx.game.phase != "action_declaration":
            self.error = "현재 단계에서 사용할 수 없는 명령어입니다."
            return
        if not self._is_combat_participant(ctx.game, ctx.user_id):
            self.error = "전투 명령어는 전투 참여자만 사용할 수 있습니다."
            return

    async def run(self, ctx: CommandContext) -> None:
        slot_idx = ctx.game.get_player_by_user_id(ctx.user_id)
        target = ctx.args[0].strip() if ctx.args else "자신"
        action_data, err = ctx.game.declare_attack()

        if not action_data or err:
            self.error = err
            return

        self.result = f'행동 선언 완료: {ctx.command}' + (f" {target}" if ctx.args else "")
        self.action_data = action_data

        if ctx.websocket:
            await ctx.websocket.send_json({
                "type": "declared_attack",
                "attack_info": asdict(action_data),
            })
        await conM.broadcast_to_game(ctx.game.id, {
            "type": "action_submission_update",
            "submitted": ctx.game.get_action_submission_status(),
        })
