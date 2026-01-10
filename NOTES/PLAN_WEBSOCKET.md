
## 4. 채팅 명령어 처리 (Chat Command Processing)

### 4.1 선언 입력 방식 (Declaration Input Method)

**중요**: 위치 선언과 행동 선언은 채팅 슬래시 명령어(`/`)를 통해 처리됩니다. 선언 데이터는 채팅 히스토리에 저장되므로 별도의 메모리 저장소(`position_declarations`, `action_declarations`)를 만들지 않습니다. `util.py`의 기존 채팅 유틸리티 함수(`dbmanager.save_chat()`, `dbmanager.get_chat_history()`)를 사용합니다.

### 4.2 위치 선언 명령어 (Position Declaration Commands)

#### 채팅 명령어 형식
```
/위치 <위치>
```

#### 예시
- `/위치 A1` - A1 위치 선언
- `/위치 B2` - B2 위치 선언
- `/위치 X3` - X3 위치 선언 (team 1)
- `/위치 Y4` - Y4 위치 선언 (team 1)

#### 처리 흐름
1. 사용자가 채팅에 `/위치 A1` 입력
2. `handle_chat()` 함수에서 슬래시 명령어 감지 (`content[0] == "/"`)
3. 명령어 파싱: `command = content[1:]` → `"위치 A1"`
4. 위치 추출: `position = "A1"`
5. `game.parse_position_declaration_from_chat(slot, position)` 호출하여 검증
6. 검증 성공 시 채팅 히스토리에 저장: `dbmanager.save_chat(game.id, "위치 A1 선언 완료", sort="system", ...)`
7. 모든 클라이언트에 채팅 메시지 브로드캐스트

#### 구현 예시
```python
# server/game_ws.py

async def handle_chat(websocket: WebSocket, message: dict, game):
    """Handle chat messages and commands"""
    content = message.get("content", "")
    sender = message.get("sender")
    user_info = conmanager.get_user_info(websocket)
    user_id = user_info.get('id')
    slot = game.get_player_by_user_id(user_id)
    
    if content and content[0] == "/":
        # Handle commands
        command = content[1:]
        result = "unknown command"
        
        # 위치 선언 명령어: /위치 A1
        if command.startswith("위치 "):
            position = command.split(" ", 1)[1].strip().upper()  # "A1"
            
            if not slot:
                result = "플레이어 슬롯을 찾을 수 없습니다"
            else:
                # 위치 선언 검증 및 처리
                validation_result = game.parse_position_declaration_from_chat(slot, position)
                result = validation_result.get("message", "위치 선언 실패")
                
                if validation_result.get("success"):
                    # 위치 선언 단계인지 확인
                    if game.combat_state['phase'] == 'position_declaration':
                        # 채팅 히스토리에 저장 (비밀 선언이므로 sort="secret" 또는 특별 처리)
                        msg = dbmanager.save_chat(
                            game.id, 
                            f"위치 {position} 선언 완료", 
                            sort="system",  # 또는 "secret" - 다른 플레이어에게는 보이지 않음
                            sender="System"
                        )
                        # 비밀 선언이므로 선언한 플레이어에게만 전송
                        await websocket.send_json(msg)
                        
                        # 모든 위치 선언이 완료되었는지 확인 (비동기 처리 고려)
                        # 주의: 실제로는 모든 선언이 완료될 때까지 대기하거나,
                        # 별도의 타이머/체크 로직이 필요할 수 있습니다
                        # 여기서는 예시만 보여줍니다
                        declarations = game.parse_position_declarations_from_chat_history()
                        if game.check_all_positions_declared_from_chat():
                            # resolve_position_declarations 호출
                            result = game.resolve_position_declarations(declarations)
                            # 전투 시작 알림 브로드캐스트
                            await conmanager.broadcast_to_game(game.id, {
                                "type": "combat_started",
                                "combat_state": game.combat_state,
                                "butting_results": result.get("butted_count", 0)
                            })
                    else:
                        result = "위치 선언 단계가 아닙니다"
        
        # 행동 선언 명령어 처리 (아래 섹션 참고)
        elif command.startswith("행동 "):
            # ...
        
        # 기존 명령어들
        elif "이동" in command:
            result = game.move_player(sender, command)
        elif "스킬" in command:
            result = "스킬 사용함"
        
        if result != "unknown command":
            msg = dbmanager.save_chat(game.id, result, sort="system")
            await conmanager.broadcast_to_game(game.id, msg)
    else:
        # Regular chat message
        msg = dbmanager.save_chat(game.id, content, sender=sender, sort="user", user_id=user_id)
        await conmanager.broadcast_to_game(game.id, msg)
```

### 4.3 행동 선언 명령어 (Action Declaration Commands)

#### 채팅 명령어 형식
```
/행동 <행동타입> [대상] [스킬]
```

#### 예시
- `/행동 근거리공격 X2` - X2를 대상으로 근거리 공격
- `/행동 원거리공격 Y1` - Y1을 대상으로 원거리 공격
- `/행동 원거리공격 Y1 순간가속` - 순간가속 스킬 체인과 함께 원거리 공격
- `/행동 전장이동 A2` - A2로 이동
- `/행동 대기` - 대기 행동
- `/행동 대기 컨토션` - 컨토션 스킬 체인과 함께 대기

#### 처리 흐름
1. 사용자가 채팅에 `/행동 근거리공격 X2` 입력
2. `handle_chat()` 함수에서 슬래시 명령어 감지
3. 명령어 파싱: `command = "행동 근거리공격 X2"`
4. 행동 타입, 대상, 스킬 추출
5. `game.parse_action_declaration_from_chat(slot, action_type, target, skill_chain)` 호출하여 검증
6. 검증 성공 시 채팅 히스토리에 저장 (비밀 선언)
7. 모든 행동 선언이 완료되었는지 확인

#### 구현 예시
```python
# server/game_ws.py - handle_chat 함수 내부

elif command.startswith("행동 "):
    action_str = command.split(" ", 1)[1]  # "근거리공격 X2" 또는 "대기"
    parts = action_str.split()
    
    action_type_map = {
        "근거리공격": "melee_attack",
        "원거리공격": "ranged_attack",
        "전장이동": "battlefield_move",
        "대기": "wait"
    }
    
    if not slot:
        result = "플레이어 슬롯을 찾을 수 없습니다"
    elif game.combat_state['phase'] != 'action_declaration':
        result = "행동 선언 단계가 아닙니다"
    else:
        action_type_kr = parts[0]  # "근거리공격"
        action_type = action_type_map.get(action_type_kr)
        
        if not action_type:
            result = f"알 수 없는 행동 타입: {action_type_kr}"
        else:
            target = None
            skill_chain = None
            
            if action_type in ['melee_attack', 'ranged_attack']:
                if len(parts) < 2:
                    result = "공격 대상이 지정되지 않았습니다"
                else:
                    target = parts[1].upper()  # "X2"
                    if len(parts) >= 3:
                        skill_chain = parts[2]  # "순간가속"
            elif action_type == 'battlefield_move':
                if len(parts) < 2:
                    result = "이동 목적지가 지정되지 않았습니다"
                else:
                    target = parts[1].upper()  # "A2"
            elif action_type == 'wait':
                if len(parts) >= 2:
                    skill_chain = parts[1]  # "컨토션"
            
            if target or action_type == 'wait':
                # 행동 선언 검증 및 처리
                validation_result = game.parse_action_declaration_from_chat(
                    slot, action_type, target, skill_chain
                )
                result = validation_result.get("message", "행동 선언 실패")
                
                if validation_result.get("success"):
                    # 비밀 선언이므로 선언한 플레이어에게만 전송
                    msg = dbmanager.save_chat(
                        game.id,
                        f"행동 선언 완료: {action_str}",
                        sort="system",
                        sender="System"
                    )
                    await websocket.send_json(msg)
                    
                    # 모든 행동 선언이 완료되었는지 확인
                    if game.check_all_action_declarations_complete_from_chat():
                        # 우선도 계산 및 해결 단계로 이동
                        declarations = game.parse_action_declarations_from_chat_history()
                        game.calculate_all_priorities(declarations)
```

### 4.4 채팅 히스토리에서 선언 파싱 (Parsing Declarations from Chat History)

#### 위치 선언 파싱 함수
```python
# server/game_core.py

def parse_position_declarations_from_chat_history(self):
    """채팅 히스토리에서 위치 선언 파싱"""
    from .util import dbmanager
    from datetime import datetime
    
    chat_history = dbmanager.get_chat_history(self.id)
    declarations = {}
    
    # position_declaration phase 동안의 채팅만 파싱
    # 주의: chat_history는 모든 채팅을 포함하므로, phase 필터링이 필요할 수 있습니다
    for row in chat_history:
        # row format: (chat_id, sender, time, content, sort, user_id)
        chat_time_str = row[2]  # ISO 형식 시간 문자열
        content = row[3]  # 내용
        user_id = row[5]  # user_id
        
        # position_declaration phase 동안의 명령어만 파싱
        if content.startswith("/위치 "):
            position = content.split(" ", 1)[1].strip().upper()
            slot = self.get_player_by_user_id(user_id)
            
            if slot:
                # 시간 문자열을 Unix timestamp로 변환
                try:
                    chat_time = datetime.fromisoformat(chat_time_str)
                    declared_at = chat_time.timestamp()
                except (ValueError, TypeError):
                    # 시간 파싱 실패 시 현재 시간 사용
                    import time
                    declared_at = time.time()
                
                declarations[slot] = {
                    'slot': slot,
                    'position': position,
                    'declared_at': declared_at,
                    'butted': False,
                    'final_position': position
                }
    
    return declarations

def check_all_positions_declared_from_chat(self):
    """채팅 히스토리에서 모든 위치 선언이 완료되었는지 확인"""
    declarations = self.parse_position_declarations_from_chat_history()
    declared_slots = set(declarations.keys())
    
    active_slots = set()
    for i in range(self.player_num):
        slot = i + 1
        player = self.players[i]
        if player.get('info') and not player.get('info', {}).get('is_bot'):
            active_slots.add(slot)
    
    return declared_slots == active_slots
```

#### 행동 선언 파싱 함수
```python
# server/game_core.py

def parse_action_declarations_from_chat_history(self):
    """채팅 히스토리에서 행동 선언 파싱"""
    from .util import dbmanager
    
    chat_history = dbmanager.get_chat_history(self.id)
    declarations = {}
    
    # action_declaration phase 동안의 채팅만 파싱
    for row in chat_history:
        content = row[3]  # 내용
        user_id = row[5]  # user_id
        
        if content.startswith("/행동 "):
            action_str = content.split(" ", 1)[1]
            slot = self.get_player_by_user_id(user_id)
            
            if slot:
                # 행동 파싱 (위의 handle_chat 로직과 동일)
                # ... 파싱 로직 ...
                
                declarations[slot] = {
                    'slot': slot,
                    'action_type': action_type,
                    'target': target,
                    'skill_chain': skill_chain,
                    # ...
                }
    
    return declarations

def check_all_action_declarations_complete_from_chat(self):
    """채팅 히스토리에서 모든 행동 선언이 완료되었는지 확인"""
    declarations = self.parse_action_declarations_from_chat_history()
    declared_slots = set(declarations.keys())
    
    active_slots = set()
    for i in range(self.player_num):
        slot = i + 1
        player = self.players[i]
        if player.get('info') and not player.get('info', {}).get('is_bot'):
            active_slots.add(slot)
    
    return declared_slots == active_slots
```

### 4.5 비밀 선언 처리 (Secret Declaration Handling)

비밀 선언(위치 선언, 행동 선언)의 경우:
- 채팅 히스토리에는 저장되지만, 다른 플레이어에게는 브로드캐스트되지 않습니다.
- 선언한 플레이어에게만 확인 메시지가 전송됩니다.
- `dbmanager.save_chat()`의 `sort` 파라미터를 사용하여 비밀 메시지로 표시할 수 있습니다 (예: `sort="secret"`).
- 또는 선언 응답 메시지는 브로드캐스트하지 않고 `websocket.send_json()`으로 개별 전송합니다.

---

## 5. WebSocket 메시지 프로토콜 (WebSocket Message Protocol - Non-Chat Commands)

### 5.1 클라이언트 → 서버 메시지 (Client → Server Messages - Non-Chat)

#### 타일 피드백 요청
```json
{
    "action": "request_tile_feedback",
    "game_id": "game123",
    "slot": 1,
    "action_type": "melee_attack"  // "melee_attack", "ranged_attack", "battlefield_move", null (모두)
}
```

**주의**: 위치 선언과 행동 선언은 위의 채팅 명령어(`/위치`, `/행동`)를 사용합니다. 별도의 WebSocket 메시지 액션이 필요하지 않습니다.

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

#### 행동 선언 단계 시작
```json
{
    "type": "action_declaration_phase",
    "round": 1,
    "time_limit": 60,
    "timer_started": true
}
```

#### 타이머 업데이트 (1초마다 브로드캐스트)
```json
{
    "type": "timer_update",
    "timer_type": "action_declaration",
    "elapsed": 15,
    "remaining": 45,
    "is_running": true,
    "duration": 60
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
    "target_hp_after": 18
}
```

#### 라운드 종료
```json
{
    "type": "round_end",
    "round": 1,
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

#### 타일 피드백 응답
```json
{
    "type": "tile_feedback",
    "valid_attack_tiles": ["X2", "A2"],
    "valid_move_tiles": ["Y1", "Y2", "X2"],
    "action_type": "melee_attack"
}
```
## 5. 구현 단계 (Implementation Steps) FRONT

### Phase 4: 타이머 시스템 통합 (Timer System Integration)

1. **타이머 메서드 구현** (`server/game_core.py`)
   - `start_timer()` 구현 (TIMER_PLAN.md 참고)
   - `stop_timer()` 구현
   - `get_timer_state()` 구현
   - `start_action_declaration_timer()` 구현 (60초 카운트다운)

2. **백그라운드 태스크** (`server/main.py`)
   - `timer_broadcast_task()` 구현
   - 1초마다 모든 게임의 타이머 상태 브로드캐스트
   - 행동 선언 단계 중인 게임만 타이머 업데이트 전송

3. **타이머 브로드캐스트 함수** (`server/game_ws.py`)
   - `broadcast_timer_update()` 구현
   - 게임의 모든 클라이언트에 타이머 상태 전송

### Phase 5: WebSocket 핸들러 구현 (WebSocket Handler Implementation)

1. **`server/game_ws.py`에 핸들러 추가**
   - `handle_declare_start_position()`
   - `handle_action_declare()`
   - `handle_start_combat()` (GM용)
   - `handle_request_tile_feedback()` (타일 피드백 요청)

2. **브로드캐스트 함수**
   - `broadcast_combat_state()`
   - `broadcast_action_resolution()`
   - `broadcast_timer_update()` (타이머 업데이트, 1초마다)

3. **타이머 관리 함수**
   - `start_action_declaration_timer()` 구현
     - 60초 타이머 시작
     - timer_type='action_declaration', duration=60
   - `stop_action_declaration_timer()` 구현
     - 행동 선언 단계 종료 시 타이머 중지
   - `get_timer_state()` 구현 (TIMER_PLAN.md 참고)
     - 현재 타이머 상태 반환 (elapsed, remaining)

3. **타일 피드백 핸들러 구현 예시**
```python
# server/game_ws.py

async def handle_request_tile_feedback(websocket: WebSocket, message: dict, game):
    """타일 피드백 요청 처리"""
    user_info = conmanager.get_user_info(websocket)
    user_id = user_info.get('id')
    slot = message.get('slot')
    action_type = message.get('action_type')  # 'melee_attack', 'ranged_attack', 'battlefield_move', None
    
    # 슬롯 확인
    if not slot:
        slot = game.get_player_by_user_id(user_id)
        if not slot:
            await websocket.send_json({
                "type": "tile_feedback_error",
                "message": "플레이어 슬롯을 찾을 수 없습니다"
            })
            return
    
    # 유효한 타일 계산
    feedback = game.get_tile_feedback(slot, action_type)
    
    # 클라이언트에 전송
    await websocket.send_json({
        "type": "tile_feedback",
        "valid_attack_tiles": feedback['valid_attack_tiles'],
        "valid_move_tiles": feedback['valid_move_tiles'],
        "action_type": action_type
    })
```


### Phase 6: 스킬 시스템 구현 (Skill System Implementation)

1. **스킬 데이터 구조 정의** (`server/skills.py`)
   - 구조화된 스킬 정의 (SkillDefinition)
   - `skill_id`, `name`, `lv`, `is_finisher`
   - `targeting`, `requires` (class/type/breed)
   - `priority_mod`, `power_mod` (int 또는 callable)
   - `flags` (예: ignore_cover)
   - `effects` (복잡한 효과는 Effect 클래스로 분리 가능)

2. **스킬 체인 처리**
   - 스킬 사용 가능 조건 검사 (lv, breed, per-battle 제한)
   - 행동 처리 전 스킬 효과 반영
   - `priority_mod`, `power_mod` 적용
   - `flags` 적용 (예: ignore_covering)

3. **스킬별 특수 로직**
   - 유도탄 (커버링 무시 플래그)
   - 컨토션 (회피 플래그)
   - 순간가속 (우선도 보정)
   - 등등...

### Phase 7: 프론트엔드 통합 (Frontend Integration)

1. **`src/hooks/useGame.js` 확장**
   - 전투 상태 관리
   - 행동 선언 함수
   - 전투 보드 상태
   - 타일 피드백 상태 관리 (`validAttackTiles`, `validMoveTiles`)
   - `requestTileFeedback()` 함수 추가
   - 타이머 상태 관리 (`timerState` - TIMER_PLAN.md 참고)
   - `timer_update` 메시지 핸들러 추가
   - 행동 선언 단계에서 타이머 표시 (60초 카운트다운)

**useGame 훅 확장 예시:**
```javascript
// src/hooks/useGame.js

export function useGame() {
  // ... 기존 코드 ...
  
  const [validAttackTiles, setValidAttackTiles] = useState([]);
  const [validMoveTiles, setValidMoveTiles] = useState([]);
  const [timerState, setTimerState] = useState({
    type: null,
    elapsed: 0,
    remaining: null,
    isRunning: false,
    duration: null
  });
  
  // WebSocket 메시지 핸들러에 추가
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    
    // ... 기존 메시지 처리 ...
    
    if (msg.type === "tile_feedback") {
      setValidAttackTiles(msg.valid_attack_tiles || []);
      setValidMoveTiles(msg.valid_move_tiles || []);
    } else if (msg.type === "timer_update") {
      // 타이머 업데이트 (TIMER_PLAN.md 참고)
      setTimerState({
        type: msg.timer_type,
        elapsed: msg.elapsed,
        remaining: msg.remaining,
        isRunning: msg.is_running,
        duration: msg.duration
      });
    } else if (msg.type === "action_declaration_phase") {
      // 행동 선언 단계 시작
      setCombatPhase('action_declaration');
      // 타이머는 timer_update 메시지로 별도 업데이트됨
    }
  };
  
  const requestTileFeedback = (actionType = null) => {
    messageGameWS({
      action: 'request_tile_feedback',
      action_type: actionType
    });
  };
  
  return {
    // ... 기존 반환값 ...
    validAttackTiles,
    validMoveTiles,
    requestTileFeedback,
    timerState  // 타이머 상태 추가
  };
}
```

2. **`src/components/room/` 컴포넌트 수정**
   - 행동 선언 UI
   - 전투 보드 표시
   - 우선도/해결 결과 표시
   - 타일 시각적 피드백 (색상 및 외곽선 스타일)
     - 공격 가능한 타일: 빨간색 외곽선 또는 배경
     - 이동 가능한 타일: 파란색 외곽선 또는 배경
     - 호버 효과 및 클릭 가능 표시

3. **타일 피드백 UI 구현 예시**
```javascript
// src/components/room/CombatBoard.jsx

import { useEffect, useState } from 'react';
import { useGame } from '../../hooks/useGame';

export default function CombatBoard() {
  const { validAttackTiles, validMoveTiles, requestTileFeedback } = useGame();
  const [selectedActionType, setSelectedActionType] = useState(null);
  
  // 행동 타입 선택 시 타일 피드백 요청
  useEffect(() => {
    if (selectedActionType) {
      requestTileFeedback(selectedActionType);
    }
  }, [selectedActionType, requestTileFeedback]);
  
  const getTileClassName = (pos) => {
    let classes = 'combat-tile';
    
    if (validAttackTiles.includes(pos)) {
      classes += ' valid-attack';
    }
    if (validMoveTiles.includes(pos)) {
      classes += ' valid-move';
    }
    
    return classes;
  };
  
  return (
    <div className="combat-board">
      {['Y', 'X', 'A', 'B'].map((row, r) => (
        <div key={row} className="board-row">
          {[1, 2, 3, 4].map((col) => {
            const pos = `${row}${col}`;
            return (
              <div
                key={pos}
                className={getTileClassName(pos)}
                onClick={() => handleTileClick(pos)}
              >
                {pos}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
```

```css
/* src/components/room/CombatBoard.css */

.combat-tile {
  width: 80px;
  height: 80px;
  border: 2px solid #333;
  background-color: #2a2a2a;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: default;
  transition: all 0.2s;
}

.combat-tile.valid-attack {
  border-color: #ff4444;
  background-color: rgba(255, 68, 68, 0.2);
  cursor: pointer;
}

.combat-tile.valid-attack:hover {
  border-color: #ff6666;
  background-color: rgba(255, 68, 68, 0.3);
  transform: scale(1.05);
}

.combat-tile.valid-move {
  border-color: #4444ff;
  background-color: rgba(68, 68, 255, 0.2);
  cursor: pointer;
}

.combat-tile.valid-move:hover {
  border-color: #6666ff;
  background-color: rgba(68, 68, 255, 0.3);
  transform: scale(1.05);
}

.combat-tile.valid-attack.valid-move {
  border-color: #ff44ff;
  background: linear-gradient(
    135deg,
    rgba(255, 68, 68, 0.2) 0%,
    rgba(68, 68, 255, 0.2) 100%
  );
}
```

---
