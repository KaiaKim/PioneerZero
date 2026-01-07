
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
    "skill_chain": "contortion"  // 스킬 ID
}
```

#### 타일 피드백 요청
```json
{
    "action": "request_tile_feedback",
    "game_id": "game123",
    "slot": 1,
    "action_type": "melee_attack"  // "melee_attack", "ranged_attack", "battlefield_move", null (모두)
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
