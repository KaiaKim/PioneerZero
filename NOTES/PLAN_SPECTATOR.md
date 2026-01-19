# 관전자 시스템 구현 계획 (Spectator System Implementation Plan)

## 개요 (Overview)

이 문서는 게임 시작 전/후 사용자 역할 관리 및 관전자 시스템 구현 계획을 담고 있습니다.

This document outlines the implementation plan for user role management and spectator system, where users who are not players (slot = None) become spectators with access to a special 'Spectate' page.

**핵심 원칙**: 역할은 slot 기반으로 단순하게 판단됩니다.
- slot이 있으면 → Player
- slot이 None이면 → Spectator
- 별도의 user_roles 딕셔너리 불필요
- slot 데이터는 players 리스트에 저장됨 (게임 세션별로 관리)

---

## 1. 사용자 역할 및 인증 상태 정의 (User Role and Auth State Definitions)

### 1.1 역할 타입 (Role Types)

```python
# 게임 내 역할 (Game Roles)
ROLES = {
    'PLAYER': 'player',        # 게임 시작 전 슬롯에 참가한 사용자
    'SPECTATOR': 'spectator'   # 게임 시작 후 플레이어가 아닌 사용자
}
```

### 1.2 인증 상태 타입 (Auth State Types)

```python
# 인증 상태 (Authentication State)
AUTH_STATES = {
    'GUEST': 'guest',    # 인증되지 않은 게스트 사용자
    'MEMBER': 'member',  # 인증된 일반 사용자
    'ADMIN': 'admin'     # 관리자 (GM - Game Master)
}
```

### 1.3 역할 전환 규칙 (Role Transition Rules)

```
게임 시작 전 (Before Game Start):
  - 사용자는 슬롯에 참가하여 Player 역할을 가질 수 있음
  - 슬롯에 참가하지 않은 사용자는 아직 역할이 없음 (null/undefined)
  
게임 시작 후 (After Game Start):
  - 슬롯에 참가한 사용자 → Player 역할 유지
  - 슬롯에 참가하지 않은 사용자 → Spectator 역할로 자동 전환
  - 단, Guest 인증 상태 사용자는 Spectator가 될 수 없음 (인증 필요)
```

### 1.4 역할과 인증 상태의 관계 (Role vs Auth State)

```
역할 (Role): 게임 내에서의 위치
  - player: 게임에 직접 참여하는 플레이어
  - spectator: 게임을 관전하는 관전자

인증 상태 (Auth State): 시스템 접근 권한
  - guest: 인증되지 않음, 제한된 기능만 사용 가능
  - member: 인증됨, 일반 기능 사용 가능
  - admin: 관리자 권한, 모든 기능 사용 가능 (GM 기능 포함)

Spectate 페이지 접근 조건:
  - 역할: spectator
  - 인증 상태: member 또는 admin (guest는 접근 불가)
```

---

## 2. 데이터 구조 (Data Structures)

### 2.1 Game 클래스 확장 (Game Class Extension)

```python
class Game():
    def __init__(self, id, player_num=4):
        # ... 기존 코드 ...
        
        # 게임 상태
        self.game_started = False  # 게임 시작 여부
        self.game_start_time = None  # 게임 시작 시간
        
        # Note: 역할은 slot 기반으로 판단
        # - slot이 None이면 spectator
        # - slot이 있으면 player
        # slot 정보는 players 리스트에 저장됨 (게임 세션별로 관리)
```

### 2.2 사용자 역할 판단 (User Role Determination)

```python
# 역할은 slot 기반으로 단순하게 판단
# - get_player_by_user_id(user_id)가 None을 반환하면 spectator
# - get_player_by_user_id(user_id)가 slot 번호를 반환하면 player

# slot 데이터는 players 리스트에 저장됨:
# players[slot_idx] = {
#     'info': user_info,  # {'id': '...', 'name': '...', 'auth_state': '...'}
#     'slot': slot,       # 슬롯 번호 (1-based)
#     ...
# }
```

---

## 3. 데이터 플로우 (Data Flow)

### 3.1 게임 시작 전 플로우 (Before Game Start Flow)

```
1. 사용자가 게임에 접속
   ↓
2. 사용자는 슬롯에 참가할 수 있음
   ↓
3. 슬롯 참가 시:
   - players 리스트의 해당 슬롯에 사용자 정보 저장
   - slot 번호가 할당됨
   ↓
4. 슬롯 미참가 사용자:
   - players 리스트에 없음 (slot = None)
   - 일반 게임 룸에서 대기
```

### 3.2 게임 시작 시 플로우 (Game Start Flow)

```
1. Admin (GM) 또는 시스템이 게임 시작 명령
   ↓
2. game_started = True
   game_start_time = 현재 시간
   ↓
3. 역할은 slot 기반으로 자동 판단:
   ↓
   [플레이어]
   - get_player_by_user_id(user_id)가 slot 번호 반환 → player
   ↓
   [관전자]
   - get_player_by_user_id(user_id)가 None 반환 → spectator
   - 단, 인증 상태가 'guest'인 경우 Spectate 페이지 접근 불가
   ↓
4. 모든 클라이언트에 게임 시작 알림 브로드캐스트
   - 각 사용자의 slot 정보 포함 (None이면 spectator)
   ↓
5. Spectator 사용자에게 Spectate 페이지로 이동 안내
   (인증 상태가 'member' 또는 'admin'인 경우만)
```

### 3.3 관전자 페이지 접근 플로우 (Spectate Page Access Flow)

```
1. 사용자가 /spectate/:gameId 경로 접근 시도
   ↓
2. 서버에서 사용자 slot 및 인증 상태 확인
   ↓
3. 접근 권한 검증:
   ↓
   [조건 1: 역할 확인 (slot 기반)]
   - get_player_by_user_id(user_id) == None → spectator (조건 만족)
   - get_player_by_user_id(user_id) != None → player (조건 불만족)
   ↓
   [조건 2: 인증 상태 확인]
   - auth_state == 'member' 또는 'admin' → 인증 조건 만족
   - auth_state == 'guest' → 인증 조건 불만족
   ↓
   [접근 허용]
   - is_spectator(user_id) == True AND (auth_state == 'member' OR auth_state == 'admin')
   - 게임 상태 전송
   ↓
   [접근 거부]
   - is_player(user_id) == True → "Players cannot access Spectate page"
   - auth_state == 'guest' → "Guests cannot access Spectate page"
   ↓
4. 접근 허용 시:
   - Spectate 페이지 렌더링
   - 실시간 게임 상태 업데이트
```

---

## 4. 백엔드 구현 (Backend Implementation)

### 4.1 Game 클래스 메서드 추가 (Game Class Methods)

```python
def start_game(self):
    """게임을 시작"""
    if self.game_started:
        return {"success": False, "message": "Game already started"}
    
    self.game_started = True
    self.game_start_time = time.time()
    
    # 역할은 slot 기반으로 자동 판단되므로 별도 할당 불필요
    # - slot이 있으면 player
    # - slot이 None이면 spectator
    
    return {"success": True, "message": "Game started"}

def get_user_slot(self, user_id: str) -> int | None:
    """사용자의 slot 번호를 반환 (None이면 spectator)"""
    return self.get_player_by_user_id(user_id)

def is_spectator(self, user_id: str) -> bool:
    """사용자가 관전자인지 확인 (slot이 None이면 spectator)"""
    slot = self.get_player_by_user_id(user_id)
    return slot is None

def is_player(self, user_id: str) -> bool:
    """사용자가 플레이어인지 확인 (slot이 있으면 player)"""
    slot = self.get_player_by_user_id(user_id)
    return slot is not None

def get_user_auth_state(self, user_id: str) -> str:
    """사용자의 인증 상태를 반환"""
    # players 리스트에서 user_info 찾기
    for player in self.players:
        if player.get('info') and player['info'].get('id') == user_id:
            return player['info'].get('auth_state', 'guest')
    
    # players 리스트에 없으면 ConnectionManager에서 찾기
    # TODO: ConnectionManager에서 user_info 가져오기
    return 'guest'  # 기본값

def can_access_spectate(self, user_id: str) -> bool:
    """사용자가 Spectate 페이지에 접근할 수 있는지 확인"""
    # slot이 None이어야 함 (spectator)
    if not self.is_spectator(user_id):
        return False
    
    # 인증 상태가 member 또는 admin이어야 함
    auth_state = self.get_user_auth_state(user_id)
    if auth_state not in ['member', 'admin']:
        return False
    
    # 게임이 시작되어야 함
    if not self.game_started:
        return False
    
    return True
```

### 4.2 WebSocket 핸들러 추가 (WebSocket Handlers)

```python
# server/game_ws.py

async def handle_start_game(websocket: WebSocket, message: dict, game):
    """게임 시작 처리"""
    user_info = conmanager.get_user_info(websocket)
    user_id = user_info.get('id')
    auth_state = user_info.get('auth_state', 'guest')
    
    # 권한 확인: Admin (GM)만 게임 시작 가능
    if auth_state != 'admin':
        await websocket.send_json({
            "type": "start_game_failed",
            "message": "Only admins (GM) can start the game"
        })
        return
    
    result = game.start_game()
    
    if result["success"]:
        # 모든 클라이언트에 게임 시작 알림
        # 각 사용자에게 자신의 slot 정보 포함 (None이면 spectator)
        user_slots = {}
        for user_id in game.users:
            slot = game.get_user_slot(user_id)
            auth_state = game.get_user_auth_state(user_id)
            user_slots[user_id] = {
                'slot': slot,  # None이면 spectator, 숫자면 player
                'auth_state': auth_state
            }
        
        await conmanager.broadcast_to_game(game.id, {
            "type": "game_started",
            "start_time": game.game_start_time,
            "user_slots": user_slots  # slot과 인증 상태 포함
        })
        
        # 각 사용자에게 개별 정보 전송
        for user_id in game.users:
            slot = game.get_user_slot(user_id)
            auth_state = game.get_user_auth_state(user_id)
            is_spectator = slot is None
            
            # 해당 사용자의 WebSocket 찾기
            for conn in conmanager.get_game_connections(game.id):
                conn_user_info = conmanager.get_user_info(conn)
                if conn_user_info and conn_user_info.get('id') == user_id:
                    await conn.send_json({
                        "type": "role_assigned",
                        "slot": slot,  # None이면 spectator
                        "auth_state": auth_state,
                        "redirect_to_spectate": (is_spectator and 
                                                 auth_state in ['member', 'admin'])
                    })
    else:
        await websocket.send_json({
            "type": "start_game_failed",
            "message": result["message"]
        })

async def handle_load_spectate(websocket: WebSocket, message: dict, game):
    """Spectate 페이지 로드 처리"""
    user_info = conmanager.get_user_info(websocket)
    user_id = user_info.get('id')
    
    # 접근 권한 확인
    if not game.can_access_spectate(user_id):
        await websocket.send_json({
            "type": "spectate_access_denied",
            "message": "Only spectators can access the Spectate page"
        })
        return
    
    # 게임 상태 전송
    vomit_data = game.vomit()
    await websocket.send_json(vomit_data)
    
    # 채팅 히스토리 전송
    chat_history_rows = dbmanager.get_chat_history(game.id)
    chat_messages = []
    for row in chat_history_rows:
        chat_messages.append({
            "type": "chat",
            "sender": row[1],
            "time": row[2],
            "content": row[3],
            "sort": row[4],
            "user_id": row[5]
        })
    
    await websocket.send_json({
        "type": "spectate_chat_history",
        "messages": chat_messages
    })
    
    # 사용자 목록 전송
    await websocket.send_json({
        "type": "users_list",
        "users": game.users
    })
    
    # 플레이어 목록 전송
    await websocket.send_json({
        "type": "players_list",
        "players": game.players
    })

async def handle_chat(websocket: WebSocket, message: dict, game):
    """채팅 메시지 처리"""
    now = datetime.now().isoformat()
    content = message.get("content", "")
    sender = message.get("sender")
    user_info = conmanager.get_user_info(websocket)
    user_id = user_info.get('id')
    
    if content and content[0] == "/":
        command = content[1:]
        result = "unknown command"
        if "이동" in command:
            result = game.move_player(sender, command)
        elif "스킬" in command:
            result = "스킬 사용함"
        elif "행동" in command:
            result = "행동함"
        msg = dbmanager.save_chat(game.id, "System", now, result, "system", None)
    else:
        msg = dbmanager.save_chat(game.id, sender, now, content, "user", user_id)
    
    await conmanager.broadcast_to_game(game.id, msg)
```


---

## 5. 프론트엔드 구현 (Frontend Implementation)

### 5.1 라우팅 추가 (Routing)

```javascript
// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Lobby from './components/lobby';
import Room from './components/room/Room';
import Spectate from './components/spectate/Spectate';  // 새 컴포넌트
import MyCharacter from './components/MyCharacter';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Lobby />} />
        <Route path="/room/:gameId" element={<Room />} />
        <Route path="/spectate/:gameId" element={<Spectate />} />
        <Route path="/edit-character" element={<MyCharacter />} />
      </Routes>
    </Router>
  );
}

export default App;
```

### 5.2 useGame 훅 확장 (useGame Hook Extension)

```javascript
// src/hooks/useGame.js

export function useGame() {
  // ... 기존 코드 ...
  
  const [userRole, setUserRole] = useState(null);  // 'player', 'spectator', null
  const [authState, setAuthState] = useState(null);  // 'guest', 'member', 'admin'
  const [gameStarted, setGameStarted] = useState(false);
  
  // WebSocket 메시지 핸들러에 추가
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    
    // ... 기존 메시지 처리 ...
    
    if (msg.type === "game_started") {
      setGameStarted(true);
      // 자신의 slot 및 인증 상태 확인
      const currentUserId = userInfo.id;
      const userSlotData = msg.user_slots[currentUserId];
      const slot = userSlotData?.slot;
      const authState = userSlotData?.auth_state;
      
      // slot이 null이면 spectator
      setUserRole(slot === null ? 'spectator' : 'player');
      setAuthState(authState);
      
      // 관전자이고 인증된 사용자인 경우 Spectate 페이지로 이동 안내
      if (slot === null && authState && ['member', 'admin'].includes(authState)) {
        // 옵션 1: 자동 리다이렉트
        // window.location.href = `/spectate/${gameId}`;
        
        // 옵션 2: 안내 메시지 표시
        alert('게임이 시작되었습니다. 관전자 모드로 전환됩니다.');
        window.location.href = `/spectate/${gameId}`;
      }
    } else if (msg.type === "role_assigned") {
      // slot이 null이면 spectator
      setUserRole(msg.slot === null ? 'spectator' : 'player');
      setAuthState(msg.auth_state);
      if (msg.redirect_to_spectate) {
        window.location.href = `/spectate/${gameId}`;
      }
    } else if (msg.type === "spectate_access_denied") {
      alert(msg.message);
      // Room 페이지로 리다이렉트
      window.location.href = `/room/${gameId}`;
    } else if (msg.type === "spectate_chat_history") {
      const messages = (msg.messages || []).map(chatMsg => ({
        sender: chatMsg.sort === "user" ? (chatMsg.sender || "noname") : "System",
        time: chatMsg.time,
        content: chatMsg.content,
        isSystem: chatMsg.sort === "system",
        user_id: chatMsg.user_id || null
      }));
      setChatMessages(messages);
    }
  };
  
  // ... 나머지 코드 ...
  
  return {
    // ... 기존 반환값 ...
    userRole,
    authState,
    gameStarted,
    loadSpectate  // 새 함수
  };
}

const loadSpectate = () => {
  messageGameWS({
    action: 'load_spectate'
  });
};
```

### 5.3 Spectate 컴포넌트 생성 (Spectate Component)

```javascript
// src/components/spectate/Spectate.jsx

import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGame } from '../../hooks/useGame';
import './Spectate.css';

export default function Spectate() {
  const { gameId } = useParams();
  const navigate = useNavigate();
  const {
    gameData,
    chatMessages,
    players,
    users,
    userRole,
    authState,
    gameStarted,
    loadSpectate,
    sendChat,
    chatLogRef
  } = useGame();
  
  useEffect(() => {
    // 컴포넌트 마운트 시 Spectate 데이터 로드
    loadSpectate();
  }, [gameId]);
  
  // 접근 권한 확인
  useEffect(() => {
    // 역할과 인증 상태 모두 확인
    if (userRole !== 'spectator' || !authState || authState === 'guest') {
      // 관전자가 아니거나 Guest 인증 상태면 접근 거부
      if (userRole !== 'spectator') {
        alert('관전자만 이 페이지에 접근할 수 있습니다.');
      } else if (authState === 'guest') {
        alert('인증된 사용자만 이 페이지에 접근할 수 있습니다.');
      }
      navigate(`/room/${gameId}`);
    }
  }, [userRole, authState, gameId, navigate]);
  
  return (
    <div className="spectate-container">
      <div className="spectate-header">
        <h1>관전 모드 - Game {gameId}</h1>
        <button onClick={() => navigate(`/room/${gameId}`)}>
          일반 뷰로 돌아가기
        </button>
      </div>
      
      <div className="spectate-content">
        {/* 게임 보드 */}
        <div className="spectate-game-board">
          {/* 게임 보드 표시 */}
        </div>
        
        {/* 채팅 */}
        <div className="spectate-chat">
          <div className="chat-log" ref={chatLogRef}>
            {chatMessages.map((msg, idx) => (
              <div key={idx} className="chat-message">
                <span className="chat-time">{msg.time}</span>
                <span className="chat-sender">{msg.sender}:</span>
                <span className="chat-content">{msg.content}</span>
              </div>
            ))}
          </div>
          
          {/* 채팅 입력 (관전자는 읽기 전용 또는 제한적) */}
          <div className="chat-input">
            <input 
              type="text" 
              placeholder="관전자 채팅 (선택적)"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  sendChat(e.target.value);
                  e.target.value = '';
                }
              }}
            />
          </div>
        </div>
        
        {/* 플레이어 정보 */}
        <div className="spectate-players">
          <h3>플레이어 목록</h3>
          {players.map((player, idx) => (
            <div key={idx} className="player-info">
              {player.info && (
                <>
                  <span>{player.info.name}</span>
                  <span>Slot {player.slot}</span>
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### 5.4 Spectate 스타일 (Spectate Styles)

```css
/* src/components/spectate/Spectate.css */

.spectate-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #1a1a1a;
  color: #fff;
}

.spectate-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background-color: #2a2a2a;
  border-bottom: 2px solid #444;
}

.spectate-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  grid-template-rows: 1fr auto;
  gap: 20px;
  padding: 20px;
  flex: 1;
  overflow: hidden;
}

.spectate-game-board {
  grid-column: 1;
  grid-row: 1 / 3;
  background-color: #2a2a2a;
  border-radius: 8px;
  padding: 20px;
}

.spectate-chat {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  flex-direction: column;
  background-color: #2a2a2a;
  border-radius: 8px;
  padding: 20px;
}

.chat-log {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 10px;
}

.chat-message {
  margin-bottom: 8px;
  padding: 4px;
}

.spectate-players {
  grid-column: 2;
  grid-row: 2;
  background-color: #2a2a2a;
  border-radius: 8px;
  padding: 20px;
}

.player-info {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  margin-bottom: 4px;
  background-color: #333;
  border-radius: 4px;
}
```

---

## 6. WebSocket 메시지 프로토콜 (WebSocket Message Protocol)

### 6.1 클라이언트 → 서버 메시지 (Client → Server Messages)

#### 게임 시작
```json
{
    "action": "start_game",
    "game_id": "game123"
}
```

#### Spectate 페이지 로드
```json
{
    "action": "load_spectate",
    "game_id": "game123"
}
```

### 6.2 서버 → 클라이언트 메시지 (Server → Client Messages)

#### 게임 시작 알림
```json
{
    "type": "game_started",
    "start_time": 1704110400,
    "user_slots": {
        "user1": {
            "slot": 1,
            "auth_state": "member"
        },
        "user2": {
            "slot": 2,
            "auth_state": "member"
        },
        "user3": {
            "slot": null,
            "auth_state": "member"
        },
        "user4": {
            "slot": null,
            "auth_state": "admin"
        }
    }
}
```

#### 역할 할당
```json
{
    "type": "role_assigned",
    "slot": null,
    "auth_state": "member",
    "redirect_to_spectate": true
}
```

#### Spectate 접근 거부
```json
{
    "type": "spectate_access_denied",
    "message": "Only authenticated spectators can access the Spectate page",
    "reason": "role_mismatch" | "auth_denied" | "not_started"
}
```

#### Spectate 채팅 히스토리
```json
{
    "type": "spectate_chat_history",
    "messages": [
        {
            "sender": "Player1",
            "time": "2024-01-01T12:00:00",
            "content": "메시지",
            "sort": "user"
        }
    ]
}
```

---

## 7. 구현 단계 (Implementation Steps)

### Phase 1: 백엔드 역할 관리 시스템 (Backend Role Management)

1. **`server/game_core.py` 수정**
   - `Game.__init__()`에 `game_started`, `game_start_time` 추가
   - `start_game()` 메서드 구현
   - `get_user_slot()`, `is_spectator()`, `is_player()`, `can_access_spectate()` 메서드 구현
   - `get_user_auth_state()` 메서드 구현
   - `vomit()` 메서드에 slot 정보 포함
   - Note: slot 데이터는 이미 players 리스트에 저장됨 (게임 세션별로 관리)

2. **`server/game_ws.py` 수정**
   - `handle_start_game()` 핸들러 구현
   - `handle_load_spectate()` 핸들러 구현

### Phase 2: 프론트엔드 라우팅 및 컴포넌트 (Frontend Routing & Components)

1. **`src/App.jsx` 수정**
   - `/spectate/:gameId` 라우트 추가

2. **`src/components/spectate/Spectate.jsx` 생성**
   - 관전자 페이지 컴포넌트 구현

3. **`src/components/spectate/Spectate.css` 생성**
   - 관전자 페이지 스타일

### Phase 3: 훅 확장 (Hook Extension)

1. **`src/hooks/useGame.js` 수정**
   - `userRole`, `gameStarted` 상태 추가
   - `loadSpectate()` 함수 추가
   - WebSocket 메시지 핸들러에 역할 관련 처리 추가

### Phase 4: 접근 제어 및 보안

1. **서버 측 접근 제어**
   - Spectate 페이지 접근 시 역할 검증

2. **클라이언트 측 접근 제어**
   - Spectate 컴포넌트에서 역할 확인
   - 접근 거부 시 리다이렉트

### Phase 5: 테스트 및 검증 (Testing & Validation)

1. **기능 테스트**
   - 게임 시작 전/후 slot 기반 역할 판단 테스트
   - Spectate 페이지 접근 권한 테스트 (slot이 None이고 인증된 사용자)
   - slot 데이터 게임 세션별 저장 테스트

2. **통합 테스트**
   - 여러 사용자 동시 접속 시나리오
   - 게임 시작 후 관전자 자동 전환
   - Spectate 페이지 실시간 업데이트

---

## 8. 보안 고려사항 (Security Considerations)

### 8.1 서버 측 검증 (Server-Side Validation)

- 모든 역할 확인은 서버에서 수행
- 클라이언트에서 전송한 역할 정보를 신뢰하지 않음
- WebSocket 연결 시 사용자 인증 정보 확인

### 8.2 접근 제어

- Spectate 페이지 접근 시 서버에서 역할과 인증 상태 모두 재확인
- 게임 시작 전에는 Spectate 페이지 접근 불가
- Guest 인증 상태 사용자는 Spectate 페이지 접근 불가 (인증 필요)
- Player 역할 사용자는 Spectate 페이지 접근 불가

---

## 9. 향후 확장 가능성 (Future Extensions)

### 9.1 Admin (GM) 인증 상태

- Admin 인증 상태는 GM 기능을 포함
- Admin은 모든 페이지에 접근 가능
- Admin 전용 기능 (게임 시작 등)
- Admin도 게임 내에서는 Player 또는 Spectator 역할을 가짐

### 9.2 관전자 채팅 (Spectator Chat)

- 관전자 간 채팅 기능
- 관전자 채팅은 플레이어에게 표시되지 않음

### 9.3 관전자 수 제한 (Spectator Limit)

- 최대 관전자 수 설정
- 관전자 대기열 시스템

### 9.4 관전 모드 기능 확장 (Extended Spectate Features)

- 게임 통계 표시
- 행동 선언 실시간 표시
- 우선도 계산 과정 표시

---

## 10. 주의사항 (Notes)

### 10.1 게임 시작 시점 (Game Start Timing)

- 게임 시작은 명시적인 명령으로만 수행
- 게임 시작 후에는 슬롯 참가 불가 (또는 제한적)

### 10.2 역할 판단 (Role Determination)

- 역할은 slot 기반으로 자동 판단됨 (별도 저장 불필요)
- slot이 있으면 Player, slot이 None이면 Spectator
- 게임 시작 후에도 slot 변경 가능 (슬롯 참가/탈퇴 시 역할 자동 변경)
- slot 데이터는 players 리스트에 저장됨 (게임 세션별로 관리)

---

## 11. 테스트 시나리오 (Test Scenarios)

1. **시나리오 1: 게임 시작 전**
   - 사용자 A (member), B (member)가 슬롯에 참가 → slot 1, 2 할당 (Player)
   - 사용자 C (member)가 게임에 접속하지만 슬롯 미참가 → slot = None (Spectator)
   - 사용자 D (guest)가 게임에 접속 → slot = None, 인증 상태: guest
   - 게임 시작 → C는 Spectator (slot = None), D는 Spectator이지만 Spectate 접근 불가 (guest)

2. **시나리오 2: Spectate 페이지 접근**
   - Spectator (member)가 `/spectate/:gameId` 접근 → 성공
   - Spectator (admin)가 `/spectate/:gameId` 접근 → 성공
   - Player (member)가 `/spectate/:gameId` 접근 → 거부 (역할 불일치)
   - Guest가 `/spectate/:gameId` 접근 → 거부 (인증 상태 불일치)

3. **시나리오 3: 게임 시작 후 접속**
   - 게임 시작 후 새로운 사용자 E (member) 접속
   - E는 slot = None (Spectator)
   - E는 Spectate 페이지 접근 가능 (member 인증 상태)
   - 게임 시작 후 새로운 사용자 F (guest) 접속
   - F는 slot = None (Spectator)
   - F는 Spectate 페이지 접근 불가 (guest 인증 상태)

