"""
Base command: all slash-command handlers inherit and implement run(ctx).
"""
from abc import ABC, abstractmethod
from typing import Any

from ..context import CommandContext


class BaseCommand(ABC):
    """One instance per command invocation. Set result/error/action_data in run()."""

    result: str | None = None
    error: str | None = None
    action_data: dict[str, Any] | None = None

    def __init__(self, ctx: CommandContext):
        self.validate(ctx)
        self.run(ctx)
        
    @abstractmethod
    async def validate(self, ctx: CommandContext) -> None:
        """Validate the command; set self.error."""
        ...




    @abstractmethod
    async def run(self, ctx: CommandContext) -> None:
        """Execute the command; set self.result, self.error, self.action_data."""
        ...
