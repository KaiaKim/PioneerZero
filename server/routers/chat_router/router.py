"""
Dict-based command router: dispatch by command name to registered handler classes.
"""
from typing import Dict, Type

from .context import CommandContext
from .commands.base import BaseCommand


class CommandManager:
    def __init__(self) -> None:
        self._handlers: Dict[str, Type[BaseCommand]] = {}

    def register(self, name: str, handler_class: Type[BaseCommand]) -> None:
        self._handlers[name] = handler_class

    async def dispatch(self, command: str, ctx: CommandContext) -> tuple[str | None, str | None, dict | None]:
        if command not in self._handlers:
            raise ValueError(f"Unknown command: {command}")
        cmd = self._handlers[command]()
        await cmd.validate(ctx)
        await cmd.run(ctx)
        return (cmd.result, cmd.error, cmd.action_data)
