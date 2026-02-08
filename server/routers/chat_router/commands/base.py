"""
Base command: all slash-command handlers inherit and implement run(ctx).
"""
from abc import ABC, abstractmethod
from typing import Any

from ....util.models import CommandContext, ActionContext


class BaseCommand(ABC):
    @staticmethod
    def _is_combat_participant(game: Any, user_id: str) -> bool:
        player_ids = [p.info.get("id") for p in game.players if p.info and p.info.get("id")]
        return user_id in player_ids

    @abstractmethod
    async def validate(self, ctx: CommandContext) -> str | None:
        """Validate the command; return error string or None."""
        ...

    @abstractmethod
    async def run(self, ctx: CommandContext) -> str:
        """Execute the command; return result string."""
        ...
