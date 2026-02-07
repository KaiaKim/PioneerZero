"""
Command context passed to slash-command handlers.
"""
from dataclasses import dataclass
from typing import Any, List

@dataclass
class CommandContext:
    """Context for a single slash command execution."""

    user_id: str
    channel_id: str  # game_id
    raw: str
    args: List[str]
    command: str  # command name (first token after "/")

    # Injected by handle_chat for handler use
    game: Any = None
    websocket: Any = None
    sender: str = ""
