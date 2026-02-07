"""
Position management functions
Coordinate & position helpers
"""
import re

# Row mapping constants
ROW_MAP = {"Y": 0, "X": 1, "A": 2, "B": 3}
REV_ROW_MAP = {v: k for k, v in ROW_MAP.items()}


def declare_position(game, sender, command):
    """Declare position for a player"""
    from . import join
    
    result = None
    err = None
    idx = join.get_player_by_user_id(game, sender) - 1
    position = command[1].strip().upper()
    player = game.players[idx]

    if command[1][0] not in ROW_MAP:
        err = "유효하지 않은 열 번호입니다."
    
    if int(command[1][1]) not in (1, 2, 3, 4):
        err = "유효하지 않은 행 번호입니다."

    # Validate position using parse_position_declaration_from_chat logic
    r, c = pos_to_rc(position)
    
    if r < 0 or c < 0 or c > 3:
        err = "유효하지 않은 위치입니다."
    
    # Check if position is in player's team area
    # Row 0-1 (Y, X) = team 1 (blue), Row 2-3 (A, B) = team 0 (white)
    position_team = 1 if r <= 1 else 0
    if position_team != player.team:
        err = "자신의 진영만 선택할 수 있습니다."
    
    result = f"위치 {position} 선언 완료"

    return result, err


def move_player(game, name, command):
    """
    Legacy move command handler (chat command).
    TODO: Replace with proper combat movement system.
    """
    # Row 0: Y1, Y2, Y3, Y4
    # Row 1: X1, X2, X3, X4
    # Row 2: A1, A2, A3, A4
    # Row 3: B1, B2, B3, B4
    # Find the player slot whose character matches the sender's name
    player_slot = next((p for p in game.players if p.character and (p.character.get('name') if isinstance(p.character, dict) else None) == name), None)
    current_pos = player_slot.pos if player_slot else None

    match = re.search(r'\b([YXAB][1-4])\b', command)
    target_pos = match.group(1) if match else None
    if target_pos and player_slot:
        player_slot.pos = target_pos
        return f"{name} moved from {current_pos} to {target_pos}"
    else:
        return f"{name} move failed."


def pos_to_rc(pos: str) -> tuple[int, int]:
    """Convert position string ("Y1") to (row_idx, col_idx)"""
    r = ROW_MAP.get(pos[0], -1)
    c = int(pos[1]) - 1
    return r, c


def rc_to_pos(r: int, c: int) -> str:
    """Convert (row_idx, col_idx) to position string ("Y1")"""
    return f"{REV_ROW_MAP.get(r, '?')}{c + 1}"


def is_front_row(pos: str) -> bool:
    """Check if position is front row (X or A)"""
    r, _ = pos_to_rc(pos)
    return r == 1 or r == 2


def is_back_row(pos: str) -> bool:
    """Check if position is back row (Y or B)"""
    r, _ = pos_to_rc(pos)
    return r == 0 or r == 3


def check_move_validity(game, from_pos: str, to_pos: str, player_team: int) -> tuple[bool, str]:
    """Validate move destination (distance, team, occupancy)"""
    fr, fc = pos_to_rc(from_pos)
    tr, tc = pos_to_rc(to_pos)
    
    row_dist = abs(fr - tr)
    col_dist = abs(fc - tc)
    
    if row_dist > 1 or col_dist > 1:
        return False, "이동 거리 초과"
    if row_dist == 0 and col_dist == 0:
        return False, "같은 위치"
    
    to_team = 1 if tr <= 1 else 0
    if to_team != player_team:
        return False, "다른 팀 셀"
    
    if hasattr(game, 'combat_board') and game.combat_board.get(to_pos) is not None:
        return False, "이미 차지됨"
    
    return True, None
