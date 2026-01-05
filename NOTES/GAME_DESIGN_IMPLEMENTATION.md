# 게임 기획 적용: Data Flow Plan & Implementation Instructions

## 목차
1. [데이터 구조 설계](#데이터-구조-설계)
2. [게임 플로우](#게임-플로우)
3. [액션 시스템](#액션-시스템)
4. [스킬 시스템](#스킬-시스템)
5. [디버프 시스템](#디버프-시스템)
6. [전투 계산](#전투-계산)
7. [구현 단계별 가이드](#구현-단계별-가이드)

---

## 데이터 구조 설계

### 1. 캐릭터 데이터 구조 확장

현재 `temp_character.py`의 캐릭터 구조를 확장해야 합니다:

```python
character = {
    # 기존 필드
    "name": str,
    "profile_image": str,
    "token_image": str,
    "pos": str,  # "A1", "B2", "X3", "Y4" 등
    
    # 능력치 (기존 vtl, sen, per, tal, mst를 한국어 키로 매핑)
    "stats": {
        "vtl": int,  # 활력 (Vitality)
        "sen": int,  # 감각 (Sense)
        "per": int,  # 인지 (Perception)
        "tal": int,  # 재능 (Talent)
        "mst": int   # 숙련 (Mastery/Proficiency)
    },
    
    # 새로 추가할 필드
    "max_hp": int,  # 활력*5+10으로 계산
    "current_hp": int,
    "team": int,  # 0 또는 1 (white/blue)
    
    # 디버프 리스트 (중첩 가능)
    "debuffs": [
        {
            "type": str,  # "Burning", "Shocked", "Wet", "Frozen", "Entangled"
            "value": int,  # Shocked의 경우 공격력 감소량, 다른 경우는 중첩 횟수
            "applied_round": int  # 적용된 라운드 번호
        }
    ],
    
    # 스킬 목록 (스킬 객체 배열)
    "skills": [
        {
            "name": str,
            "category": str,  # "사이킥", "피지컬", "테라포머", "유형"
            "attribute": str,  # "염동력", "팬텀", "전뇌", "토카막", "초고속", "변이", "무게조작", "변온", "초생장", "퓨어"
            "level": int,  # 1, 2, 3
            "is_passive": bool,  # 패시브 스킬 여부
            "uses_remaining": int  # 극한반복의 경우 (숙/2)회
        }
    ],
    
    # 전투 상태
    "battle_state": {
        "is_knocked_out": bool,  # 전투불능 여부
        "action_declared": bool,  # 이번 라운드 행동 선언 여부
        "action": dict | None,  # 선언한 행동 (아래 Action 구조 참조)
        "last_skill_used": str | None,  # 심화훈련을 위한 마지막 사용 스킬
        "consecutive_skill_uses": int  # 연속 사용 횟수 (심화훈련용)
    }
}
```

### 2. 액션 데이터 구조

```python
action = {
    "type": str,  # "melee_attack", "ranged_attack", "battlefield_movement", "wait"
    "skill_chain": str | None,  # 체인할 스킬 이름 (없으면 None)
    "target": str | None,  # 공격 대상 위치 ("A1", "X3" 등) 또는 이동 목표 위치
    "direction": str | None,  # 이동의 경우: "up", "down", "left", "right", "up-left", "up-right", "down-left", "down-right"
    "priority": int,  # 계산된 우선도
    "attack_power": int,  # 계산된 공격력 (공격인 경우)
    "player_slot": int  # 행동을 선언한 플레이어 슬롯
}
```

### 3. 게임 상태 데이터 구조

`Game` 클래스에 추가할 필드:

```python
class Game:
    # 기존 필드들...
    
    # 전투 관련 새 필드
    self.battle_phase = str  # "setup", "declaration", "resolution", "end"
    self.declared_actions = {}  # {slot: action} - 비밀 제출된 행동들
    self.action_queue = []  # 우선도 순으로 정렬된 행동 큐
    self.round_start_positions = {}  # {slot: position} - 라운드 시작 위치 선언
    self.position_occupancy = {}  # {position: slot} - 위치별 캐릭터 배치
```

---

## 게임 플로우

### Phase 1: 전투 시작 (Setup Phase)

```
1. 전투 시작 신호 수신
2. 모든 플레이어에게 시작 위치 선언 요청
3. 각 플레이어가 자신의 진영(A~B 또는 X~Y) 중 위치 선언
4. 위치 검증 및 배치
5. Phase 2로 전환
```

### Phase 2: 행동 선언 (Declaration Phase)

```
1. 모든 플레이어에게 행동 선언 요청
2. 각 플레이어가 비밀 제출:
   - 행동 타입 선택
   - 스킬 체인 선택 (선택사항)
   - 타겟/목표 위치 선택
3. 모든 플레이어 제출 완료 대기
4. Phase 3로 전환
```

### Phase 3: 우선도 계산 및 정렬 (Priority Calculation)

```
1. 각 선언된 행동에 대해 우선도 계산:
   - 근거리공격: 감각*10 + 숙련
   - 원거리공격: 인지*10 + 숙련
   - 전장이동: (감각+인지)*5 + 숙련
   - 대기: 100 + 숙련
   
2. 스킬 체인이 있는 경우 우선도 보정 적용:
   - 순간가속: +숙련*20
   
3. action_queue를 우선도 내림차순으로 정렬
4. Phase 4로 전환
```

### Phase 4: 행동 계산 (Resolution Phase)

```
1. action_queue를 순회하며 각 행동 처리:
   
   a. 스킬 체인 효과 적용 (해당하는 경우)
   
   b. 행동 타입별 처리:
      - 근거리공격: 사거리 검증 → 커버링 검증 → 공격력 계산 → 대미지 적용
      - 원거리공격: 사거리 검증 → 커버링 검증 → 공격력 계산 → 대미지 적용
      - 전장이동: 이동 가능 여부 검증 → 위치 이동 → 커버링 상태 업데이트
      - 대기: 특수 효과 적용 (컨토션 등)
   
   c. 디버프 턴 종료 처리:
      - Burning: 2d4 대미지
      - Wet + Frozen: 4d4 대미지
   
   d. 전투불능 체크
   
2. 모든 행동 처리 완료 후 Phase 5로 전환
```

### Phase 5: 라운드 종료 (End Phase)

```
1. 디버프 지속성 확인 (모든 디버프는 전투 종료까지 지속)
2. 전투 종료 조건 체크:
   - 한 팀 전원 전투불능
   - 특정 승리 조건 달성
3. 전투 종료가 아니면:
   - current_round += 1
   - Phase 2로 돌아가기
4. 전투 종료면:
   - 결과 처리
   - 게임 종료
```

---

## 액션 시스템

### 1. 우선도 계산 함수

```python
def calculate_action_priority(action: dict, character: dict) -> int:
    """
    행동의 우선도를 계산합니다.
    
    Args:
        action: 행동 딕셔너리
        character: 캐릭터 딕셔너리
    
    Returns:
        계산된 우선도 값
    """
    stats = character["stats"]
    base_priority = 0
    
    if action["type"] == "melee_attack":
        base_priority = stats["sen"] * 10 + stats["mst"]
    elif action["type"] == "ranged_attack":
        base_priority = stats["per"] * 10 + stats["mst"]
    elif action["type"] == "battlefield_movement":
        base_priority = (stats["sen"] + stats["per"]) * 5 + stats["mst"]
    elif action["type"] == "wait":
        base_priority = 100 + stats["mst"]
    
    # 스킬 체인 보정
    if action.get("skill_chain") == "순간가속":
        base_priority += stats["mst"] * 20
    
    return base_priority
```

### 2. 공격력 계산 함수

```python
def calculate_attack_power(action: dict, character: dict) -> int:
    """
    공격 행동의 공격력을 계산합니다.
    
    Args:
        action: 행동 딕셔너리
        character: 캐릭터 딕셔너리
    
    Returns:
        계산된 공격력 값
    """
    stats = character["stats"]
    base_power = 0
    
    if action["type"] == "melee_attack":
        base_power = (stats["per"] * 2) + (stats["sen"] * 3) + 5
    elif action["type"] == "ranged_attack":
        base_power = (stats["per"] * 3) + (stats["sen"] * 2)
    
    # 스킬 체인 보정
    skill_chain = action.get("skill_chain")
    if skill_chain:
        skill_data = get_skill_data(character, skill_chain)
        if skill_data:
            # 스킬별 공격력 보정 적용
            # 예: 노심융해P는 재능*2, 전퇴P는 활력+재능 등
    
    # 디버프 보정
    for debuff in character.get("debuffs", []):
        if debuff["type"] == "Shocked":
            base_power -= debuff["value"]
    
    return max(0, base_power)  # 공격력은 0 이하가 될 수 없음
```

### 3. 사거리 검증

```python
def is_in_range(attacker_pos: str, target_pos: str, attack_type: str) -> bool:
    """
    공격 타입에 따른 사거리 내에 있는지 확인합니다.
    
    Args:
        attacker_pos: 공격자 위치 ("A1", "X3" 등)
        target_pos: 타겟 위치
        attack_type: "melee_attack" 또는 "ranged_attack"
    
    Returns:
        사거리 내에 있으면 True
    """
    # 위치 파싱
    attacker_row = attacker_pos[0]  # 'A', 'B', 'X', 'Y'
    attacker_col = int(attacker_pos[1])
    target_row = target_pos[0]
    target_col = int(target_pos[1])
    
    # 근거리공격: 전방↔전방
    if attack_type == "melee_attack":
        attacker_is_front = attacker_row in ['A', 'X']
        target_is_front = target_row in ['A', 'X']
        return attacker_is_front and target_is_front
    
    # 원거리공격: 후방↔후방
    elif attack_type == "ranged_attack":
        attacker_is_back = attacker_row in ['B', 'Y']
        target_is_back = target_row in ['B', 'Y']
        return attacker_is_back and target_is_back
    
    return False
```

### 4. 커버링 검증

```python
def is_covered(attacker_pos: str, target_pos: str, position_occupancy: dict) -> bool:
    """
    원거리공격 시 타겟이 커버링되어 있는지 확인합니다.
    
    Args:
        attacker_pos: 공격자 위치
        target_pos: 타겟 위치
        position_occupancy: {position: slot} 딕셔너리
    
    Returns:
        커버링되어 있으면 True
    """
    # 원거리공격만 커버링 적용
    # 후방에서 후방을 공격할 때, 타겟 앞에 다른 캐릭터가 있으면 커버링
    
    attacker_row = attacker_pos[0]
    target_row = target_pos[0]
    attacker_col = int(attacker_pos[1])
    target_col = int(target_pos[1])
    
    # 같은 팀인지 확인 (같은 팀은 커버링 안 됨)
    attacker_team = 0 if attacker_row in ['A', 'B'] else 1
    target_team = 0 if target_row in ['A', 'B'] else 1
    if attacker_team == target_team:
        return False
    
    # 원거리공격이 아니면 커버링 없음
    if attacker_row not in ['B', 'Y'] or target_row not in ['B', 'Y']:
        return False
    
    # 타겟의 전방 위치 확인
    if target_row == 'B':
        front_pos = f"A{target_col}"
    else:  # target_row == 'Y'
        front_pos = f"X{target_col}"
    
    # 전방 위치에 다른 캐릭터가 있는지 확인
    return front_pos in position_occupancy and position_occupancy[front_pos] is not None
```

---

## 스킬 시스템

### 1. 스킬 데이터베이스

```python
SKILL_DATABASE = {
    # 사이킥 - 염동력
    "유도탄": {
        "category": "사이킥",
        "attribute": "염동력",
        "level": 1,
        "priority_mod": 0,
        "attack_mod": 0,
        "special": "cover_ignore"  # 커버링 무시 가능
    },
    "역장": {
        "category": "사이킥",
        "attribute": "염동력",
        "level": 2
    },
    "조종": {
        "category": "사이킥",
        "attribute": "염동력",
        "level": 2
    },
    "싱크홀P": {
        "category": "사이킥",
        "attribute": "염동력",
        "level": 3,
        "attack_mod": 0,
        "special": "horizontal_splash"  # 가로 스플래시
    },
    
    # 사이킥 - 팬텀
    "도깨비불": {
        "category": "사이킥",
        "attribute": "팬텀",
        "level": 1,
        "debuff": "LED"  # 특수 상태
    },
    "액토플라즘": {
        "category": "사이킥",
        "attribute": "팬텀",
        "level": 2,
        "debuff": "초유체"
    },
    "중첩P": {
        "category": "사이킥",
        "attribute": "팬텀",
        "level": 3,
        "special": "horizontal_splash",
        "debuff": "슈뢰딩거의고양이"
    },
    
    # 사이킥 - 전뇌
    "추론": {
        "category": "사이킥",
        "attribute": "전뇌",
        "level": 1
    },
    "예측": {
        "category": "사이킥",
        "attribute": "전뇌",
        "level": 2,
        "special": "debuff_immunity"  # 모든 디버프 면역
    },
    "오버클럭P": {
        "category": "사이킥",
        "attribute": "전뇌",
        "level": 3
    },
    
    # 피지컬 - 토카막
    "그래플링": {
        "category": "피지컬",
        "attribute": "토카막",
        "level": 1,
        "special": "pull"  # 풀링 가능
    },
    "예열": {
        "category": "피지컬",
        "attribute": "토카막",
        "level": 2,
        "debuff": "Burning",
        "attack_mod": "tal"  # 재능 보정
    },
    "노심융해P": {
        "category": "피지컬",
        "attribute": "토카막",
        "level": 3,
        "attack_mod": "tal*2"  # 재능*2
    },
    
    # 피지컬 - 초고속
    "순간가속": {
        "category": "피지컬",
        "attribute": "초고속",
        "level": 1,
        "priority_mod": "mst*20"  # 숙련*20
    },
    "소닉붐": {
        "category": "피지컬",
        "attribute": "초고속",
        "level": 2,
        "attack_mod": "tal",
        "special": "vertical_splash",  # 세로 스플래시
        "effect": "knockback"
    },
    "시간정지P": {
        "category": "피지컬",
        "attribute": "초고속",
        "level": 3,
        "special": "double_action"  # 행동 2개
    },
    
    # 피지컬 - 변이
    "컨토션": {
        "category": "피지컬",
        "attribute": "변이",
        "level": 1,
        "special": "dodge"  # 회피 가능
    },
    "외골격": {
        "category": "피지컬",
        "attribute": "변이",
        "level": 2,
        "special": "damage_reduction"
    },
    "전퇴P": {
        "category": "피지컬",
        "attribute": "변이",
        "level": 3,
        "attack_mod": "vtl+tal"  # 활력+재능
    },
    
    # 테라포머 - 무게조작
    "부유": {
        "category": "테라포머",
        "attribute": "무게조작",
        "level": 1,
        "special": "stacking_allowed"  # 겹쳐서기 가능
    },
    "무겁게": {
        "category": "테라포머",
        "attribute": "무게조작",
        "level": 2,
        "debuff": "Entangled",
        "target": "all_enemies",
        "effect": "pull_all"
    },
    "나선P": {
        "category": "테라포머",
        "attribute": "무게조작",
        "level": 3,
        "attack_mod": "tal",
        "special": "reflect"  # 반사
    },
    
    # 테라포머 - 변온
    "안개의장막": {
        "category": "테라포머",
        "attribute": "변온",
        "level": 1,
        "special": "ranged_dodge",  # 원거리 회피
        "target": "adjacent"  # 양옆 범위
    },
    "인공강우": {
        "category": "테라포머",
        "attribute": "변온",
        "level": 2,
        "debuff": "Wet",
        "target": "all_enemies"
    },
    "절대영도P": {
        "category": "테라포머",
        "attribute": "변온",
        "level": 3,
        "debuff": "Frozen",
        "effect": "immobilize_all"
    },
    
    # 테라포머 - 초생장
    "재생": {
        "category": "테라포머",
        "attribute": "초생장",
        "level": 1,
        "effect": "heal",
        "target": "adjacent"
    },
    "인공우림": {
        "category": "테라포머",
        "attribute": "초생장",
        "level": 2,
        "debuff": "Entangled",
        "target": "all_enemies"
    },
    "부식P": {
        "category": "테라포머",
        "attribute": "초생장",
        "level": 3
    },
    
    # 유형 - 퓨어 전용
    "수복": {
        "category": "유형",
        "attribute": "퓨어",
        "level": 2,
        "effect": "debuff_remove"  # 디버프 d(숙련/2)개 해제
    },
    "심화훈련": {
        "category": "유형",
        "attribute": "퓨어",
        "level": 2,
        "is_passive": True,
        "effect": "skill_chain_bonus"  # 같은 속성 연속 사용 시 (재×2) 보너스
    },
    "극한반복": {
        "category": "유형",
        "attribute": "퓨어",
        "level": 3,
        "is_passive": True,
        "effect": "skill_uses_multiply"  # 필살기 사용 횟수 (숙/2)회
    },
    
    # 공통
    "응급처치키트": {
        "category": "공통",
        "level": 1,
        "effect": "self_heal"
    },
    "제트슈즈": {
        "category": "공통",
        "level": 1,
        "special": "move_4"  # 최대 4칸 이동 (직선)
    },
    "아드레날린": {
        "category": "공통",
        "level": 2,
        "effect": "focus_band"  # 기합의띠 효과
    },
    "초공간도약": {
        "category": "공통",
        "level": 4,
        "special": "teleport"  # 텔레포트
    }
}
```

### 2. 스킬 체인 처리

```python
def apply_skill_chain(action: dict, character: dict, game_state: dict) -> dict:
    """
    스킬 체인 효과를 행동에 적용합니다.
    
    Returns:
        수정된 행동 딕셔너리
    """
    if not action.get("skill_chain"):
        return action
    
    skill_name = action["skill_chain"]
    skill_data = SKILL_DATABASE.get(skill_name)
    if not skill_data:
        return action
    
    stats = character["stats"]
    
    # 우선도 보정
    if "priority_mod" in skill_data:
        mod = skill_data["priority_mod"]
        if isinstance(mod, str):
            if mod == "mst*20":
                action["priority"] += stats["mst"] * 20
        elif isinstance(mod, int):
            action["priority"] += mod
    
    # 공격력 보정
    if "attack_mod" in skill_data and action["type"] in ["melee_attack", "ranged_attack"]:
        mod = skill_data["attack_mod"]
        if mod == "tal":
            action["attack_power"] += stats["tal"]
        elif mod == "tal*2":
            action["attack_power"] += stats["tal"] * 2
        elif mod == "vtl+tal":
            action["attack_power"] += stats["vtl"] + stats["tal"]
        elif mod == "재*2":  # 심화훈련 보너스
            if check_consecutive_skill_use(character, skill_name):
                action["attack_power"] += stats["tal"] * 2
    
    # 특수 효과는 행동 계산 단계에서 처리
    action["skill_effects"] = skill_data.get("special", [])
    
    return action
```

---

## 디버프 시스템

### 1. 디버프 적용

```python
def apply_debuff(character: dict, debuff_type: str, value: int = 1, current_round: int = 0):
    """
    캐릭터에 디버프를 적용합니다. 모든 디버프는 중첩됩니다.
    
    Args:
        character: 캐릭터 딕셔너리
        debuff_type: "Burning", "Shocked", "Wet", "Frozen", "Entangled"
        value: 디버프 값 (Shocked의 경우 공격력 감소량, 다른 경우는 중첩 횟수)
        current_round: 현재 라운드 번호
    """
    if "debuffs" not in character:
        character["debuffs"] = []
    
    character["debuffs"].append({
        "type": debuff_type,
        "value": value,
        "applied_round": current_round
    })
```

### 2. 디버프 턴 종료 처리

```python
def process_debuffs_end_turn(character: dict) -> int:
    """
    턴 종료 시 디버프로 인한 대미지를 처리합니다.
    
    Returns:
        받은 총 대미지
    """
    total_damage = 0
    
    if "debuffs" not in character:
        return 0
    
    # Burning: 매 턴 2d4 대미지
    burning_count = sum(1 for d in character["debuffs"] if d["type"] == "Burning")
    if burning_count > 0:
        for _ in range(burning_count):
            total_damage += roll_dice(2, 4)
    
    # Wet + Frozen: 매 턴 4d4 대미지
    has_wet = any(d["type"] == "Wet" for d in character["debuffs"])
    has_frozen = any(d["type"] == "Frozen" for d in character["debuffs"])
    if has_wet and has_frozen:
        wet_frozen_count = min(
            sum(1 for d in character["debuffs"] if d["type"] == "Wet"),
            sum(1 for d in character["debuffs"] if d["type"] == "Frozen")
        )
        for _ in range(wet_frozen_count):
            total_damage += roll_dice(4, 4)
    
    return total_damage
```

### 3. 디버프 면역 체크

```python
def is_immune_to_debuff(character: dict, debuff_type: str) -> bool:
    """
    캐릭터가 특정 디버프에 면역인지 확인합니다.
    
    예측 스킬: 모든 디버프 면역
    """
    # 예측 스킬 체크
    skills = character.get("skills", [])
    for skill in skills:
        if skill.get("name") == "예측":
            return True
    
    return False
```

### 4. 빙결 추가 대미지

```python
def calculate_frozen_bonus_damage(base_damage: int, character: dict) -> int:
    """
    빙결 상태일 때 받는 추가 대미지를 계산합니다.
    공격받았을 때 50%의 추가 대미지 (디버프 대미지는 포함X)
    """
    has_frozen = any(d["type"] == "Frozen" for d in character.get("debuffs", []))
    if has_frozen:
        return int(base_damage * 0.5)
    return 0
```

---

## 전투 계산

### 1. 행동 계산 메인 함수

```python
def resolve_action(action: dict, game: Game) -> dict:
    """
    단일 행동을 계산합니다.
    
    Returns:
        계산 결과 딕셔너리
    """
    slot = action["player_slot"]
    character = game.players[slot - 1]["character"]
    result = {
        "action": action,
        "success": False,
        "damage_dealt": 0,
        "effects_applied": [],
        "message": ""
    }
    
    # 스킬 체인 특수 효과 처리
    if action.get("skill_chain"):
        skill_result = apply_skill_special_effects(action, character, game)
        result["effects_applied"].extend(skill_result.get("effects", []))
    
    # 행동 타입별 처리
    if action["type"] == "melee_attack":
        result = resolve_melee_attack(action, character, game, result)
    elif action["type"] == "ranged_attack":
        result = resolve_ranged_attack(action, character, game, result)
    elif action["type"] == "battlefield_movement":
        result = resolve_movement(action, character, game, result)
    elif action["type"] == "wait":
        result = resolve_wait(action, character, game, result)
    
    return result
```

### 2. 근거리공격 계산

```python
def resolve_melee_attack(action: dict, attacker: dict, game: Game, result: dict) -> dict:
    """
    근거리공격을 계산합니다.
    """
    attacker_pos = attacker["pos"]
    target_pos = action["target"]
    
    # 사거리 검증
    if not is_in_range(attacker_pos, target_pos, "melee_attack"):
        result["message"] = f"{attacker['name']}의 공격이 사거리를 벗어났습니다."
        return result
    
    # 타겟 찾기
    target_slot = game.position_occupancy.get(target_pos)
    if not target_slot:
        result["message"] = f"{target_pos}에 타겟이 없습니다."
        return result
    
    target = game.players[target_slot - 1]["character"]
    
    # 회피 체크 (컨토션 등)
    if check_dodge(action, attacker, target, game):
        result["message"] = f"{target['name']}이(가) 공격을 회피했습니다!"
        result["success"] = True
        return result
    
    # 공격력 계산
    attack_power = action["attack_power"]
    
    # 디버프 보정 (Shocked)
    for debuff in target.get("debuffs", []):
        if debuff["type"] == "Shocked":
            attack_power -= debuff["value"]
    
    attack_power = max(0, attack_power)
    
    # 빙결 추가 대미지
    frozen_bonus = calculate_frozen_bonus_damage(attack_power, target)
    total_damage = attack_power + frozen_bonus
    
    # 대미지 적용
    target["current_hp"] -= total_damage
    target["current_hp"] = max(0, target["current_hp"])
    
    # 전투불능 체크
    if target["current_hp"] == 0:
        target["battle_state"]["is_knocked_out"] = True
    
    result["success"] = True
    result["damage_dealt"] = total_damage
    result["message"] = f"{attacker['name']}이(가) {target['name']}에게 {total_damage} 대미지를 입혔습니다!"
    
    return result
```

### 3. 원거리공격 계산

```python
def resolve_ranged_attack(action: dict, attacker: dict, game: Game, result: dict) -> dict:
    """
    원거리공격을 계산합니다.
    """
    attacker_pos = attacker["pos"]
    target_pos = action["target"]
    
    # 사거리 검증
    if not is_in_range(attacker_pos, target_pos, "ranged_attack"):
        result["message"] = f"{attacker['name']}의 공격이 사거리를 벗어났습니다."
        return result
    
    # 커버링 검증
    if is_covered(attacker_pos, target_pos, game.position_occupancy):
        # 유도탄 스킬 체크
        if action.get("skill_chain") != "유도탄" or not check_proficiency_roll(attacker, "유도탄"):
            result["message"] = f"{target_pos}의 타겟이 커버링되어 있습니다."
            return result
    
    # 타겟 찾기
    target_slot = game.position_occupancy.get(target_pos)
    if not target_slot:
        result["message"] = f"{target_pos}에 타겟이 없습니다."
        return result
    
    target = game.players[target_slot - 1]["character"]
    
    # 회피 체크
    if check_dodge(action, attacker, target, game):
        result["message"] = f"{target['name']}이(가) 공격을 회피했습니다!"
        result["success"] = True
        return result
    
    # 공격력 계산 및 대미지 적용 (근거리공격과 동일)
    # ... (근거리공격과 유사한 로직)
    
    return result
```

### 4. 이동 계산

```python
def resolve_movement(action: dict, character: dict, game: Game, result: dict) -> dict:
    """
    전장이동을 계산합니다.
    """
    current_pos = character["pos"]
    direction = action["direction"]
    
    # 속박 체크
    if has_debuff(character, "Entangled"):
        if not check_vitality_roll(character):
            result["message"] = f"{character['name']}이(가) 속박되어 이동에 실패했습니다."
            return result
    
    # 목표 위치 계산
    target_pos = calculate_target_position(current_pos, direction)
    
    # 이동 가능 여부 검증
    if not is_valid_position(target_pos):
        result["message"] = f"{target_pos}는 유효하지 않은 위치입니다."
        return result
    
    # 목표 위치가 비어있는지 확인 (부유 스킬이 없으면)
    if target_pos in game.position_occupancy and not has_skill(character, "부유"):
        result["message"] = f"{target_pos}는 이미 점유되어 있습니다."
        return result
    
    # 위치 이동
    old_pos = current_pos
    character["pos"] = target_pos
    game.position_occupancy.pop(old_pos, None)
    game.position_occupancy[target_pos] = get_slot_by_character(character, game)
    
    result["success"] = True
    result["message"] = f"{character['name']}이(가) {old_pos}에서 {target_pos}로 이동했습니다."
    
    return result
```

---

## 구현 단계별 가이드

### Phase 1: 데이터 구조 확장 (1-2일)

1. **캐릭터 데이터 구조 확장**
   - `temp_character.py`에 디버프, 전투 상태 필드 추가
   - HP 계산 로직 추가 (활력*5+10)
   - 스킬 데이터 구조 정의

2. **Game 클래스 확장**
   - `battle_phase`, `declared_actions`, `action_queue` 필드 추가
   - `position_occupancy` 딕셔너리 추가
   - `round_start_positions` 딕셔너리 추가

3. **스킬 데이터베이스 생성**
   - `SKILL_DATABASE` 딕셔너리 생성
   - 모든 스킬의 속성, 레벨, 효과 정의

### Phase 2: 기본 전투 플로우 구현 (2-3일)

1. **전투 시작 처리**
   - `start_battle()` 메서드 구현
   - 시작 위치 선언 수신 및 검증
   - 캐릭터 배치

2. **행동 선언 시스템**
   - `declare_action(slot, action)` 메서드 구현
   - 행동 검증 로직
   - 모든 플레이어 제출 완료 체크

3. **우선도 계산 시스템**
   - `calculate_action_priority()` 함수 구현
   - 스킬 체인 우선도 보정
   - `action_queue` 정렬

### Phase 3: 행동 계산 구현 (3-4일)

1. **사거리 및 커버링 시스템**
   - `is_in_range()` 함수 구현
   - `is_covered()` 함수 구현
   - 유도탄 스킬 예외 처리

2. **공격 계산**
   - `resolve_melee_attack()` 구현
   - `resolve_ranged_attack()` 구현
   - 공격력 계산 및 대미지 적용
   - 빙결 추가 대미지 처리

3. **이동 계산**
   - `resolve_movement()` 구현
   - 위치 계산 로직
   - 속박 체크
   - 부유 스킬 예외 처리

4. **대기 계산**
   - `resolve_wait()` 구현
   - 컨토션 등 특수 효과 처리

### Phase 4: 스킬 시스템 구현 (3-4일)

1. **스킬 체인 처리**
   - `apply_skill_chain()` 함수 구현
   - 우선도/공격력 보정 적용
   - 심화훈련 보너스 처리

2. **스킬 특수 효과**
   - 회피 (컨토션)
   - 스플래시 (가로/세로)
   - 넉백
   - 풀링
   - 디버프 부여

3. **패시브 스킬**
   - 심화훈련 연속 사용 추적
   - 극한반복 사용 횟수 계산

### Phase 5: 디버프 시스템 구현 (2일)

1. **디버프 적용**
   - `apply_debuff()` 함수 구현
   - 중첩 로직
   - 면역 체크

2. **디버프 턴 종료 처리**
   - `process_debuffs_end_turn()` 구현
   - Burning 대미지
   - Wet + Frozen 대미지

3. **디버프 해제**
   - 수복 스킬 구현
   - 선입선출 로직

### Phase 6: 통합 및 테스트 (2-3일)

1. **전투 루프 완성**
   - 모든 Phase 연결
   - 라운드 종료 처리
   - 전투 종료 조건 체크

2. **에러 처리**
   - 잘못된 행동 선언 처리
   - 네트워크 오류 처리
   - 상태 동기화

3. **테스트**
   - 단위 테스트 작성
   - 통합 테스트
   - 엣지 케이스 테스트

---

## 주요 함수 목록

### Game 클래스 메서드

```python
class Game:
    def start_battle(self) -> dict
    def declare_start_position(self, slot: int, position: str) -> dict
    def declare_action(self, slot: int, action: dict) -> dict
    def calculate_priorities(self) -> None
    def resolve_round(self) -> list[dict]
    def process_round_end(self) -> dict
    def check_battle_end(self) -> bool
```

### 유틸리티 함수

```python
# 우선도 및 공격력
calculate_action_priority(action: dict, character: dict) -> int
calculate_attack_power(action: dict, character: dict) -> int

# 위치 및 사거리
is_in_range(attacker_pos: str, target_pos: str, attack_type: str) -> bool
is_covered(attacker_pos: str, target_pos: str, position_occupancy: dict) -> bool
calculate_target_position(current_pos: str, direction: str) -> str
is_valid_position(position: str) -> bool

# 스킬
apply_skill_chain(action: dict, character: dict, game_state: dict) -> dict
apply_skill_special_effects(action: dict, character: dict, game: Game) -> dict
check_proficiency_roll(character: dict, skill_name: str) -> bool
has_skill(character: dict, skill_name: str) -> bool

# 디버프
apply_debuff(character: dict, debuff_type: str, value: int, current_round: int) -> None
process_debuffs_end_turn(character: dict) -> int
has_debuff(character: dict, debuff_type: str) -> bool
is_immune_to_debuff(character: dict, debuff_type: str) -> bool
calculate_frozen_bonus_damage(base_damage: int, character: dict) -> int

# 행동 계산
resolve_action(action: dict, game: Game) -> dict
resolve_melee_attack(action: dict, attacker: dict, game: Game, result: dict) -> dict
resolve_ranged_attack(action: dict, attacker: dict, game: Game, result: dict) -> dict
resolve_movement(action: dict, character: dict, game: Game, result: dict) -> dict
resolve_wait(action: dict, character: dict, game: Game, result: dict) -> dict

# 기타
roll_dice(count: int, sides: int) -> int
check_dodge(action: dict, attacker: dict, target: dict, game: Game) -> bool
check_vitality_roll(character: dict) -> bool
get_slot_by_character(character: dict, game: Game) -> int
```

---

## WebSocket 메시지 프로토콜

### 클라이언트 → 서버

```json
// 전투 시작 위치 선언
{
    "action": "declare_start_position",
    "game_id": "game123",
    "position": "A1"
}

// 행동 선언
{
    "action": "declare_action",
    "game_id": "game123",
    "action_type": "melee_attack",
    "skill_chain": "순간가속",
    "target": "X2"
}

// 전투 시작 요청
{
    "action": "start_battle",
    "game_id": "game123"
}
```

### 서버 → 클라이언트

```json
// 전투 시작 위치 선언 요청
{
    "type": "request_start_position",
    "game_id": "game123",
    "available_positions": ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]
}

// 행동 선언 요청
{
    "type": "request_action_declaration",
    "game_id": "game123",
    "round": 1
}

// 행동 계산 결과
{
    "type": "action_resolved",
    "game_id": "game123",
    "result": {
        "action": {...},
        "success": true,
        "damage_dealt": 12,
        "message": "..."
    }
}

// 라운드 종료
{
    "type": "round_end",
    "game_id": "game123",
    "round": 1,
    "results": [...]
}

// 전투 종료
{
    "type": "battle_end",
    "game_id": "game123",
    "winner": "team_0",
    "results": {...}
}
```

---

## 주의사항 및 고려사항

1. **상태 동기화**: 모든 클라이언트가 동일한 게임 상태를 유지해야 합니다.
2. **비밀 제출**: 행동 선언은 모든 플레이어가 제출할 때까지 다른 플레이어에게 공개되지 않아야 합니다.
3. **우선도 동점**: 우선도가 같을 경우 처리 방법 정의 필요 (예: 슬롯 순서, 랜덤)
4. **스킬 사용 횟수**: 극한반복의 경우 필살기 사용 횟수 추적 필요
5. **디버프 중첩**: 모든 디버프는 중첩되며, 각각 독립적으로 작동
6. **전투불능**: PVP 대련장에서는 체력 0이 되어도 다음 날 풀피로 회복 (데이터베이스에 기록만)
7. **커버링**: 원거리공격만 적용되며, 같은 팀은 커버링 불가
8. **이동 제한**: 속박 상태에서는 활력 판정 필요, 이동 실패 시 행동 소모

---

## 다음 단계

이 문서를 기반으로 `game_core.py`를 단계별로 확장하세요. 각 Phase를 완료한 후 테스트를 진행하고, 다음 Phase로 진행하는 것을 권장합니다.

추가 질문이나 명확화가 필요한 부분이 있으면 언제든지 문의하세요.

