"""
Base command: all slash-command handlers inherit and implement run(ctx).
"""
from abc import ABC, abstractmethod
from typing import Any

from ....util.context import CommandContext, ActionContext


class BaseCommand(ABC):
    """One instance per command invocation. Set result/error/action_data in run()."""
    result: str | None = None
    error: str | None = None
    action_data: ActionContext | None = None

    @staticmethod
    def _is_combat_participant(game: Any, user_id: str) -> bool:
        player_ids = [p.info.get("id") for p in game.players if p.info and p.info.get("id")]
        return user_id in player_ids

    @abstractmethod
    async def validate(self, ctx: CommandContext) -> None:
        """Validate the command; set self.error."""
        ...

    @abstractmethod
    async def run(self, ctx: CommandContext) -> None:
        """Execute the command; set self.result, self.error, self.action_data."""
        ...
