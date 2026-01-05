# 목표
현재 `game_core.py`의 **세션/슬롯/보드** 중심 구조에, 기획서의 **전투 규칙(위치·커버링·행동 비밀제출·우선도 계산·체인·디버프·스킬/필살기·브리드 패시브)** 를 단계적으로 얹습니다.

---

# 0) 현재 코드에서 먼저 손볼 점 (버그/구조)
1) `self.p_init`를 그대로 리스트에 반복 사용하면 **모든 슬롯이 같은 dict 객체**를 참조합니다.
- 해결: 슬롯 dict는 매번 새로 만들어야 합니다(복사 or 팩토리 함수).

2) `move_player()`에서 `c['name']`을 찾는데, 현재 `self.players` 원소는 `info/character/...` 구조입니다.
- 해결: 캐릭터 정보는 `self.players[slot_idx]['character']`에 들어가도록 일원화하고, `name`은 그 안에서 참조.

3) `team`은 `slot % 2`로 주고 있는데, 실제로는 **A/B 진영 선택**, 레이드에서는 A~B칸 같은 개념이 있으니:
- `team_id` (A/B 등)와 `side`(white/blue 등)는 분리하거나, 기획서대로 **진영(A,B)** 로 단순화 권장.

---

# 1) 데이터 모델 설계 (최소 필수)
아래는 “서버가 알아야 하는 최소 상태”입니다.

## 1-1. CharacterState
- identity
  - `char_id: str`
  - `name: str`
  - `class_id: str`  # Psychic/Physical/Terraformer
  - `types: list[str]`  # one or two types
  - `breed: str`  # Pure/Multi
- stats
        "vtl": 4,    # 활력 (Vitality)
        "sen": 1,    # 감각 (Sense)
        "per": 1,    # 인지 (Perception)
        "tal": 2,    # 재능 (Talent)
        "mst": 2     # 숙련 (Mastery/Proficiency)
  - `hp_max: int = vit * 5 + 10`
  - `hp: int`
- board
  - `pos: str`  # e.g. "Y1" "A3"
- combat runtime
  - `debuffs: dict[str, int]`  # stacks, or store as {name: stacks}
  - `debuff_meta: dict[str, any]`  # optional (e.g. entangled checks)
  - `cooldowns: dict[str, int]`  # optional
  - `per_battle_used: set[str]`  # P skills used
  - `passives: set[str]`  # e.g. "deep_training" "extreme_repeat"

## 1-2. SkillDefinition
- `skill_id: str`
- `name: str`
- `lv: int`
- `is_finisher: bool`  # P
- `targeting: str`  # self / single / row / all_enemies / adjacent, etc.
- `requires: dict`  # class/type/breed requirements
- `effects: list[Effect]`
- `priority_mod: int | callable`
- `power_mod: int | callable`
- `notes: str`

## 1-3. ActionIntent (비밀 제출)
플레이어가 라운드 시작 시 제출:
- `slot: int`
- `base_action: str`  # melee/ranged/move/wait
- `target: str | None`  # slot id or position or row, etc.
- `move_to: str | None`
- `chain_skill_id: str | None`  # 행동 전에 1장 사용

서버는 모든 제출을 모은 뒤 **ResolveQueue**를 생성합니다.

---

# 2) 전투 상태 머신 (Data Flow)
아래 흐름으로 “라운드 단위”를 서버가 통제합니다.

## 2-1. 전투 준비
1) `start_battle()`
- 보드 초기화
- 각 플레이어: 시작 위치 선언(진영 내부에서 선택)
- 덱/핸드 초기화(현재는 규칙만, 구현은 추후)
- `current_round = 1`

## 2-2. 라운드 시작: 비밀 제출 단계
1) 서버가 `round_phase = "collect_intents"` 상태로 전환
2) 클라이언트가 각자 `ActionIntent`를 제출
3) 서버는 `intents_by_slot`에 저장
4) 모두 제출되면 `resolve_round()` 호출

## 2-3. Resolve: 우선도 계산 → 순서대로 처리
1) 각 intent에 대해 우선도 계산
- melee: `priority = sen*10 + mst`
- ranged: `priority = per*10 + mst`
- move: `priority = (sen+per)*5 + mst`
- wait: `priority = 100 + mst`
2) 체인 스킬이 있으면:
- `skill.priority_mod` 반영
- `skill.power_mod` 반영
- `skill.pre_effects`(예: 면역/회피 예약/타겟 규칙 변경) 적용
3) `priority` 높은 것부터 실행
- 동률 처리 규칙을 정해야 함(권장: `priority` 동률이면 `per` 높은 쪽 → `sen` 높은 쪽 → 랜덤)

## 2-4. 각 행동 처리 시 공통 체크
- 타겟 유효성
- 사거리 규칙
  - 근거리: 전방↔전방
  - 원거리: 후방↔후방
- 커버링 규칙
  - 같은 열(1~4)에서 전방이 막으면 후방 타겟 불가
- 디버프/면역/회피 예약
- 데미지/효과 적용

## 2-5. 라운드 종료: 디버프 틱
- Burning: `2d4` damage
- Wet+Frozen: `4d4` per turn
- Frozen: attacked receives +50% damage (exclude debuff damage)
- Shocked: power -n (stack)
- Entangled: when trying to move, check VIT

---

# 3) 보드/커버링/사거리 구현 지침
현재 보드는 4x4 grid로 이미 있음.

## 3-1. 좌표 표준화
서버 내부는 `row_idx, col_idx`로 통일하고, 표시만 "Y1" 형태로 변환 권장.
- rows: 0=Y, 1=X, 2=A, 3=B
- cols: 0=1,1=2,2=3,3=4

### helper (예시)
```python
ROW_MAP = {"Y": 0, "X": 1, "A": 2, "B": 3}
REV_ROW_MAP = {v: k for k, v in ROW_MAP.items()}

def pos_to_rc(pos: str) -> tuple[int, int]:
    r = ROW_MAP[pos[0]]
    c = int(pos[1]) - 1
    return r, c

def rc_to_pos(r: int, c: int) -> str:
    return f"{REV_ROW_MAP[r]}{c+1}"
```

## 3-2. 전방/후방 판정
- 팀/진영에 따라 “전방/후방”의 row 집합이 다를 수 있음.
- 현재 기획서 그림 기준으로는:
  - (상대 진영) Y/X: Y=후방, X=전방
  - (아군 진영) A/B: A=전방, B=후방

즉, 간단 규칙:
- `is_front_row(pos)`
  - if row == X or row == A: front
  - if row == Y or row == B: back

## 3-3. 커버링 체크
원거리 사거리(후방↔후방)에서,
- 같은 col에서 전방 칸에 누가 서 있으면 후방 타겟을 막음.

구현 개념:
1) 공격자 pos의 col = c
2) 타겟이 후방(row=Y or B)인지 확인
3) 타겟의 전방 row(X or A) 같은 col에 **살아있는** 유닛이 있으면 `covered=True`
4) 기본적으로 타겟팅 불가(단, 유도탄 같은 스킬이 override)

---

# 4) 공격력/데미지/보정 적용 지침
기획서 표에 있는 공격력 수식은 예시처럼 보입니다.

권장: 기본 공격력 계산 함수로 통일
- melee_base_power: `(per*2) + (sen*3) + 5`
- ranged_base_power: `(per*3) + (sen*2)`

그리고 스킬은 `power_mod`로 추가.

## 4-1. Frozen(빙결) 50% 추가
- “공격으로 들어가는 최종 데미지”에만 적용
- Burning/Wet tick 같은 디버프 딜은 제외

---

# 5) 체인(스킬 1장 + 행동 1개) 처리 지침
라운드 제출 시점에 `chain_skill_id`를 함께 받습니다.

Resolve 단계에서:
1) 스킬 사용 가능 조건 검사
- lv 제한
- breed 제한
- per-battle(P) 사용 여부
2) 스킬 효과를 **행동 처리 전에** 반영
- 예: `컨토션 + 대기` → 대기 먼저 실행되므로, contortion이 “다음 공격 확정 회피” 같은 플래그를 캐릭터 상태에 세팅
3) 행동 처리
4) 스킬의 후처리(필요 시)

---

# 6) 스킬 테이블을 코드에 넣는 방법
가장 단순하고 유지보수 좋은 방식:
1) `skills.py`에 스킬 정의 dict를 둠
2) `game_core.py`는 id로 조회해서 효과를 적용

예시 스키마(간단):
```python
SKILLS = {
  "guided_missile": {
    "name": "Guided Missile",
    "lv": 1,
    "is_finisher": False,
    "requires": {"class": "psychic", "type": "telekinesis"},
    "targeting": "single",
    "flags": {"ignore_cover": True},
    "priority_mod": 0,
    "power_mod": 0,
  },
}
```

효과가 복잡해지면 `Effect` 클래스로 분리(예: ApplyDebuff, Heal, Move, SetFlag).

---

# 7) 브리드 전용 패시브 적용 지침
현재 기획서:
- Pure Lv2 `심화훈련` (passive)
- Pure Lv3 `극한반복` (passive)

구현 방식:
- 캐릭터 생성 시 `passives`에 등록
- 공격력/스킬 사용 가능 횟수 계산 시 참조

### 심화훈련
- “같은 속성 스킬을 연속 사용하면 (tal*2) power bonus, non-stack”
- 서버는 캐릭터별로:
  - `last_used_type: str | None`
  - `deep_training_active: bool`
를 유지

### 극한반복
- 필살기 사용 가능 횟수: 기본 1 → `(mst // 2)`
- per-battle P 사용 체크를 `per_battle_used_count[skill_id]`로 바꾸는 게 안전

---

# 8) 구현 순서 (Instruction)
아래 순서로 하면 리스크가 가장 낮습니다.

## Step 1. 슬롯/플레이어 구조 안정화
- `p_init_factory()`로 매 슬롯 dict 생성
- `add_player_to_slot()`에서 `character` 필드 구조 확정
- `get_player_by_user_id()` 유지

## Step 2. CharacterState 도입
- `assign_character(slot, character_data)` 추가
- vit/sen/per/tal/mst → hp_max/hp 계산
- `pos` 저장

## Step 3. Board helpers + 이동
- `pos_to_rc/rc_to_pos`
- `is_front_row/is_back_row`
- `is_occupied(pos)`
- `move_intent` 처리(상하좌우대각 1칸)
- 제트슈즈 같은 예외 이동은 나중에 스킬로 처리

## Step 4. Intent 수집 API
- `submit_intent(slot, intent)`
- `all_intents_submitted()`
- `resolve_round()` 뼈대

## Step 5. 우선도 계산 + 정렬 + 타이브레이커
- `calc_priority(character, base_action)`
- tie-break rule 확정

## Step 6. 커버링/사거리/타겟 유효성
- `can_target(attacker, target, action, flags)`
- `is_covered(target)`

## Step 7. 데미지/디버프 시스템
- `apply_damage(target, amount, *, is_attack=True)`
- `apply_debuff(target, name, stacks=1)`
- `tick_debuffs_end_of_round()`

## Step 8. 체인 스킬 (간단 3개부터)
- 먼저 “플래그형” 스킬로 시작 권장
  - Guided Missile: ignore_cover flag
  - Moment Accel: priority +
  - Contortion: evade_next_attack flag

## Step 9. 스킬 테이블 확장
- 현재 표의 스킬들을 `skill_id`로 정리
- `requires`/`flags`/`effects`를 채워넣기

## Step 10. vomit() 확장
- 클라가 필요한 UI 상태를 모두 포함
  - characters: stats/hp/pos/debuffs
  - current_round
  - phase
  - pending intents count (optional)

---

# 9) 서버-클라 메시지 흐름 (권장)
- client → server
  - `join_slot`
  - `assign_character`
  - `declare_start_pos`
  - `submit_intent` (base_action + optional chain_skill)
- server → client
  - `state_update` (vomit 확장)
  - `round_resolved` (log + hp changes + debuffs + moves)

---

# 10) 바로 다음에 결정해야 하는 것 (코드 작성 전 최소 결정)
1) 동률 우선도 처리 규칙
2) “근거리/원거리”의 판정 기준이 **행동 종류**인지, **무기/스킬**인지
3) 스킬의 판정(숙련판정 등)에서 주사위/확률 규칙
   - 예: `roll = d100 <= mst*20` 같은 형태로 일단 고정하면 구현이 쉬움

원하시면, 위 계획을 기준으로 `game_core.py`에 들어갈 **함수 시그니처 목록(스켈레톤)** 을 바로 뽑아드릴 수 있습니다.

