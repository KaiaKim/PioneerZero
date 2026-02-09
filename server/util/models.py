"""
Shared context types: command invocation (chat), action declaration (game),
player slot, character, and user identity. See services.game_core.characters for data constants.
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class UserInfo:
    """Identity for a connected user (Google, guest, or bot). Set at auth and stored per WebSocket."""
    id: str
    name: str = ""
    email: Optional[str] = None
    picture: Optional[str] = None
    is_google: bool = False
    is_guest: bool = False
    is_bot: bool = False

@dataclass
class PlayerSlot:
    """One player slot in the game (empty or occupied)."""
    index: int = 0
    info: Optional["UserInfo"] = None  # user or bot identity
    character: Optional["Character"] = None  # constants only
    ready: bool = False
    team: int = 0  # 0=white, 1=blue
    occupy: int = 0  # 0=empty, 1=occupied, 2=connection-lost
    action: Optional["ActionContext"] = None
    current_hp: int = 0  # mutable state
    pos: Optional[str] = None  # board position e.g. "A1"


@dataclass
class Character:
    """Character constants only. Mutable state (current_hp, pos) lives on PlayerSlot."""

    name: str = ""
    profile_image: str = ""
    token_image: str = ""
    stats: List[int] = field(default_factory=list)  # [vtl, sen, per, tal, mst]
    character_class: str = ""  # physical, psychic (key "class" in characters.py)
    type: str = ""  # none, etc.
    skills: List[str] = field(default_factory=list)
    initial_hp: int = 100
    initial_pos: Optional[str] = None  # default spawn e.g. "A1"


@dataclass
class CommandContext:
    """관전자도 플레이어도 보낼 수 있는 범용 커맨드 컨텍스트"""
    user_id: str
    slot_idx: Optional[int] = None
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
    slot_idx: int
    round: int = 0
    attack_type: str = ""
    skill_type: str = ""
    destination: str = ""  # character wants to go there, not yet arrived
    destination_resolved: bool = False
    target_char: str = "자신"
    target_cell: str = ""
    priority: int = 0
    power: int = 0
