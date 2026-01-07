# 전투 시스템 구현 계획 (Combat System Implementation Plan)



## 1. 데이터 구조 (Data Structures)

### 1.1 캐릭터 데이터 확장 (Character Data Extension)

현재 `game_bot.py`의 캐릭터 구조를 확장해야 합니다:

```python
character = {
    "name": "Pikita",
    "profile_image": "/images/pikita_profile.png",
    "token_image": "/images/pikita_token.png",
    "stats": {
        "vtl": 4,    # 활력 (Vitality)
        "sen": 1,    # 감각 (Sense)
        "per": 1,    # 인지 (Perception)
        "tal": 2,    # 재능 (Talent)
        "mst": 2     # 숙련 (Mastery/Proficiency)
    },
    "class": "physical",
    "type": "none",
    "skills": ["Medikit", "Acceleration", "Contortion"],
    "current_hp": 30,  # 활력*5+10 = 4*5+10 = 30
    "max_hp": 30,      # 활력*5+10
    "pos": "A1",       # 전투 시작 위치
    "team": 0          # 0=white, 1=blue
}
```

### 1.2 전투 상태 데이터 (Combat State Data)

`Game` 클래스에 추가할 전투 관련 속성:

```python
class Game():
    def __init__(self, id, player_num=4):
        # ... 기존 코드 ...
        
        # 전투 상태
        self.combat_state = {
            'in_combat': False,           # 전투 중 여부
            'current_round': 0,           # 현재 라운드
            'phase': 'preparation',       # 'preparation', 'action_declaration', 'resolution', 'end'
            'action_declarations': {},    # {slot: action_data}
            'action_queue': [],           # 우선도 순으로 정렬된 행동 큐
            'resolved_actions': []        # 처리된 행동 기록
        }
        
        # 전투 보드 (4x4 그리드)
        # 좌표 표준화: 서버 내부는 (row_idx, col_idx)로 관리
        # row_idx: 0=Y(후방), 1=X(전방), 2=A(전방), 3=B(후방)
        # col_idx: 0=1, 1=2, 2=3, 3=4
        # 표시는 "Y1", "X2" 등의 문자열로 변환
        # 팀 구분: XY = team 1 (blue), AB = team 0 (white)
        self.combat_board = {
            'Y1': None, 'Y2': None, 'Y3': None, 'Y4': None,  # row 0 (후방, team 1)
            'X1': None, 'X2': None, 'X3': None, 'X4': None,  # row 1 (전방, team 1)
            'A1': None, 'A2': None, 'A3': None, 'A4': None,  # row 2 (전방, team 0)
            'B1': None, 'B2': None, 'B3': None, 'B4': None   # row 3 (후방, team 0)
        }
        
        # 타이머 상태 (행동 선언 단계용, TIMER_PLAN.md 참고)
        self.timer = {
            'type': None,                 # 'action_declaration', 'session', etc.
            'start_time': None,           # Unix timestamp when timer started
            'duration': None,             # Duration in seconds (60 for action_declaration)
            'is_running': False,          # Whether timer is currently running
            'paused_at': None,             # Unix timestamp when paused
            'elapsed_before_pause': 0     # Accumulated elapsed time before pause
        }
```

### 1.3 행동 데이터 구조 (Action Data Structure)

```python
action_data = {
    'slot': 1,                    # 플레이어 슬롯 번호
    'action_type': 'melee_attack', # 'melee_attack', 'ranged_attack', 'battlefield_move', 'wait'
    'skill_chain': None,          # 체인된 스킬 ID (skill_id, 없으면 None)
    'target': 'X2',              # 대상 위치 또는 None
    'target_slot': 2,            # 대상 플레이어 슬롯 (선택적)
    'move_to': 'A2',             # 이동 행동의 경우 목적지
    'priority': 44,               # 계산된 우선도
    'attack_power': 12,          # 계산된 공격력
    'resolved': False            # 처리 완료 여부
}
```

---

## 2. 데이터 플로우 (Data Flow)

### 2.1 전투 시작 플로우 (Combat Start Flow)

```
1. GM이 전투 시작 명령
   ↓
2. 모든 플레이어에게 시작 위치 선언 요청
   ↓
3. 각 플레이어가 자신의 진영(A~B 또는 X~Y)에서 위치 선택
   ↓
4. 서버가 위치 검증 및 토큰 배치
   ↓
5. combat_state['in_combat'] = True
   combat_state['phase'] = 'preparation'
   combat_state['current_round'] = 1
   ↓
6. 모든 클라이언트에 전투 시작 알림 브로드캐스트
```

### 2.2 라운드 플로우 (Round Flow)

```
라운드 시작
   ↓
Phase 1: Action Declaration (행동 선언)
   - 60초 타이머 시작 (서버에서 브로드캐스트)
   - 모든 플레이어가 비밀 제출
   - action_declarations에 저장
   - 모두 제출 완료 또는 시간 초과 대기
   - 타이머는 1초마다 모든 클라이언트에 업데이트 브로드캐스트
   ↓
Phase 2: Priority Calculation (우선도 계산)
   - 각 행동의 우선도 계산
   - action_queue에 우선도 순으로 정렬
   ↓
Phase 3: Resolution (해결/계산)
   - action_queue에서 순차적으로 처리
   - 각 행동 실행 및 결과 계산
   - resolved_actions에 기록
   ↓
Phase 4: Round End (라운드 종료)
   - 전투 불능 체크
   - 승리 조건 체크
   - 다음 라운드로 진행 또는 전투 종료
```

### 2.3 행동 선언 플로우 (Action Declaration Flow)

```
1. 행동 선언 단계 시작
   - 서버: 60초 타이머 시작 (timer_type='action_declaration', duration=60)
   - 서버: 모든 클라이언트에 action_declaration_phase 메시지 브로드캐스트
   - 서버: 백그라운드 태스크가 1초마다 타이머 업데이트 브로드캐스트
   ↓
2. 클라이언트 → 서버: action_declare 메시지
{
    "action": "action_declare",
    "game_id": "game123",
    "slot": 1,
    "action_type": "melee_attack",
    "skill_chain": "instant_acceleration",  // 스킬 ID (선택적)
    "target": "X2"
}
   ↓
3. 서버: action_declarations[slot] = action_data 저장
   ↓
4. 서버: 모든 플레이어 제출 확인
   ↓
5. 종료 조건:
   - 모두 제출 완료 → 타이머 중지 → Priority Calculation 단계로 이동
   - 시간 초과 (60초) → 미제출 플레이어는 자동으로 '대기' 행동 처리 → Priority Calculation 단계로 이동
```

### 2.4 우선도 계산 플로우 (Priority Calculation Flow)

```
각 행동에 대해:
   ↓
1. 기본 우선도 계산
   - 근거리공격: 감각*10 + 숙련
   - 원거리공격: 인지*10 + 숙련
   - 전장이동: (감각+인지)*5 + 숙련
   - 대기: 100 + 숙련
   ↓
2. 스킬 체인 보정 적용
   - 순간가속: 우선도 + 숙련*20
   - 기타 스킬 보정
   ↓
3. action_queue에 우선도 내림차순 정렬
   ↓
4. Resolution 단계로 이동
```

### 2.5 행동 해결 플로우 (Action Resolution Flow)

```
action_queue에서 순차 처리:
   ↓
각 행동 타입별 처리:
   ↓
[근거리공격]
   1. 사거리 확인 (전방↔전방, 사거리 1)
   2. 커버링 체크 (근거리는 커버링 없음)
   3. 공격력 계산: (인지*2) + (감각*3) + 5
   4. 스킬 체인 보정 적용
   5. 대미지 적용
   ↓
[원거리공격]
   1. 사거리 확인 (사거리 2~3, 전방→전방 불가)
      - 후방→후방: OK (사거리 2~3)
      - 전방→후방: OK (사거리 2)
      - 후방→전방: OK (사거리 2)
      - 전방→전방: NO (사거리 1)
   2. 커버링 체크 (중요!)
   3. 공격력 계산: (인지*3) + (감각*2)
   4. 스킬 체인 보정 적용
   5. 대미지 적용
   ↓
[전장이동]
   1. 이동 거리 확인
   3. 목적지 유효성 확인
   4. 위치 업데이트
   5. combat_board 업데이트
   ↓
[대기]
   1. 특수 효과 적용 (컨토션 등)
   2. 다음 공격 회피 준비
   ↓
resolved_actions에 기록
```

---

## 3. 핵심 로직 구현 (Core Logic Implementation)

### 3.1 우선도 계산 함수 (Priority Calculation Function)

```python
def calculate_priority(self, slot, action_type, skill_chain=None):
    """행동의 우선도를 계산"""
    player = self.players[slot - 1]
    stats = player['character']['stats']
    
    base_priority = 0
    
    if action_type == 'melee_attack':
        base_priority = stats['sen'] * 10 + stats['mst']
    elif action_type == 'ranged_attack':
        base_priority = stats['per'] * 10 + stats['mst']
    elif action_type == 'battlefield_move':
        base_priority = (stats['sen'] + stats['per']) * 5 + stats['mst']
    elif action_type == 'wait':
        base_priority = 100 + stats['mst']
    
    # 스킬 체인 보정
    if skill_chain:
        from server.skills import SKILLS
        skill = SKILLS.get(skill_chain)
        if skill and skill.get('priority_mod'):
            if callable(skill['priority_mod']):
                bonus = skill['priority_mod'](stats)
            else:
                bonus = skill['priority_mod']
            base_priority += bonus
    
    return base_priority
```

### 3.2 공격력 계산 함수 (Attack Power Calculation Function)

```python
def calculate_attack_power(self, slot, action_type, skill_chain=None):
    """공격력을 계산"""
    player = self.players[slot - 1]
    stats = player['character']['stats']
    
    base_power = 0
    
    if action_type == 'melee_attack':
        base_power = (stats['per'] * 2) + (stats['sen'] * 3) + 5
    elif action_type == 'ranged_attack':
        base_power = (stats['per'] * 3) + (stats['sen'] * 2)
    
    # 스킬 체인 보정
    if skill_chain:
        from server.skills import SKILLS
        skill = SKILLS.get(skill_chain)
        if skill and skill.get('power_mod'):
            if callable(skill['power_mod']):
                bonus = skill['power_mod'](stats)
            else:
                bonus = skill['power_mod']
            base_power += bonus
    
    return max(0, base_power)  # 음수 방지
```

### 3.3 좌표 표준화 헬퍼 함수 (Coordinate Standardization Helpers)

```python
# 좌표 표준화: 서버 내부는 row_idx, col_idx로 통일, 표시만 "Y1" 형태로 변환
ROW_MAP = {"Y": 0, "X": 1, "A": 2, "B": 3}
REV_ROW_MAP = {v: k for k, v in ROW_MAP.items()}

def pos_to_rc(self, pos: str) -> tuple[int, int]:
    """위치 문자열("Y1")을 (row_idx, col_idx)로 변환"""
    r = ROW_MAP.get(pos[0], -1)
    c = int(pos[1]) - 1  # "1" -> 0, "2" -> 1, etc.
    return r, c

def rc_to_pos(self, r: int, c: int) -> str:
    """(row_idx, col_idx)를 위치 문자열("Y1")로 변환"""
    row_char = REV_ROW_MAP.get(r, '?')
    return f"{row_char}{c + 1}"

def is_front_row(self, pos: str) -> bool:
    """위치가 전방인지 확인"""
    r, _ = self.pos_to_rc(pos)
    # row == 1 (X) or row == 2 (A): front
    return r == 1 or r == 2

def is_back_row(self, pos: str) -> bool:
    """위치가 후방인지 확인"""
    r, _ = self.pos_to_rc(pos)
    # row == 0 (Y) or row == 3 (B): back
    return r == 0 or r == 3

def check_move_validity(self, from_pos: str, to_pos: str, player_team: int) -> tuple[bool, str]:
    """이동 유효성 확인"""
    # 1. 이동 거리 확인 (최대 1 거리, 대각선 포함)
    fr, fc = self.pos_to_rc(from_pos)
    tr, tc = self.pos_to_rc(to_pos)
    
    row_distance = abs(fr - tr)
    col_distance = abs(fc - tc)
    
    if row_distance > 1 or col_distance > 1:
        return False, f"이동 거리가 너무 깁니다 (최대 1 거리만 가능)"
    
    if row_distance == 0 and col_distance == 0:
        return False, "같은 위치로는 이동할 수 없습니다"
    
    # 2. 목적지가 같은 팀의 셀인지 확인
    # team 0 (white): row 2,3 (A,B)
    # team 1 (blue): row 0,1 (Y,X)
    to_team = 1 if tr <= 1 else 0
    if to_team != player_team:
        return False, "다른 팀의 셀로는 이동할 수 없습니다"
    
    # 3. 목적지가 비어있는지 확인
    if self.combat_board.get(to_pos) is not None:
        return False, f"{to_pos}는 이미 다른 플레이어가가 차지하고 있습니다"
    
    return True, None
```

### 3.4 사거리 체크 함수 (Range Check Function)

```python
def check_range(self, attacker_pos, target_pos, action_type):
    """공격 사거리 확인"""
    # 좌표를 (row_idx, col_idx)로 변환
    ar, ac = self.pos_to_rc(attacker_pos)
    tr, tc = self.pos_to_rc(target_pos)
    
    # 같은 열인지 확인
    if ac != tc:
        return False, "같은 열에 있는 대상만 공격할 수 있습니다"
    
    # 행 간 거리 계산 (절대값)
    row_distance = abs(ar - tr)
    
    if action_type == 'melee_attack':
        # 근거리 공격: 전방↔전방, 사거리 1
        attacker_is_front = self.is_front_row(attacker_pos)
        target_is_front = self.is_front_row(target_pos)
        
        if not (attacker_is_front and target_is_front):
            return False, "근거리 공격은 전방↔전방만 가능합니다"
        
        if row_distance != 1:
            return False, "근거리 공격은 사거리 1만 가능합니다"
        
        return True, None
    
    elif action_type == 'ranged_attack':
        # 원거리 공격: 사거리 2~3, 전방→전방 불가
        attacker_is_front = self.is_front_row(attacker_pos)
        target_is_front = self.is_front_row(target_pos)
        
        # 전방→전방은 불가
        if attacker_is_front and target_is_front:
            return False, "원거리 공격은 전방→전방이 불가능합니다"
        
        # 사거리 확인 (2~3)
        if row_distance < 2 or row_distance > 3:
            return False, f"원거리 공격은 사거리 2~3만 가능합니다 (현재: {row_distance})"
        
        return True, None
    
    return False, "알 수 없는 공격 타입입니다"
```

### 3.5 커버링 체크 함수 (Covering Check Function)

```python
def check_covering(self, attacker_pos, target_pos, attacker_team):
    """원거리 공격 시 커버링 체크"""
    # 근거리 공격은 커버링 없음
    # 원거리 공격만 체크
    
    # 좌표를 (row_idx, col_idx)로 변환
    ar, ac = self.pos_to_rc(attacker_pos)
    tr, tc = self.pos_to_rc(target_pos)
    
    # 같은 열인지 확인
    if ac != tc:
        return True, None  # 다른 열이면 커버링 없음
    
    # 타겟이 후방인지 확인
    if not self.is_back_row(target_pos):
        return True, None  # 타겟이 후방이 아니면 커버링 체크 불필요
    
    # 타겟의 전방 row에 살아있는 플레이어가 있는지 확인
    # 타겟이 Y row(0)면 전방은 X row(1)
    # 타겟이 B row(3)면 전방은 A row(2)
    front_row = 1 if tr == 0 else 2  # Y면 X(1), B면 A(2)
    
    front_pos = self.rc_to_pos(front_row, tc)
    occupant = self.combat_board.get(front_pos)
    
    if occupant and occupant['team'] != attacker_team:
        return False, f"{front_pos}에 있는 {occupant['name']}이(가) 커버링 중입니다"
    
    return True, None
```

### 3.6 행동 해결 함수 (Action Resolution Function)

```python
def resolve_action(self, action_data):
    """행동을 해결하고 결과를 반환"""
    slot = action_data['slot']
    action_type = action_data['action_type']
    player = self.players[slot - 1]
    attacker_pos = player['character']['pos']
    
    result = {
        'slot': slot,
        'action_type': action_type,
        'success': False,
        'message': '',
        'damage_dealt': 0,
        'target_hp_after': None
    }
    
    if action_type in ['melee_attack', 'ranged_attack']:
        target_pos = action_data.get('target')
        if not target_pos:
            result['message'] = "대상이 지정되지 않았습니다"
            return result
        
        # 사거리 체크
        range_ok, range_msg = self.check_range(attacker_pos, target_pos, action_type)
        if not range_ok:
            result['message'] = range_msg
            return result
        
        # 커버링 체크 (원거리 공격만)
        if action_type == 'ranged_attack':
            # 스킬 플래그로 커버링 무시 가능 (예: 유도탄)
            ignore_covering = action_data.get('ignore_covering', False)
            if not ignore_covering:
                covering_ok, covering_msg = self.check_covering(
                    attacker_pos, target_pos, player['team']
                )
                if not covering_ok:
                    result['message'] = covering_msg
                    return result
        
        # 공격력 계산
        attack_power = self.calculate_attack_power(
            slot, action_type, action_data.get('skill_chain')
        )
        action_data['attack_power'] = attack_power
        
        # 대상 찾기
        target_slot = action_data.get('target_slot')
        if target_slot:
            target_player = self.players[target_slot - 1]
            target_character = target_player['character']
            
            # 대미지 적용
            damage = attack_power
            target_character['current_hp'] = max(0, target_character['current_hp'] - damage)
            
            result['success'] = True
            result['damage_dealt'] = damage
            result['target_hp_after'] = target_character['current_hp']
            result['message'] = f"{player['character']['name']}이(가) {target_character['name']}에게 {damage} 대미지"
    
    elif action_type == 'battlefield_move':
        move_to = action_data.get('move_to')
        if not move_to:
            result['message'] = "이동 목적지가 지정되지 않았습니다"
            return result
        
        # 1. 이동 거리 및 유효성 확인
        move_ok, move_msg = self.check_move_validity(
            attacker_pos, move_to, player['team']
        )
        if not move_ok:
            result['message'] = move_msg
            return result
        
        # 3. 위치 업데이트
        old_pos = attacker_pos
        player['character']['pos'] = move_to
        self.combat_board[old_pos] = None
        self.combat_board[move_to] = {
            'slot': slot,
            'name': player['character']['name'],
            'team': player['team']
        }
        
        result['success'] = True
        result['message'] = f"{player['character']['name']}이(가) {old_pos}에서 {move_to}로 이동"
    
    elif action_type == 'wait':
        # 대기 행동 처리
        result['success'] = True
        result['message'] = f"{player['character']['name']}이(가) 대기"
    
    return result
```

### 3.7 유효한 타일 계산 함수 (Valid Tiles Calculation Function)

```python
def get_valid_attack_tiles(self, slot, action_type):
    """공격 가능한 타일 목록 반환 (사거리 기반)"""
    player = self.players[slot - 1]
    attacker_pos = player['character']['pos']
    attacker_team = player['team']
    
    if not attacker_pos:
        return []
    
    valid_tiles = []
    ar, ac = self.pos_to_rc(attacker_pos)
    
    # 같은 열의 모든 타일 확인 (공격은 같은 열만 가능)
    for r in range(4):
        target_pos = self.rc_to_pos(r, ac)
        
        # 같은 위치는 제외
        if target_pos == attacker_pos:
            continue
        
        # 사거리 체크
        range_ok, _ = self.check_range(attacker_pos, target_pos, action_type)
        if not range_ok:
            continue
        
        # 커버링 체크 (원거리 공격만)
        if action_type == 'ranged_attack':
            covering_ok, _ = self.check_covering(attacker_pos, target_pos, attacker_team)
            if not covering_ok:
                continue
        
        # 목표 위치에 적 플레이어가 있는지 확인 (공격 대상 필요)
        target_occupant = self.combat_board.get(target_pos)
        if target_occupant and target_occupant['team'] != attacker_team:
            valid_tiles.append(target_pos)
    
    return valid_tiles

def get_valid_move_tiles(self, slot):
    """이동 가능한 타일 목록 반환 (이동 거리 및 팀 제한 기반)"""
    player = self.players[slot - 1]
    from_pos = player['character']['pos']
    player_team = player['team']
    
    if not from_pos:
        return []
    
    valid_tiles = []
    fr, fc = self.pos_to_rc(from_pos)
    
    # 최대 1 거리 내의 모든 타일 확인 (대각선 포함)
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            # 같은 위치는 제외
            if dr == 0 and dc == 0:
                continue
            
            tr = fr + dr
            tc = fc + dc
            
            # 보드 범위 체크
            if tr < 0 or tr >= 4 or tc < 0 or tc >= 4:
                continue
            
            to_pos = self.rc_to_pos(tr, tc)
            
            # 이동 유효성 체크
            move_ok, _ = self.check_move_validity(from_pos, to_pos, player_team)
            if move_ok:
                valid_tiles.append(to_pos)
    
    return valid_tiles

def get_tile_feedback(self, slot, action_type=None):
    """타일 피드백 정보 반환 (공격/이동 가능한 타일)"""
    result = {
        'valid_attack_tiles': [],
        'valid_move_tiles': []
    }
    
    if action_type in ['melee_attack', 'ranged_attack']:
        result['valid_attack_tiles'] = self.get_valid_attack_tiles(slot, action_type)
    
    if action_type == 'battlefield_move' or action_type is None:
        result['valid_move_tiles'] = self.get_valid_move_tiles(slot)
    
    return result
```

### 3.8 체력 계산 함수 (HP Calculation Function)

```python
def calculate_max_hp(self, vitality):
    """최대 체력 계산: 활력*5+10"""
    return vitality * 5 + 10

def initialize_character_hp(self, slot):
    """캐릭터의 체력을 초기화"""
    player = self.players[slot - 1]
    vitality = player['character']['stats']['vtl']
    max_hp = self.calculate_max_hp(vitality)
    player['character']['max_hp'] = max_hp
    player['character']['current_hp'] = max_hp
```

---

---

## 5. 구현 단계 (Implementation Steps) BACK

### Phase 1: 데이터 구조 확장 (Data Structure Extension)

1. **`server/game_core.py` 수정**
   - `Game.__init__()`에 `combat_state` 추가
   - `combat_board` 딕셔너리 추가
   - 캐릭터 데이터에 `max_hp` 필드 추가

2. **`server/game_bot.py` 수정**
   - 캐릭터 초기화 시 `max_hp` 계산

### Phase 2: 핵심 계산 함수 구현 (Core Calculation Functions)

1. **우선도 계산 함수**
   - `calculate_priority()` 구현
   - 스킬 체인 보정 로직 포함

2. **공격력 계산 함수**
   - `calculate_attack_power()` 구현

3. **좌표 표준화 헬퍼 함수**
   - `pos_to_rc()` 구현 (위치 문자열 → row_idx, col_idx)
   - `rc_to_pos()` 구현 (row_idx, col_idx → 위치 문자열)
   - `is_front_row()`, `is_back_row()` 구현 (전방/후방 판정)

4. **사거리 체크 함수**
   - `check_range()` 구현
   - 근거리: 전방↔전방, 사거리 1
   - 원거리: 사거리 2~3, 전방→전방 불가
   - 좌표 표준화 헬퍼 함수 사용

5. **커버링 체크 함수**
   - `check_covering()` 구현
   - 좌표 표준화 헬퍼 함수 사용
   - 후방 타겟의 전방 row에 플레이어가 있으면 커버링

6. **이동 유효성 체크 함수**
   - `check_move_validity()` 구현
   - 이동 거리 확인 (최대 1, 대각선 포함)
   - 팀 제한 확인 (같은 팀 셀로만 이동 가능, row 기반)
   - 목적지 비어있음 확인

7. **유효한 타일 계산 함수**
   - `get_valid_attack_tiles()` 구현 (사거리 기반)
   - `get_valid_move_tiles()` 구현 (이동 거리 및 팀 제한 기반)
   - `get_tile_feedback()` 구현 (통합 함수)

8. **체력 계산 함수**
   - `calculate_max_hp()` 구현
   - `initialize_character_hp()` 구현

### Phase 3: 전투 플로우 구현 (Combat Flow Implementation)

1. **전투 시작 함수**
   - `start_combat()` 구현
   - 시작 위치 선언 처리
   - 보드 초기화

2. **행동 선언 함수**
   - `start_action_declaration_phase()` 구현
     - 60초 타이머 시작
     - 모든 클라이언트에 행동 선언 단계 시작 알림
   - `declare_action()` 구현
     - 선언 검증
     - action_declarations에 저장
   - `check_all_declarations_complete()` 구현
     - 모든 플레이어 제출 확인
     - 모두 제출 완료 또는 시간 초과 시 다음 단계로 이동
   - `handle_timeout()` 구현
     - 시간 초과 시 미제출 플레이어는 자동으로 '대기' 행동 처리

3. **우선도 계산 및 정렬**
   - `calculate_all_priorities()` 구현
   - `action_queue` 정렬

4. **행동 해결 함수**
   - `resolve_action()` 구현
   - 각 행동 타입별 처리
   - 대미지 적용

5. **라운드 종료 함수**
   - `end_round()` 구현
   - 전투 불능 체크
   - 승리 조건 체크

