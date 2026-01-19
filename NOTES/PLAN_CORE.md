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
            'action_queue': [],
            'resolved_actions': []
        }
        # 선언 데이터는 채팅 히스토리에서 파싱 (PLAN_WEBSOCKET.md 참고)
        
        # 전투 보드 (4x4): row_idx 0=Y, 1=X, 2=A, 3=B | col_idx 0-3 = 1-4
        # XY = team 1 (blue), AB = team 0 (white)
        self.combat_board = {
            'Y1': None, 'Y2': None, 'Y3': None, 'Y4': None,
            'X1': None, 'X2': None, 'X3': None, 'X4': None,
            'A1': None, 'A2': None, 'A3': None, 'A4': None,
            'B1': None, 'B2': None, 'B3': None, 'B4': None
        }
        
        self.timer = {
            'type': None,
            'start_time': None,
            'duration': None,
            'is_running': False,
            'paused_at': None,
            'elapsed_before_pause': 0
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
    'action_type': 'melee_attack',  # 'melee_attack', 'ranged_attack', 'battlefield_move', 'wait'
    'skill_chain': None,
    'target': 'X2',
    'target_slot': 2,
    'move_to': 'A2',
    'priority': 44,
    'attack_power': 12,
    'resolved': False
}
```

---

## 2. 데이터 플로우

### 2.1 전투 시작

```
1. 전투 시작 브로드캐스트 → 3초 후 FloorArea 전환
2. 위치 선언 단계: `/위치 A1` (채팅 명령어, PLAN_WEBSOCKET.md 참고)
3. 버팅 처리: 같은 위치 선언 시 나중 선언자가 인접 빈칸으로 이동
4. 최종 위치 배치: combat_board 및 player['character']['pos'] 업데이트
5. phase = 'preparation', round = 1
```

### 2.2 라운드 플로우

1. 행동 선언: 60초 타이머, 채팅 명령어로 비밀 제출
2. 우선도 계산: action_queue에 우선도 순 정렬
3. 해결: action_queue 순차 처리, 결과 기록
4. 라운드 종료: 전투 불능/승리 조건 체크

### 2.3 우선도 계산

- 근거리공격: sen*10 + mst
- 원거리공격: per*10 + mst
- 전장이동: (sen+per)*5 + mst
- 대기: 100 + mst
- 스킬 체인 보정 적용 후 내림차순 정렬

### 2.4 행동 해결

- 근거리공격: 전방↔전방, 사거리 1, 공격력 (per*2)+(sen*3)+5
- 원거리공격: 사거리 2~3, 전방→전방 불가, 커버링 체크, 공격력 (per*3)+(sen*2)
- 전장이동: 최대 1 거리, 같은 팀 셀만, 빈칸 확인
- 대기: 특수 효과 적용

---

## 3. 핵심 로직 구현

### 3.1 우선도 계산

```python
def calculate_priority(self, slot, action_type, skill_chain=None):
    player = self.players[slot - 1]
    stats = player['character']['stats']
    
    if action_type == 'melee_attack':
        base_priority = stats['sen'] * 10 + stats['mst']
    elif action_type == 'ranged_attack':
        base_priority = stats['per'] * 10 + stats['mst']
    elif action_type == 'battlefield_move':
        base_priority = (stats['sen'] + stats['per']) * 5 + stats['mst']
    elif action_type == 'wait':
        base_priority = 100 + stats['mst']
    
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

def check_move_validity(self, from_pos: str, to_pos: str, player_team: int) -> tuple[bool, str]:
    fr, fc = self.pos_to_rc(from_pos)
    tr, tc = self.pos_to_rc(to_pos)
    
    row_dist = abs(fr - tr)
    col_dist = abs(fc - tc)
    
    if row_dist > 1 or col_dist > 1:
        return False, "이동 거리 초과"
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

### 3.6 행동 해결

```python
def resolve_action(self, action_data):
    slot = action_data['slot']
    action_type = action_data['action_type']
    player = self.players[slot - 1]
    attacker_pos = player['character']['pos']
    
    result = {'slot': slot, 'action_type': action_type, 'success': False, 'message': '', 'damage_dealt': 0, 'target_hp_after': None}
    
    if action_type in ['melee_attack', 'ranged_attack']:
        target_pos = action_data.get('target')
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
        target_slot = action_data.get('target_slot')
        
        if target_slot:
            target_char = self.players[target_slot - 1]['character']
            damage = attack_power
            target_char['current_hp'] = max(0, target_char['current_hp'] - damage)
            return {**result, 'success': True, 'damage_dealt': damage, 'target_hp_after': target_char['current_hp']}
    
    elif action_type == 'battlefield_move':
        move_to = action_data.get('move_to')
        if not move_to:
            return {**result, 'message': "목적지 미지정"}
        
        move_ok, move_msg = self.check_move_validity(attacker_pos, move_to, player['team'])
        if not move_ok:
            return {**result, 'message': move_msg}
        
        old_pos = attacker_pos
        player['character']['pos'] = move_to
        self.combat_board[old_pos] = None
        self.combat_board[move_to] = {'slot': slot, 'name': player['character']['name'], 'team': player['team']}
        return {**result, 'success': True, 'message': f"{old_pos}→{move_to}"}
    
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

def get_valid_move_tiles(self, slot):
    player = self.players[slot - 1]
    from_pos = player['character']['pos']
    player_team = player['team']
    if not from_pos:
        return []
    
    valid_tiles = []
    fr, fc = self.pos_to_rc(from_pos)
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            tr, tc = fr + dr, fc + dc
            if 0 <= tr < 4 and 0 <= tc < 4:
            to_pos = self.rc_to_pos(tr, tc)
                if self.check_move_validity(from_pos, to_pos, player_team)[0]:
                valid_tiles.append(to_pos)
    return valid_tiles

def get_tile_feedback(self, slot, action_type=None):
    result = {'valid_attack_tiles': [], 'valid_move_tiles': []}
    if action_type in ['melee_attack', 'ranged_attack']:
        result['valid_attack_tiles'] = self.get_valid_attack_tiles(slot, action_type)
    if action_type == 'battlefield_move' or action_type is None:
        result['valid_move_tiles'] = self.get_valid_move_tiles(slot)
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


**사용 예시:**

1. **전투 시작**: 
   - `start_combat()` 호출 (phase = 'position_declaration'로 설정)
   - `get_combat_start_message()` → '전투를 시작합니다.'
   - `start_position_declaration_phase()` → '위치 선언 페이즈입니다. 시작 위치를 선언해주세요.'

2. **위치 선언 완료**: 
   - `resolve_position_declarations()` 완료 후
   - `start_action_declaration_phase()` → '라운드 {} 선언 페이즈입니다. 스킬과 행동을 선언해주세요.'.format(1), round = 1

3. **행동 선언 완료**: 
   - `check_all_declarations_complete()` 완료 후
   - `start_resolution_phase()` → '라운드 {} 선언이 끝났습니다. 계산을 시작합니다.'.format(current_round)

4. **해결 완료**: 
   - `resolve_all_actions()` 완료 후
   - `end_round()` → '라운드 {} 결과를 요약합니다.'.format(current_round) → 다음 라운드 action_declaration 또는 전투 종료

**WebSocket 통합 (PLAN_WEBSOCKET.md 참고):**

```python
# game_ws.py 예시
result = game.advance_combat_phase('action_declaration')
if result['success']:
    await conmanager.broadcast_to_game(game.id, {
        "type": result['notification_type'],
        "phase": result['phase'],
        "round": result['round'],
        "message": result['message'],
        **result['additional_data']
    })
```

**참고사항:**

- 모든 메시지는 함수 내에서 하드코딩된 문자열로 정의됩니다.
- 라운드 번호가 필요한 메시지는 `.format()`을 사용하여 동적으로 생성됩니다.
- `advance_combat_phase()`는 실제 phase 전환을 담당하며, 메시지와 notification_type을 반환합니다.
- `get_round_summary_message()`는 phase를 변경하지 않고 메시지만 반환합니다 (라운드 종료 시).
- 실제 WebSocket 전송은 `game_ws.py`에서 처리합니다 (PLAN_WEBSOCKET.md 참고).

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

**버팅 규칙**: 같은 위치 선언 시 나중 선언자가 인접 빈칸(없으면 전체 빈칸)으로 이동

---

## 5. 구현 단계

### Phase 1: 데이터 구조 확장

1. `Game.__init__()`에 `combat_state`, `combat_board`, `timer` 추가
2. 캐릭터 데이터에 `max_hp` 필드 추가

### Phase 2: 핵심 계산 함수

1. `calculate_priority()`, `calculate_attack_power()`
2. 좌표 헬퍼: `pos_to_rc()`, `rc_to_pos()`, `is_front_row()`, `is_back_row()`
3. `check_range()`, `check_covering()`, `check_move_validity()`
4. `get_valid_attack_tiles()`, `get_valid_move_tiles()`, `get_tile_feedback()`
5. `calculate_max_hp()`, `initialize_character_hp()`

### Phase 3: 전투 플로우

1. `start_combat()`: phase = 'position_declaration'
2. 위치 선언: `parse_position_declaration_from_chat()`, `resolve_position_declarations()` (채팅 파싱은 PLAN_WEBSOCKET.md 참고)
3. 행동 선언: `start_action_declaration_phase()`, `parse_action_declaration_from_chat()`, 타이머 처리 (채팅 파싱은 PLAN_WEBSOCKET.md 참고)
4. 우선도 계산: `calculate_all_priorities()`, `action_queue` 정렬
5. 행동 해결: `resolve_action()`
6. 라운드 종료: `end_round()`, 전투 불능/승리 조건 체크

