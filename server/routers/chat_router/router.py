"""
Dict-based command router: dispatch by command name to registered handler classes.
"""
from typing import Dict, Type

from ...util.context import CommandContext
from .commands.base import BaseCommand


class CommandManager:
    def __init__(self) -> None:
        self._handlers: Dict[str, Type[BaseCommand]] = {}

    def register(self, name: str, handler_class: Type[BaseCommand]) -> None:
        self._handlers[name] = handler_class

    async def dispatch(self, command: str, ctx: CommandContext) -> tuple[str | None, str | None, dict | None]:
        #dispatch is now being handled in handle_chat. Might separate it later.
        pass

    def get_cmd(self, command: str) -> BaseCommand:
        return self._handlers[command]

cmdM = CommandManager()
