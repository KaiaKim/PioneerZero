"""
Dict-based command router: dispatch by command name to registered handlers.
"""
from typing import Awaitable, Callable, Dict

from .context import CommandContext

# Handler returns (result, err, action_data) for message/broadcast
CommandHandler = Callable[[CommandContext], Awaitable[tuple[str | None, str | None, dict | None]]]


class CommandRouter:
    def __init__(self) -> None:
        self._handlers: Dict[str, CommandHandler] = {}

    def register(self, name: str, handler: CommandHandler) -> None:
        self._handlers[name] = handler

    async def dispatch(self, command: str, ctx: CommandContext) -> tuple[str | None, str | None, dict | None]:
        if command not in self._handlers:
            raise ValueError(f"Unknown command: {command}")
        return await self._handlers[command](ctx)
