"""
Dict-based command router: dispatch by command name to registered handler classes.
"""
from typing import Dict, Optional, Type
from .commands.base import BaseCommand


class CommandManager:
    def __init__(self) -> None:
        self._handlers: Dict[str, Type[BaseCommand]] = {}

    def register(self, name: str, handler_class: Type[BaseCommand]) -> None:
        self._handlers[name] = handler_class

    def get_handler(self, command: str) -> Optional[BaseCommand]:
        """Return a command handler instance for the given command, or None if unknown."""
        cls = self._handlers.get(command)
        if cls is None:
            return None
        return cls()

cmdM = CommandManager()
