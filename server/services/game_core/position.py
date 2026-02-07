"""
Position management functions
Coordinate & position helpers
"""

# Row mapping constants
ROW_MAP = {"Y": 0, "X": 1, "A": 2, "B": 3}
REV_ROW_MAP = {v: k for k, v in ROW_MAP.items()}


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
