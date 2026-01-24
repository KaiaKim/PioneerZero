# 전투 시스템 구현 계획

## 1. 데이터 구조

```python
character = {
    "name": "Pikita",
    "profile_image": "/images/pikita_profile.png",
    "token_image": "/images/pikita_token.png",
    "stats": {"vtl": 4, "sen": 1, "per": 1, "tal": 2, "mst": 2},
    "class": "physical",
    "type": "none",
    "skills": ["Medikit", "Acceleration", "Contortion"],
    "current_hp": 30,
    "max_hp": 30,
    "pos": "A1",
    "team": 0  # 0=white, 1=blue
}
```

### 1.2 전투 상태 데이터

```python
class Game():
    def __init__(self, id, player_num=4):
        # ... 기존 코드 ...
        self.combat_state = {
            'in_combat': False,
            'current_round': 0,
            'phase': 'preparation',  # 'preparation', 'position_declaration', 'action_declaration', 'resolution', 'wrap-up'
            'action_queue': [],  # 공격과 스킬이 등록되는 큐 (즉시 실행되지 않음)
            'resolved_actions': [],
            'early_submission_pending': False  # 모든 플레이어가 일찍 제출한 경우 확정 대기 상태
        }

```

### 1.3 데이터 구조

```python
position_declaration = {
    'slot': 1,
    'position': 'A1',
    'declared_at': 1234567890,
    'butted': False,
    'final_position': 'A1'
}

action_data = {
    'slot': 1,
    'action_type': 'melee_attack',  # 'melee_attack', 'ranged_attack', 'wait' (전장이동은 스킬로 처리)
    'skill_chain': None,  # 스킬은 단독 사용 또는 공격과 조합 가능
    'target': 'X2',  # 캐릭터 이름 또는 위치, 미지정 시 '자신'
    'target_slot': 2,
    'priority': 44,
    'attack_power': 12,
    'resolved': False
}
```
---

## 3. 핵심 로직 구현

### 3.1 우선도 계산

```python
def calculate_priority(self, slot, action_type, skill_chain=None):
    """
    공격 우선도 계산 (전장이동은 스킬로 처리되므로 제외)
    """
    player = self.players[slot - 1]
    stats = player['character']['stats']
    
    if action_type == 'melee_attack':
        base_priority = stats['sen'] * 10 + stats['mst']
    elif action_type == 'ranged_attack':
        base_priority = stats['per'] * 10 + stats['mst']
    elif action_type == 'wait':
        base_priority = 100 + stats['mst']
    #else is not needed because no submission is already process as 'wait'
    
    if skill_chain:
        from server.skills import SKILLS
        skill = SKILLS.get(skill_chain)
        if skill and skill.get('priority_mod'):
            bonus = skill['priority_mod'](stats) if callable(skill['priority_mod']) else skill['priority_mod']
            base_priority += bonus
    
    return base_priority
```

### 3.2 공격력 계산

```python
def calculate_attack_power(self, slot, action_type, skill_chain=None):
    player = self.players[slot - 1]
    stats = player['character']['stats']
    
    if action_type == 'melee_attack':
        base_power = (stats['per'] * 2) + (stats['sen'] * 3) + 5
    elif action_type == 'ranged_attack':
        base_power = (stats['per'] * 3) + (stats['sen'] * 2)
    
    if skill_chain:
        from server.skills import SKILLS
        skill = SKILLS.get(skill_chain)
        if skill and skill.get('power_mod'):
            bonus = skill['power_mod'](stats) if callable(skill['power_mod']) else skill['power_mod']
            base_power += bonus
    
    return max(0, base_power)
```

### 3.3 좌표 표준화

```python
ROW_MAP = {"Y": 0, "X": 1, "A": 2, "B": 3}
REV_ROW_MAP = {v: k for k, v in ROW_MAP.items()}

def pos_to_rc(self, pos: str) -> tuple[int, int]:
    r = ROW_MAP.get(pos[0], -1)
    c = int(pos[1]) - 1
    return r, c

def rc_to_pos(self, r: int, c: int) -> str:
    return f"{REV_ROW_MAP.get(r, '?')}{c + 1}"

def is_front_row(self, pos: str) -> bool:
    r, _ = self.pos_to_rc(pos)
    return r == 1 or r == 2

def is_back_row(self, pos: str) -> bool:
    r, _ = self.pos_to_rc(pos)
    return r == 0 or r == 3

def check_move_validity(self, from_pos: str, to_pos: str, player_team: int, max_distance: int = 1) -> tuple[bool, str]:
    """
    이동 유효성 검사
    max_distance: 최대 이동 거리 (기본값 1, 스킬에 따라 2 등으로 변경 가능)
    """
    fr, fc = self.pos_to_rc(from_pos)
    tr, tc = self.pos_to_rc(to_pos)
    
    row_dist = abs(fr - tr)
    col_dist = abs(fc - tc)
    
    # 체비셰프 거리 (상하좌우 대각선 모두 포함)
    distance = max(row_dist, col_dist)
    
    if distance > max_distance:
        return False, f"이동 거리 초과 (최대 {max_distance}칸)"
    if row_dist == 0 and col_dist == 0:
        return False, "같은 위치"
    
    to_team = 1 if tr <= 1 else 0
    if to_team != player_team:
        return False, "다른 팀 셀"
    
    if self.combat_board.get(to_pos) is not None:
        return False, "이미 차지됨"
    
    return True, None
```

### 3.4 사거리 체크

```python
def check_range(self, attacker_pos, target_pos, action_type):
    ar, ac = self.pos_to_rc(attacker_pos)
    tr, tc = self.pos_to_rc(target_pos)
    
    if ac != tc:
        return False, "같은 열만 공격 가능"
    
    row_dist = abs(ar - tr)
    
    if action_type == 'melee_attack':
        if not (self.is_front_row(attacker_pos) and self.is_front_row(target_pos)):
            return False, "근거리는 전방↔전방만"
        if row_dist != 1:
            return False, "근거리 사거리 1만"
        return True, None
    
    elif action_type == 'ranged_attack':
        if self.is_front_row(attacker_pos) and self.is_front_row(target_pos):
            return False, "원거리는 전방→전방 불가"
        if row_dist < 2 or row_dist > 3:
            return False, "원거리 사거리 2~3만"
        return True, None
    
    return False, "알 수 없는 타입"
```

### 3.5 커버링 체크

```python
def check_covering(self, attacker_pos, target_pos, attacker_team):
    ar, ac = self.pos_to_rc(attacker_pos)
    tr, tc = self.pos_to_rc(target_pos)
    
    if ac != tc or not self.is_back_row(target_pos):
        return True, None
    
    front_row = 1 if tr == 0 else 2
    front_pos = self.rc_to_pos(front_row, tc)
    occupant = self.combat_board.get(front_pos)
    
    if occupant and occupant['team'] != attacker_team:
        return False, f"{front_pos} 커버링 중"
    
    return True, None
```

### 3.5.1 대상 지정 헬퍼

```python
def find_slot_by_name(self, character_name):
    """캐릭터 이름으로 slot 찾기"""
    for i, player in enumerate(self.players):
        if player.get('character') and player['character'].get('name') == character_name:
            return i + 1
    return None
```

### 3.6 공격 해결

```python
def resolve_action(self, action_data):
    """
    공격 해결 (전장이동은 스킬로 처리되므로 제외)
    대상 지정: 캐릭터 이름 또는 위치, 미지정 시 '자신'
    """
    slot = action_data['slot']
    action_type = action_data['action_type']
    player = self.players[slot - 1]
    attacker_pos = player['character']['pos']
    
    result = {'slot': slot, 'action_type': action_type, 'success': False, 'message': '', 'damage_dealt': 0, 'target_hp_after': None}
    
    if action_type in ['melee_attack', 'ranged_attack']:
        target = action_data.get('target', '자신')  # 미지정 시 '자신'
        
        # 대상이 캐릭터 이름인지 위치인지 판단
        if target == '자신':
            target_pos = attacker_pos
            target_slot = slot
        elif target in self.combat_board:
            # 위치 지정
            target_pos = target
            occupant = self.combat_board.get(target_pos)
            target_slot = occupant['slot'] if occupant else None
        else:
            # 캐릭터 이름 지정 - 현재 위치에서 찾기
            target_slot = self.find_slot_by_name(target)
            if target_slot:
                target_pos = self.players[target_slot - 1]['character']['pos']
            else:
                return {**result, 'message': "대상 찾을 수 없음"}
        
        if not target_pos:
            return {**result, 'message': "대상 미지정"}
        
        range_ok, range_msg = self.check_range(attacker_pos, target_pos, action_type)
        if not range_ok:
            return {**result, 'message': range_msg}
        
        if action_type == 'ranged_attack' and not action_data.get('ignore_covering', False):
            covering_ok, covering_msg = self.check_covering(attacker_pos, target_pos, player['team'])
            if not covering_ok:
                return {**result, 'message': covering_msg}
        
        attack_power = self.calculate_attack_power(slot, action_type, action_data.get('skill_chain'))
        
        if target_slot:
            target_char = self.players[target_slot - 1]['character']
            damage = attack_power
            target_char['current_hp'] = max(0, target_char['current_hp'] - damage)
            return {**result, 'success': True, 'damage_dealt': damage, 'target_hp_after': target_char['current_hp']}
    
    elif action_type == 'wait':
        return {**result, 'success': True, 'message': "대기"}
    
    return result
```

### 3.7 유효한 타일 계산

```python
def get_valid_attack_tiles(self, slot, action_type):
    player = self.players[slot - 1]
    attacker_pos = player['character']['pos']
    attacker_team = player['team']
    if not attacker_pos:
        return []
    
    valid_tiles = []
    ar, ac = self.pos_to_rc(attacker_pos)
    
    for r in range(4):
        target_pos = self.rc_to_pos(r, ac)
        if target_pos == attacker_pos:
            continue
        if not self.check_range(attacker_pos, target_pos, action_type)[0]:
            continue
        if action_type == 'ranged_attack' and not self.check_covering(attacker_pos, target_pos, attacker_team)[0]:
                continue
        target_occupant = self.combat_board.get(target_pos)
        if target_occupant and target_occupant['team'] != attacker_team:
            valid_tiles.append(target_pos)
    return valid_tiles

def get_valid_move_tiles(self, slot, max_distance: int = 1):
    """
    유효한 이동 타일 계산
    max_distance: 최대 이동 거리 (스킬에 따라 다를 수 있음, 기본값 1)
    """
    player = self.players[slot - 1]
    from_pos = player['character']['pos']
    player_team = player['team']
    if not from_pos:
        return []
    
    valid_tiles = []
    fr, fc = self.pos_to_rc(from_pos)
    # 체비셰프 거리로 체크 (상하좌우 대각선 모두 포함)
    for dr in range(-max_distance, max_distance + 1):
        for dc in range(-max_distance, max_distance + 1):
            if dr == 0 and dc == 0:
                continue
            # 체비셰프 거리 체크
            if max(abs(dr), abs(dc)) > max_distance:
                continue
            tr, tc = fr + dr, fc + dc
            if 0 <= tr < 4 and 0 <= tc < 4:
                to_pos = self.rc_to_pos(tr, tc)
                if self.check_move_validity(from_pos, to_pos, player_team, max_distance)[0]:
                    valid_tiles.append(to_pos)
    return valid_tiles

def get_tile_feedback(self, slot, action_type=None):
    """
    타일 피드백 (이동은 스킬로 처리되므로 action_type으로는 공격만)
    """
    result = {'valid_attack_tiles': [], 'valid_move_tiles': []}
    if action_type in ['melee_attack', 'ranged_attack']:
        result['valid_attack_tiles'] = self.get_valid_attack_tiles(slot, action_type)
    # 이동 타일은 스킬별로 계산 (스킬 시스템에서 처리)
    if action_type is None:
        result['valid_move_tiles'] = self.get_valid_move_tiles(slot)  # 기본 이동 스킬용
    return result
```

### 3.8 위치 선언 및 버팅

```python
def parse_position_declaration_from_chat(self, slot, position):
    player = self.players[slot - 1]
    player_team = player['team']
    r, c = self.pos_to_rc(position)
    
    if r < 0 or c < 0:
        return {"success": False, "message": "유효하지 않은 위치"}
    
    position_team = 1 if r <= 1 else 0
    if position_team != player_team:
        return {"success": False, "message": "자신의 진영만 가능"}
    
    return {"success": True, "message": f"위치 {position} 선언 완료"}

def resolve_position_declarations(self, declarations):
    """선언 처리 및 버팅 해결 (채팅 히스토리에서 파싱된 데이터 사용)"""
    position_groups = {}
    for slot, decl in declarations.items():
        pos = decl['position']
        position_groups.setdefault(pos, []).append(decl)
    
    butted_players = []
    final_positions = {}
    
    # 충돌 없는 선언 확정
    for position, group in position_groups.items():
        if len(group) == 1:
            decl = group[0]
            final_positions[decl['slot']] = position
            decl['final_position'] = position
    
    # 충돌 처리: 나중 선언자가 버팅됨
    import random
    for position, group in position_groups.items():
        if len(group) > 1:
            sorted_group = sorted(group, key=lambda x: x['declared_at'])
            first_decl = sorted_group[0]
            final_positions[first_decl['slot']] = position
            first_decl['final_position'] = position
            
            for decl in sorted_group[1:]:
                decl['butted'] = True
                butted_players.append(decl)
    
    # 버팅된 플레이어 이동: 인접 빈칸 우선, 없으면 전체 빈칸
    for butted_decl in butted_players:
        slot = butted_decl['slot']
        player = self.players[slot - 1]
        declared_pos = butted_decl['position']
        
        adjacent = self.get_adjacent_empty_positions(declared_pos, player['team'], final_positions.values())
        if adjacent:
            final_pos = random.choice(adjacent)
        else:
            all_empty = self.get_empty_team_positions(player['team'], final_positions.values())
            final_pos = random.choice(all_empty) if all_empty else declared_pos
            if final_pos == declared_pos:
                butted_decl['butted'] = False
        
        butted_decl['final_position'] = final_pos
        final_positions[slot] = final_pos
    
    # 최종 배치
    for slot, decl in declarations.items():
        final_pos = decl['final_position']
        player = self.players[slot - 1]
        self.combat_board[final_pos] = {'slot': slot, 'name': player['character']['name'], 'team': player['team']}
        player['character']['pos'] = final_pos
    
    return {"success": True, "declarations": declarations, "butted_count": len(butted_players)}

def get_adjacent_empty_positions(self, from_pos, team, excluded_positions=None):
    adjacent_empty = []
    excluded = set(excluded_positions or [])
    fr, fc = self.pos_to_rc(from_pos)
    
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            tr, tc = fr + dr, fc + dc
            if 0 <= tr < 4 and 0 <= tc < 4:
                to_pos = self.rc_to_pos(tr, tc)
                to_team = 1 if tr <= 1 else 0
                if to_team == team and self.combat_board.get(to_pos) is None and to_pos not in excluded:
                    adjacent_empty.append(to_pos)
    return adjacent_empty

def get_empty_team_positions(self, team, excluded_positions=None):
    excluded = set(excluded_positions or [])
    team_rows = [(2, 3), (0, 1)][team]
    return [self.rc_to_pos(r, c) for r in range(team_rows[0], team_rows[1] + 1) for c in range(4)
            if self.combat_board.get(self.rc_to_pos(r, c)) is None and self.rc_to_pos(r, c) not in excluded]

def check_all_positions_declared(self):
    """채팅 히스토리에서 파싱하여 확인 (PLAN_WEBSOCKET.md 참고)"""
    pass
```

### 3.9 체력 계산

```python
def calculate_max_hp(self, vitality):
    return vitality * 5 + 10

def initialize_character_hp(self, slot):
    player = self.players[slot - 1]
    max_hp = self.calculate_max_hp(player['character']['stats']['vtl'])
    player['character']['max_hp'] = max_hp
    player['character']['current_hp'] = max_hp
```


**큐 시스템:**
- 공격과 스킬은 즉시 실행되지 않고 큐에 등록됨
- 효과, 우선도, 공격력이 미리 계산되어 표시됨
- 플레이어는 확정 전에 큐에 등록된 내용을 미리 볼 수 있음
- 모든 플레이어가 제한 시간 전에 제출하면 확정할지 묻는 알림창 표시


---

## 4. WebSocket 메시지 프로토콜

**주의**: 선언은 채팅 명령어로 처리 (PLAN_WEBSOCKET.md 참고)

### 4.1 위치 선언 메시지

#### 서버 → 클라이언트: 위치 선언 단계 시작
```json
{
    "type": "position_declaration_phase",
    "message": "시작 위치를 선언하세요: /위치 A1 형식으로 입력"
}
```

#### 서버 → 클라이언트: 위치 선언 확인 (채팅 메시지로 응답)
```json
{
    "type": "chat",
    "sender": "System",
    "content": "위치 A1 선언 완료",
    "sort": "system",
    "time": "2024-01-01T12:00:00"
}
```

#### 서버 → 클라이언트: 위치 선언 완료 및 결과 (비밀)
```json
{
    "type": "position_declaration_result",
    "slot": 1,
    "declared_position": "A1",
    "final_position": "A1",
    "butted": false
}
```

#### 서버 → 클라이언트: 전투 시작 (모든 위치 선언 완료)
```json
{
    "type": "combat_started",
    "round": 1,
    "combat_board": {
        "A1": {"slot": 1, "name": "Pikita", "team": 0},
        "B2": {"slot": 2, "name": "Player2", "team": 0},
        "X1": {"slot": 3, "name": "Player3", "team": 1},
        "Y3": {"slot": 4, "name": "Player4", "team": 1}
    },
    "butting_results": [
        {
            "slot": 2,
            "declared_position": "A1",
            "final_position": "B2",
            "butted": true,
            "reason": "Slot 1이 먼저 A1을 선언했습니다"
        }
    ]
}
```

