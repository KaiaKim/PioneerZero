
## 6. 스킬 상세 구현 가이드 (Skill Implementation Guide)

### 6.1 스킬 데이터 구조 (Skill Data Structure)

구조화된 스킬 정의를 사용합니다. `server/skills.py`에 스킬 정의를 둡니다:

```python
# server/skills.py

SKILLS = {
    "guided_missile": {
        "name": "유도탄",
        "lv": 1,
        "is_finisher": False,
        "requires": {
            "class": "psychic",
            "type": "telekinesis"
        },
        "targeting": "single",
        "flags": {
            "ignore_cover": True
        },
        "priority_mod": 0,
        "power_mod": 0,
        "notes": "커버링 무시"
    },
    "instant_acceleration": {
        "name": "순간가속",
        "lv": 1,
        "is_finisher": False,
        "requires": {
            "class": "physical",
            "type": "superspeed"
        },
        "targeting": "self",
        "flags": {},
        "priority_mod": lambda stats: stats['mst'] * 20,  # callable
        "power_mod": 0,
        "notes": "우선도 증가"
    },
    "contortion": {
        "name": "컨토션",
        "lv": 1,
        "is_finisher": False,
        "requires": {
            "class": "physical",
            "type": "mutation"
        },
        "targeting": "self",
        "flags": {
            "dodge_next_attack": True
        },
        "priority_mod": 0,
        "power_mod": 0,
        "notes": "다음 공격 회피"
    },
    # ... 기타 스킬들
}
```

**스킬 정의 필드 설명:**
- `skill_id`: 스킬 고유 식별자 (영문)
- `name`: 스킬 이름 (한글)
- `lv`: 스킬 레벨
- `is_finisher`: 필살기(P) 여부
- `requires`: 사용 조건 (class, type, breed 등)
- `targeting`: 타겟팅 타입 (self, single, row, all_enemies, adjacent 등)
- `flags`: 특수 플래그 (ignore_cover, dodge_next_attack 등)
- `priority_mod`: 우선도 보정 (int 또는 callable(stats) -> int)
- `power_mod`: 공격력 보정 (int 또는 callable(stats) -> int)
- `effects`: 복잡한 효과 리스트 (필요 시 Effect 클래스로 분리)
- `notes`: 메모

### 6.2 스킬 체인 처리 로직 (Skill Chain Processing Logic)

```python
# server/game_core.py

from server.skills import SKILLS

def apply_skill_chain(self, action_data, skill_id):
    """스킬 체인 효과 적용"""
    skill = SKILLS.get(skill_id)
    if not skill:
        return action_data
    
    player = self.players[action_data['slot'] - 1]
    character = player['character']
    stats = character['stats']
    
    # 스킬 사용 가능 조건 검사
    if not self.check_skill_requirements(character, skill):
        return action_data  # 조건 불만족 시 스킬 효과 없음
    
    # 우선도 보정
    if skill.get('priority_mod'):
        if callable(skill['priority_mod']):
            bonus = skill['priority_mod'](stats)
        else:
            bonus = skill['priority_mod']
        action_data['priority'] += bonus
    
    # 공격력 보정
    if skill.get('power_mod'):
        if callable(skill['power_mod']):
            bonus = skill['power_mod'](stats)
        else:
            bonus = skill['power_mod']
        action_data['attack_power'] = action_data.get('attack_power', 0) + bonus
    
    # 플래그 적용
    if skill.get('flags'):
        for flag, value in skill['flags'].items():
            if flag == 'ignore_cover':
                action_data['ignore_covering'] = True
            elif flag == 'dodge_next_attack':
                character['dodge_next_attack'] = True
            # 기타 플래그 처리...
    
    # 효과 적용 (복잡한 효과는 Effect 클래스로 처리)
    if skill.get('effects'):
        for effect in skill['effects']:
            self.apply_effect(effect, action_data, character)
    
    return action_data

def check_skill_requirements(self, character, skill):
    """스킬 사용 가능 조건 검사"""
    requires = skill.get('requires', {})
    
    # class 체크
    if 'class' in requires:
        if character.get('class') != requires['class']:
            return False
    
    # type 체크
    if 'type' in requires:
        if requires['type'] not in character.get('types', []):
            return False
    
    # breed 체크
    if 'breed' in requires:
        if character.get('breed') != requires['breed']:
            return False
    
    # lv 체크 (필요 시)
    if skill.get('lv', 0) > 0:
        # 레벨 체크 로직 (필요 시 구현)
        pass
    
    # per-battle 제한 체크 (필살기인 경우)
    if skill.get('is_finisher'):
        per_battle_used = character.get('per_battle_used', set())
        if skill['name'] in per_battle_used:
            return False  # 이미 사용함
    
    return True
```
