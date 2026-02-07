"""
Shared context types: command invocation (chat), action declaration (game), and player slot.
"""
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Player:
    """One player slot in the game (empty or occupied)."""

    info: Any = None  # user/bot info dict
    character: Any = None
    slot: int = 0
    ready: bool = False
    team: int = 0  # 0=white, 1=blue
    occupy: int = 0  # 0=empty, 1=occupied, 2=connection-lost
    pos: Any = None  # position on the game board


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


@dataclass
class ActionContext:
    """Declared action payload for the game action queue."""

    slot: int
    action_type: str
    skill_chain: Optional[Any] = None
    target: str = "자신"
    target_slot: Optional[int] = None
    priority: Optional[int] = None
    attack_power: Optional[int] = None
    resolved: bool = False
