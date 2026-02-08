"""
Base command: all slash-command handlers inherit and implement run(ctx).
"""
from abc import ABC, abstractmethod
from typing import Any

from ....util.models import CommandContext, ActionContext


class BaseCommand(ABC):
    @abstractmethod
    async def run(self, ctx: CommandContext) -> str:
        """Execute the command; return result string."""
        ...
