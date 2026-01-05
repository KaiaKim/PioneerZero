# 전투 시스템 구현 계획 (Combat System Implementation Plan)

## 개요 (Overview)

이 문서는 제공된 게임 기획서를 `game_core.py`에 적용하기 위한 데이터 플로우 계획과 구현 지침을 담고 있습니다.

This document outlines the data flow plan and implementation instructions for applying the game design document to `game_core.py`.

---

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
    "debuffs": [],     # 디버프 리스트 (중첩 가능)
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
        # Row 0: Y1, Y2, Y3, Y4 (후방)
        # Row 1: X1, X2, X3, X4 (전방)
        # Row 2: A1, A2, A3, A4 (전방)
        # Row 3: B1, B2, B3, B4 (후방)
        self.combat_board = {
            'Y1': None, 'Y2': None, 'Y3': None, 'Y4': None,
            'X1': None, 'X2': None, 'X3': None, 'X4': None,
            'A1': None, 'A2': None, 'A3': None, 'A4': None,
            'B1': None, 'B2': None, 'B3': None, 'B4': None
        }
```

### 1.3 행동 데이터 구조 (Action Data Structure)

```python
action_data = {
    'slot': 1,                    # 플레이어 슬롯 번호
    'action_type': 'melee_attack', # 'melee_attack', 'ranged_attack', 'battlefield_move', 'wait'
    'skill_chain': None,          # 체인된 스킬 이름 (없으면 None)
    'target': 'X2',              # 대상 위치 또는 None
    'target_slot': 2,            # 대상 플레이어 슬롯 (선택적)
    'move_to': 'A2',             # 이동 행동의 경우 목적지
    'priority': 44,               # 계산된 우선도
    'attack_power': 12,          # 계산된 공격력
    'resolved': False            # 처리 완료 여부
}
```

### 1.4 디버프 데이터 구조 (Debuff Data Structure)

```python
debuff = {
    'type': 'burning',      # 'burning', 'shocked', 'wet', 'frozen', 'entangled'
    'value': 0,             # 디버프 수치 (shocked의 경우 공격력 감소량)
    'applied_round': 1,     # 적용된 라운드 (선입선출 정렬용)
    'duration': 'permanent' # 'permanent' 또는 턴 수
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
   - 모든 플레이어가 비밀 제출
   - action_declarations에 저장
   - 모두 제출 완료 대기
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
Phase 4: Debuff Application (디버프 적용)
   - 모든 디버프 효과 적용 (화상, 빙결 등)
   - 디버프 지속 시간 감소
   ↓
Phase 5: Round End (라운드 종료)
   - 전투 불능 체크
   - 승리 조건 체크
   - 다음 라운드로 진행 또는 전투 종료
```

### 2.3 행동 선언 플로우 (Action Declaration Flow)

```
클라이언트 → 서버: action_declare 메시지
{
    "action": "action_declare",
    "game_id": "game123",
    "slot": 1,
    "action_type": "melee_attack",
    "skill_chain": "순간가속",  // 선택적
    "target": "X2"
}
   ↓
서버: action_declarations[slot] = action_data 저장
   ↓
서버: 모든 플레이어 제출 확인
   ↓
모두 제출 완료 시 → Priority Calculation 단계로 이동
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
   1. 사거리 확인 (전방↔전방)
   2. 커버링 체크
   3. 공격력 계산: (인지*2) + (감각*3) + 5
   4. 스킬 체인 보정 적용
   5. 대미지 적용
   6. 디버프 부여 (해당 스킬의 경우)
   ↓
[원거리공격]
   1. 사거리 확인 (후방↔후방)
   2. 커버링 체크 (중요!)
   3. 공격력 계산: (인지*3) + (감각*2)
   4. 스킬 체인 보정 적용
   5. 대미지 적용
   6. 디버프 부여
   ↓
[전장이동]
   1. 이동 가능 여부 확인 (속박 디버프 체크)
   2. 목적지 유효성 확인
   3. 위치 업데이트
   4. combat_board 업데이트
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
    if skill_chain == '순간가속':
        base_priority += stats['mst'] * 20
    
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
    if skill_chain == '예열':
        base_power += stats['tal']  # 재능 보정
    elif skill_chain == '노심융해':
        base_power += stats['tal'] * 2
    
    # 디버프 보정 (shocked)
    for debuff in player['character'].get('debuffs', []):
        if debuff['type'] == 'shocked':
            base_power -= debuff['value']
    
    return max(0, base_power)  # 음수 방지
```

### 3.3 커버링 체크 함수 (Covering Check Function)

```python
def check_covering(self, attacker_pos, target_pos, attacker_team):
    """원거리 공격 시 커버링 체크"""
    # 근거리 공격은 커버링 없음
    # 원거리 공격만 체크
    
    # 전방/후방 확인
    front_positions = ['X1', 'X2', 'X3', 'X4', 'A1', 'A2', 'A3', 'A4']
    back_positions = ['Y1', 'Y2', 'Y3', 'Y4', 'B1', 'B2', 'B3', 'B4']
    
    attacker_is_back = attacker_pos in back_positions
    target_is_back = target_pos in back_positions
    
    # 원거리 공격은 후방↔후방만 가능
    if not (attacker_is_back and target_is_back):
        return False, "원거리 공격은 후방에서만 가능합니다"
    
    # 같은 열(column)에서 공격자와 목표 사이에 다른 캐릭터가 있는지 확인
    attacker_col = attacker_pos[1]  # 'Y2' -> '2'
    target_col = target_pos[1]
    
    if attacker_col != target_col:
        return True, None  # 다른 열이면 커버링 없음
    
    # 같은 열에서 사이에 있는지 확인
    attacker_row_idx = self._get_row_index(attacker_pos)
    target_row_idx = self._get_row_index(target_pos)
    
    # 사이의 위치들 확인
    min_row = min(attacker_row_idx, target_row_idx)
    max_row = max(attacker_row_idx, target_row_idx)
    
    for row in range(min_row + 1, max_row):
        pos = self._get_position_from_index(row, int(attacker_col))
        occupant = self.combat_board.get(pos)
        
        if occupant and occupant['team'] != attacker_team:
            return False, f"{pos}에 있는 {occupant['name']}이(가) 커버링 중입니다"
    
    return True, None

def _get_row_index(self, pos):
    """위치를 행 인덱스로 변환"""
    row_map = {'Y': 0, 'X': 1, 'A': 2, 'B': 3}
    return row_map.get(pos[0], -1)

def _get_position_from_index(self, row, col):
    """행 인덱스와 열로 위치 반환"""
    row_map = {0: 'Y', 1: 'X', 2: 'A', 3: 'B'}
    return f"{row_map.get(row, '?')}{col}"
```

### 3.4 디버프 적용 함수 (Debuff Application Function)

```python
def apply_debuffs(self, slot):
    """라운드 종료 시 디버프 효과 적용"""
    player = self.players[slot - 1]
    character = player['character']
    debuffs = character.get('debuffs', [])
    
    total_damage = 0
    
    for debuff in debuffs:
        if debuff['type'] == 'burning':
            # 매 턴 2d4 대미지
            damage = random.randint(1, 4) + random.randint(1, 4)
            total_damage += damage
        
        elif debuff['type'] == 'frozen' and self._has_debuff(debuffs, 'wet'):
            # 빙결 + 젖음 = 매 턴 4d4 대미지
            damage = sum([random.randint(1, 4) for _ in range(4)])
            total_damage += damage
        
        elif debuff['type'] == 'wet' and self._has_debuff(debuffs, 'frozen'):
            # 이미 위에서 처리됨
            pass
    
    # 대미지 적용
    if total_damage > 0:
        character['current_hp'] = max(0, character['current_hp'] - total_damage)
    
    return total_damage

def _has_debuff(self, debuffs, debuff_type):
    """디버프 리스트에 특정 타입이 있는지 확인"""
    return any(d['type'] == debuff_type for d in debuffs)
```

### 3.5 체력 계산 함수 (HP Calculation Function)

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

## 4. WebSocket 메시지 프로토콜 (WebSocket Message Protocol)

### 4.1 클라이언트 → 서버 메시지 (Client → Server Messages)

#### 전투 시작 위치 선언
```json
{
    "action": "declare_start_position",
    "game_id": "game123",
    "slot": 1,
    "position": "A1"
}
```

#### 행동 선언
```json
{
    "action": "action_declare",
    "game_id": "game123",
    "slot": 1,
    "action_type": "melee_attack",
    "skill_chain": "순간가속",
    "target": "X2",
    "target_slot": 2
}
```

#### 이동 행동 선언
```json
{
    "action": "action_declare",
    "game_id": "game123",
    "slot": 1,
    "action_type": "battlefield_move",
    "move_to": "A2"
}
```

#### 대기 행동 선언
```json
{
    "action": "action_declare",
    "game_id": "game123",
    "slot": 1,
    "action_type": "wait",
    "skill_chain": "컨토션"
}
```

### 4.2 서버 → 클라이언트 메시지 (Server → Client Messages)

#### 전투 시작 알림
```json
{
    "type": "combat_started",
    "round": 1,
    "combat_board": {
        "A1": {"slot": 1, "name": "Pikita"},
        "X2": {"slot": 2, "name": "Enemy"}
    }
}
```

#### 행동 선언 요청
```json
{
    "type": "action_declaration_phase",
    "round": 1,
    "time_limit": 60
}
```

#### 우선도 계산 완료 및 해결 시작
```json
{
    "type": "action_resolution_start",
    "round": 1,
    "action_queue": [
        {
            "slot": 1,
            "action_type": "wait",
            "priority": 104
        },
        {
            "slot": 2,
            "action_type": "melee_attack",
            "priority": 44
        }
    ]
}
```

#### 행동 해결 결과
```json
{
    "type": "action_resolved",
    "slot": 2,
    "action_type": "melee_attack",
    "target": "A1",
    "attack_power": 12,
    "damage_dealt": 12,
    "target_hp_after": 18,
    "debuffs_applied": []
}
```

#### 라운드 종료
```json
{
    "type": "round_end",
    "round": 1,
    "debuff_damage": {
        "1": 5,
        "2": 0
    },
    "next_round": 2
}
```

#### 전투 종료
```json
{
    "type": "combat_end",
    "winner_team": 0,
    "final_state": {
        "players": [...]
    }
}
```

---

## 5. 구현 단계 (Implementation Steps)

### Phase 1: 데이터 구조 확장 (Data Structure Extension)

1. **`server/game_core.py` 수정**
   - `Game.__init__()`에 `combat_state` 추가
   - `combat_board` 딕셔너리 추가
   - 캐릭터 데이터에 `debuffs`, `max_hp` 필드 추가

2. **`server/game_bot.py` 수정**
   - 캐릭터 초기화 시 `max_hp` 계산
   - `debuffs` 리스트 초기화

### Phase 2: 핵심 계산 함수 구현 (Core Calculation Functions)

1. **우선도 계산 함수**
   - `calculate_priority()` 구현
   - 스킬 체인 보정 로직 포함

2. **공격력 계산 함수**
   - `calculate_attack_power()` 구현
   - 디버프 보정 포함

3. **커버링 체크 함수**
   - `check_covering()` 구현
   - 위치 기반 로직

4. **체력 계산 함수**
   - `calculate_max_hp()` 구현
   - `initialize_character_hp()` 구현

### Phase 3: 전투 플로우 구현 (Combat Flow Implementation)

1. **전투 시작 함수**
   - `start_combat()` 구현
   - 시작 위치 선언 처리
   - 보드 초기화

2. **행동 선언 함수**
   - `declare_action()` 구현
   - 선언 검증
   - 모든 플레이어 제출 대기

3. **우선도 계산 및 정렬**
   - `calculate_all_priorities()` 구현
   - `action_queue` 정렬

4. **행동 해결 함수**
   - `resolve_action()` 구현
   - 각 행동 타입별 처리
   - 대미지 적용
   - 디버프 부여

5. **라운드 종료 함수**
   - `end_round()` 구현
   - 디버프 효과 적용
   - 전투 불능 체크
   - 승리 조건 체크

### Phase 4: WebSocket 핸들러 구현 (WebSocket Handler Implementation)

1. **`server/game_ws.py`에 핸들러 추가**
   - `handle_declare_start_position()`
   - `handle_action_declare()`
   - `handle_start_combat()` (GM용)

2. **브로드캐스트 함수**
   - `broadcast_combat_state()`
   - `broadcast_action_resolution()`

### Phase 5: 스킬 시스템 구현 (Skill System Implementation)

1. **스킬 데이터 구조 정의**
   - 스킬별 효과 정의
   - 우선도/공격력 보정 매핑

2. **스킬 체인 처리**
   - 스킬 효과 적용 로직
   - 특수 효과 처리 (회피, 넉백 등)

3. **스킬별 특수 로직**
   - 유도탄 (커버링 무시)
   - 컨토션 (회피)
   - 순간가속 (우선도 증가)
   - 등등...

### Phase 6: 디버프 시스템 구현 (Debuff System Implementation)

1. **디버프 적용 함수**
   - `apply_debuff()` 구현
   - 중첩 처리

2. **디버프 효과 함수**
   - `apply_debuffs()` 구현 (라운드 종료 시)
   - 각 디버프 타입별 효과

3. **디버프 해제 함수**
   - `remove_debuff()` 구현
   - 수복 스킬 연동

### Phase 7: 프론트엔드 통합 (Frontend Integration)

1. **`src/hooks/useGame.js` 확장**
   - 전투 상태 관리
   - 행동 선언 함수
   - 전투 보드 상태

2. **`src/components/room/` 컴포넌트 수정**
   - 행동 선언 UI
   - 전투 보드 표시
   - 우선도/해결 결과 표시

---

## 6. 스킬 상세 구현 가이드 (Skill Implementation Guide)

### 6.1 스킬 데이터 구조 (Skill Data Structure)

```python
SKILLS = {
    '유도탄': {
        'type': 'psychic',
        'attribute': 'telekinesis',
        'level': 1,
        'effect': 'ignore_covering',
        'requires_proficiency_check': True
    },
    '순간가속': {
        'type': 'physical',
        'attribute': 'superspeed',
        'level': 1,
        'priority_bonus': lambda mst: mst * 20,
        'effect': 'priority_boost'
    },
    '컨토션': {
        'type': 'physical',
        'attribute': 'mutation',
        'level': 1,
        'effect': 'dodge',
        'requires_proficiency_check': True,
        'success_rate_decrease': True  # 연속 사용 시 확률 감소
    },
    # ... 기타 스킬들
}
```

### 6.2 스킬 체인 처리 로직 (Skill Chain Processing Logic)

```python
def apply_skill_chain(self, action_data, skill_name):
    """스킬 체인 효과 적용"""
    skill = SKILLS.get(skill_name)
    if not skill:
        return action_data
    
    player = self.players[action_data['slot'] - 1]
    stats = player['character']['stats']
    
    # 우선도 보정
    if skill.get('priority_bonus'):
        bonus = skill['priority_bonus'](stats['mst'])
        action_data['priority'] += bonus
    
    # 공격력 보정
    if skill.get('attack_power_bonus'):
        bonus = skill['attack_power_bonus'](stats)
        action_data['attack_power'] += bonus
    
    # 특수 효과
    if skill.get('effect') == 'ignore_covering':
        action_data['ignore_covering'] = True
    
    return action_data
```

---

## 7. 주의사항 및 고려사항 (Notes and Considerations)

### 7.1 용어 정리 (Terminology)
- **Resolution**: '해결' 또는 '계산' (해상도가 아님)
- **Priority**: 우선도 (행동 순서 결정)
- **Covering**: 커버링 (원거리 공격 차단)

### 7.2 게임 밸런스 (Game Balance)
- 우선도 계산식이 게임플레이에 큰 영향을 미침
- 디버프 중첩 시스템이 복잡할 수 있음
- 스킬 체인 조합이 강력할 수 있음

### 7.3 성능 고려사항 (Performance Considerations)
- 모든 플레이어의 행동 선언을 기다리는 동안 타임아웃 필요
- 우선도 계산은 빠르게 처리되어야 함
- 브로드캐스트 메시지 최적화

### 7.4 테스트 시나리오 (Test Scenarios)
1. 기본 근거리/원거리 공격
2. 커버링 시스템 테스트
3. 스킬 체인 조합 테스트
4. 디버프 중첩 테스트
5. 전투 불능 처리 테스트
6. 승리 조건 테스트

---

## 8. 다음 단계 (Next Steps)

1. 이 문서를 기반으로 `game_core.py` 확장 시작
2. 각 Phase별로 단계적 구현 및 테스트
3. 프론트엔드와의 통합 테스트
4. 게임 밸런스 조정
5. 추가 스킬 효과 구현

---

## 부록: 스킬 목록 매핑 (Appendix: Skill List Mapping)

| 기획서 스킬명 | 영문명 (코드용) | 타입 | 속성 | 레벨 |
|------------|--------------|------|------|------|
| 유도탄 | GuidedMissile | psychic | telekinesis | 1 |
| 순간가속 | InstantAcceleration | physical | superspeed | 1 |
| 컨토션 | Contortion | physical | mutation | 1 |
| 예열 | Preheat | physical | tokamak | 2 |
| 수복 | Repair | pure | - | 2 |
| ... | ... | ... | ... | ... |

*이 매핑은 구현 시 확장 및 수정될 수 있습니다.*

