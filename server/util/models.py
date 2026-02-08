"""
Shared context types: command invocation (chat), action declaration (game),
player slot, and character. See services.game_core.characters for data constants.
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional

@dataclass
class PlayerSlot:
    """One player slot in the game (empty or occupied)."""
    index: int = 0
    info: Any = None  # user/bot info dict
    character: Any = None #Character object
    ready: bool = False
    team: int = 0  # 0=white, 1=blue
    occupy: int = 0  # 0=empty, 1=occupied, 2=connection-lost
    submission: Optional[Any] = None #ActionContext object

@dataclass
class Character:
    """Character data. Shape matches services.game_core.characters (default_character, bots)."""

    name: str = ""
    profile_image: str = ""
    token_image: str = ""
    stats: List[int] = field(default_factory=list)  # [vtl, sen, per, tal, mst]
    character_class: str = ""  # physical, psychic (key "class" in characters.py)
    type: str = ""  # none, etc.
    skills: List[str] = field(default_factory=list)
    current_hp: int = 0
    pos: Optional[str] = None  # board position e.g. "A1"


@dataclass
class CommandContext:
    """관전자도 플레이어도 보낼 수 있는 범용 커맨드 컨텍스트"""
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
    """우선도, 공격력, 특수효과 등이 계산되어 액션 큐에 등록되는 데이터."""

    slot: int
    action_type: str
    skill_chain: Optional[Any] = None
    target: str = "자신"
    target_slot_idx: Optional[int] = None  # 0-based
    priority: Optional[int] = None
    attack_power: Optional[int] = None
    resolved: bool = False
    destination: Any = None  # character wants to go there, not yet arrived
