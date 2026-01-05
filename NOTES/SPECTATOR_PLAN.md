# 관전자 시스템 구현 계획 (Spectator System Implementation Plan)

## 개요 (Overview)

이 문서는 게임 시작 전/후 사용자 역할 관리 및 관전자 시스템 구현 계획을 담고 있습니다.

This document outlines the implementation plan for user role management and spectator system, where users who are not players after game start become spectators with access to a special 'Spectate' page that shows all secret messages.

---

## 1. 사용자 역할 정의 (User Role Definitions)

### 1.1 역할 타입 (Role Types)

```python
# 사용자 역할
ROLES = {
    'PLAYER': 'player',        # 게임 시작 전 슬롯에 참가한 사용자
    'SPECTATOR': 'spectator',  # 게임 시작 후 플레이어가 아닌 사용자
    'GUEST': 'guest',          # 인증되지 않은 게스트 사용자
    'GM': 'gm'                 # 게임 마스터 (선택적, 향후 확장)
}
```

### 1.2 역할 전환 규칙 (Role Transition Rules)

```
게임 시작 전 (Before Game Start):
  - 사용자는 슬롯에 참가하여 Player가 될 수 있음
  - 슬롯에 참가하지 않은 사용자는 아직 역할이 없음 (null/undefined)
  
게임 시작 후 (After Game Start):
  - 슬롯에 참가한 사용자 → Player 역할 유지
  - 슬롯에 참가하지 않은 사용자 → Spectator 역할로 자동 전환
  - Guest 사용자 → Guest 역할 유지 (Spectator가 될 수 없음)
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
        
        # 사용자 역할 관리
        self.user_roles = {}  # {user_id: role} - 'player', 'spectator', 'guest'
        self.spectators = []  # 관전자 user_id 리스트
```

### 2.2 사용자 역할 데이터 (User Role Data)

```python
user_role = {
    'user_id': 'user123',
    'role': 'spectator',  # 'player', 'spectator', 'guest'
    'slot': None,  # Player인 경우 슬롯 번호, 그 외는 None
    'joined_at': '2024-01-01T12:00:00',  # 게임 참가 시간
    'role_assigned_at': '2024-01-01T12:05:00'  # 역할 할당 시간
}
```

### 2.3 비밀 메시지 타입 (Secret Message Types)

```python
# 채팅 메시지의 sort 필드 확장
MESSAGE_TYPES = {
    'user': 'user',           # 일반 사용자 메시지
    'system': 'system',        # 시스템 메시지
    'secret': 'secret',         # 비밀 메시지 (GM, 행동 선언 등)
    'action_declare': 'action_declare',  # 행동 선언 (비밀)
    'gm_note': 'gm_note'       # GM 노트 (비밀)
}
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
   - user_roles[user_id] = 'player'
   - players 리스트에 추가
   ↓
4. 슬롯 미참가 사용자:
   - user_roles[user_id] = None (역할 없음)
   - 일반 게임 룸에서 대기
```

### 3.2 게임 시작 시 플로우 (Game Start Flow)

```
1. GM 또는 시스템이 게임 시작 명령
   ↓
2. game_started = True
   game_start_time = 현재 시간
   ↓
3. 모든 접속 사용자에 대해 역할 확인:
   ↓
   [플레이어 확인]
   - players 리스트에 있는 사용자 → role = 'player' 유지
   ↓
   [관전자 전환]
   - players 리스트에 없는 사용자
   - user_roles[user_id] = 'spectator'
   - spectators 리스트에 추가
   ↓
4. 모든 클라이언트에 게임 시작 알림 브로드캐스트
   - 자신의 역할 정보 포함
   ↓
5. Spectator 역할 사용자에게 Spectate 페이지로 이동 안내
```

### 3.3 관전자 페이지 접근 플로우 (Spectate Page Access Flow)

```
1. 사용자가 /spectate/:gameId 경로 접근 시도
   ↓
2. 서버에서 사용자 역할 확인
   ↓
3. 역할 검증:
   ↓
   [Spectator]
   - role == 'spectator' → 접근 허용
   - 모든 비밀 메시지 포함하여 게임 상태 전송
   ↓
   [Player]
   - role == 'player' → 접근 거부
   - "Players cannot access Spectate page" 메시지
   ↓
   [Guest]
   - role == 'guest' 또는 None → 접근 거부
   - "Guests cannot access Spectate page" 메시지
   ↓
4. 접근 허용 시:
   - Spectate 페이지 렌더링
   - 모든 메시지 (비밀 포함) 표시
   - 실시간 게임 상태 업데이트
```

### 3.4 비밀 메시지 처리 플로우 (Secret Message Processing Flow)

```
1. 비밀 메시지 생성 (행동 선언, GM 노트 등)
   ↓
2. 메시지 저장 시 sort = 'secret' 또는 특정 비밀 타입
   ↓
3. 메시지 브로드캐스트:
   ↓
   [일반 사용자/플레이어]
   - 비밀 메시지 필터링
   - 일반 메시지만 수신
   ↓
   [관전자]
   - 모든 메시지 수신 (비밀 포함)
   - Spectate 페이지에 표시
```

---

## 4. 백엔드 구현 (Backend Implementation)

### 4.1 Game 클래스 메서드 추가 (Game Class Methods)

```python
def start_game(self):
    """게임을 시작하고 사용자 역할을 할당"""
    if self.game_started:
        return {"success": False, "message": "Game already started"}
    
    self.game_started = True
    self.game_start_time = time.time()
    
    # 모든 접속 사용자에 대해 역할 할당
    player_user_ids = set()
    for player in self.players:
        if player.get('info') and player['info'].get('id'):
            user_id = player['info']['id']
            player_user_ids.add(user_id)
            self.user_roles[user_id] = 'player'
    
    # 관전자로 전환
    for user_id in self.users:
        if user_id not in player_user_ids:
            self.user_roles[user_id] = 'spectator'
            if user_id not in self.spectators:
                self.spectators.append(user_id)
    
    return {"success": True, "message": "Game started"}

def get_user_role(self, user_id: str) -> str | None:
    """사용자의 역할을 반환"""
    return self.user_roles.get(user_id)

def is_spectator(self, user_id: str) -> bool:
    """사용자가 관전자인지 확인"""
    return self.user_roles.get(user_id) == 'spectator'

def is_player(self, user_id: str) -> bool:
    """사용자가 플레이어인지 확인"""
    return self.user_roles.get(user_id) == 'player'

def can_access_spectate(self, user_id: str) -> bool:
    """사용자가 Spectate 페이지에 접근할 수 있는지 확인"""
    role = self.user_roles.get(user_id)
    return role == 'spectator' and self.game_started
```

### 4.2 WebSocket 핸들러 추가 (WebSocket Handlers)

```python
# server/game_ws.py

async def handle_start_game(websocket: WebSocket, message: dict, game):
    """게임 시작 처리"""
    user_info = conmanager.get_user_info(websocket)
    user_id = user_info.get('id')
    
    # 권한 확인 (GM 또는 특정 조건)
    # TODO: GM 권한 시스템 구현 시 추가
    
    result = game.start_game()
    
    if result["success"]:
        # 모든 클라이언트에 게임 시작 알림
        await conmanager.broadcast_to_game(game.id, {
            "type": "game_started",
            "start_time": game.game_start_time,
            "user_roles": game.user_roles  # 각 사용자에게 자신의 역할 포함
        })
        
        # 각 사용자에게 개별 역할 정보 전송
        for user_id, role in game.user_roles.items():
            # 해당 사용자의 WebSocket 찾기
            for conn in conmanager.get_game_connections(game.id):
                conn_user_info = conmanager.get_user_info(conn)
                if conn_user_info and conn_user_info.get('id') == user_id:
                    await conn.send_json({
                        "type": "role_assigned",
                        "role": role,
                        "redirect_to_spectate": role == 'spectator'
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
    
    # 게임 상태 전송 (모든 정보 포함)
    vomit_data = game.vomit()
    vomit_data['include_secrets'] = True  # 비밀 정보 포함 플래그
    await websocket.send_json(vomit_data)
    
    # 모든 채팅 메시지 전송 (비밀 메시지 포함)
    chat_history_rows = dbmanager.get_chat_history(game.id)
    chat_messages = []
    for row in chat_history_rows:
        # row format: (chat_id, sender, time, content, sort, user_id)
        chat_messages.append({
            "type": "chat",
            "sender": row[1],
            "time": row[2],
            "content": row[3],
            "sort": row[4],
            "user_id": row[5],
            "is_secret": row[4] in ['secret', 'action_declare', 'gm_note']  # 비밀 메시지 표시
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
    """채팅 메시지 처리 (기존 함수 수정)"""
    now = datetime.now().isoformat()
    content = message.get("content", "")
    sender = message.get("sender")
    user_info = conmanager.get_user_info(websocket)
    user_id = user_info.get('id')
    user_role = game.get_user_role(user_id)
    
    # 비밀 메시지 타입 확인
    is_secret = message.get("is_secret", False)
    message_sort = "secret" if is_secret else "user"
    
    if content and content[0] == "/":
        # 명령 처리
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
        # 일반 채팅 메시지
        msg = dbmanager.save_chat(game.id, sender, now, content, message_sort, user_id)
    
    # 메시지 브로드캐스트
    # 플레이어와 일반 사용자에게는 비밀 메시지 필터링
    # 관전자에게는 모든 메시지 전송
    for conn in conmanager.get_game_connections(game.id):
        conn_user_info = conmanager.get_user_info(conn)
        if conn_user_info:
            conn_user_id = conn_user_info.get('id')
            conn_role = game.get_user_role(conn_user_id)
            
            # 관전자는 모든 메시지 수신
            if conn_role == 'spectator':
                await conn.send_json(msg)
            # 플레이어와 기타 사용자는 비밀 메시지 제외
            elif not is_secret:
                await conn.send_json(msg)
```

### 4.3 DatabaseManager 확장 (Database Manager Extension)

```python
# server/util.py - DatabaseManager 클래스에 추가

def get_chat_history_for_spectator(self, game_id, limit=None):
    """관전자용 채팅 히스토리 (비밀 메시지 포함)"""
    query = f'SELECT chat_id, sender, time, content, sort, user_id FROM "{game_id}"'
    if limit:
        query += f' LIMIT {limit}'
    self.cursor.execute(query)
    messages = self.cursor.fetchall()
    return messages

def get_chat_history_for_player(self, game_id, limit=None):
    """플레이어용 채팅 히스토리 (비밀 메시지 제외)"""
    query = f'''SELECT chat_id, sender, time, content, sort, user_id 
               FROM "{game_id}" 
               WHERE sort NOT IN ('secret', 'action_declare', 'gm_note')'''
    if limit:
        query += f' LIMIT {limit}'
    self.cursor.execute(query)
    messages = self.cursor.fetchall()
    return messages
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
  const [gameStarted, setGameStarted] = useState(false);
  
  // WebSocket 메시지 핸들러에 추가
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    
    // ... 기존 메시지 처리 ...
    
    if (msg.type === "game_started") {
      setGameStarted(true);
      // 자신의 역할 확인
      const currentUserId = userInfo.id;
      const role = msg.user_roles[currentUserId];
      setUserRole(role);
      
      // 관전자인 경우 Spectate 페이지로 이동 안내
      if (role === 'spectator') {
        // 옵션 1: 자동 리다이렉트
        // window.location.href = `/spectate/${gameId}`;
        
        // 옵션 2: 안내 메시지 표시
        alert('게임이 시작되었습니다. 관전자 모드로 전환됩니다.');
        window.location.href = `/spectate/${gameId}`;
      }
    } else if (msg.type === "role_assigned") {
      setUserRole(msg.role);
      if (msg.redirect_to_spectate) {
        window.location.href = `/spectate/${gameId}`;
      }
    } else if (msg.type === "spectate_access_denied") {
      alert(msg.message);
      // Room 페이지로 리다이렉트
      window.location.href = `/room/${gameId}`;
    } else if (msg.type === "spectate_chat_history") {
      // 관전자용 채팅 히스토리 (비밀 메시지 포함)
      const messages = (msg.messages || []).map(chatMsg => ({
        sender: chatMsg.sort === "user" ? (chatMsg.sender || "noname") : "System",
        time: chatMsg.time,
        content: chatMsg.content,
        isSystem: chatMsg.sort === "system",
        isSecret: chatMsg.is_secret || false,  // 비밀 메시지 플래그
        user_id: chatMsg.user_id || null
      }));
      setChatMessages(messages);
    }
  };
  
  // ... 나머지 코드 ...
  
  return {
    // ... 기존 반환값 ...
    userRole,
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
    if (userRole !== 'spectator') {
      // 관전자가 아니면 접근 거부
      alert('관전자만 이 페이지에 접근할 수 있습니다.');
      navigate(`/room/${gameId}`);
    }
  }, [userRole, gameId, navigate]);
  
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
        
        {/* 채팅 (비밀 메시지 포함) */}
        <div className="spectate-chat">
          <div className="chat-log" ref={chatLogRef}>
            {chatMessages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`chat-message ${msg.isSecret ? 'secret-message' : ''}`}
              >
                <span className="chat-time">{msg.time}</span>
                <span className="chat-sender">{msg.sender}:</span>
                <span className="chat-content">{msg.content}</span>
                {msg.isSecret && (
                  <span className="secret-badge">[비밀]</span>
                )}
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

.chat-message.secret-message {
  background-color: rgba(255, 215, 0, 0.1);
  border-left: 3px solid #ffd700;
  padding-left: 8px;
}

.secret-badge {
  color: #ffd700;
  font-weight: bold;
  margin-left: 8px;
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

#### 비밀 메시지 전송 (GM 또는 시스템)
```json
{
    "action": "chat",
    "game_id": "game123",
    "sender": "GM",
    "content": "비밀 메시지 내용",
    "is_secret": true
}
```

### 6.2 서버 → 클라이언트 메시지 (Server → Client Messages)

#### 게임 시작 알림
```json
{
    "type": "game_started",
    "start_time": 1704110400,
    "user_roles": {
        "user1": "player",
        "user2": "player",
        "user3": "spectator",
        "user4": "spectator"
    }
}
```

#### 역할 할당
```json
{
    "type": "role_assigned",
    "role": "spectator",
    "redirect_to_spectate": true
}
```

#### Spectate 접근 거부
```json
{
    "type": "spectate_access_denied",
    "message": "Only spectators can access the Spectate page"
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
            "content": "일반 메시지",
            "sort": "user",
            "is_secret": false
        },
        {
            "sender": "System",
            "time": "2024-01-01T12:01:00",
            "content": "행동 선언: 근거리공격",
            "sort": "action_declare",
            "is_secret": true
        }
    ]
}
```

---

## 7. 구현 단계 (Implementation Steps)

### Phase 1: 백엔드 역할 관리 시스템 (Backend Role Management)

1. **`server/game_core.py` 수정**
   - `Game.__init__()`에 `game_started`, `user_roles`, `spectators` 추가
   - `start_game()` 메서드 구현
   - `get_user_role()`, `is_spectator()`, `is_player()`, `can_access_spectate()` 메서드 구현
   - `vomit()` 메서드에 역할 정보 포함

2. **`server/game_ws.py` 수정**
   - `handle_start_game()` 핸들러 구현
   - `handle_load_spectate()` 핸들러 구현
   - `handle_chat()` 수정 (비밀 메시지 필터링 로직 추가)

3. **`server/util.py` 수정**
   - `DatabaseManager`에 `get_chat_history_for_spectator()`, `get_chat_history_for_player()` 메서드 추가

### Phase 2: 프론트엔드 라우팅 및 컴포넌트 (Frontend Routing & Components)

1. **`src/App.jsx` 수정**
   - `/spectate/:gameId` 라우트 추가

2. **`src/components/spectate/Spectate.jsx` 생성**
   - 관전자 페이지 컴포넌트 구현
   - 비밀 메시지 표시 UI

3. **`src/components/spectate/Spectate.css` 생성**
   - 관전자 페이지 스타일

### Phase 3: 훅 확장 (Hook Extension)

1. **`src/hooks/useGame.js` 수정**
   - `userRole`, `gameStarted` 상태 추가
   - `loadSpectate()` 함수 추가
   - WebSocket 메시지 핸들러에 역할 관련 처리 추가

### Phase 4: 접근 제어 및 보안 (Access Control & Security)

1. **서버 측 접근 제어**
   - Spectate 페이지 접근 시 역할 검증
   - 비밀 메시지 필터링 로직 검증

2. **클라이언트 측 접근 제어**
   - Spectate 컴포넌트에서 역할 확인
   - 접근 거부 시 리다이렉트

### Phase 5: 테스트 및 검증 (Testing & Validation)

1. **기능 테스트**
   - 게임 시작 전/후 역할 전환 테스트
   - Spectate 페이지 접근 권한 테스트
   - 비밀 메시지 필터링 테스트

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

### 8.2 비밀 메시지 보호 (Secret Message Protection)

- 비밀 메시지는 데이터베이스에 저장되지만, 전송 시 필터링
- 관전자에게만 비밀 메시지 전송
- 메시지 타입(sort) 검증

### 8.3 접근 제어 (Access Control)

- Spectate 페이지 접근 시 서버에서 역할 재확인
- 게임 시작 전에는 Spectate 페이지 접근 불가
- Guest 사용자는 Spectate 페이지 접근 불가

---

## 9. 향후 확장 가능성 (Future Extensions)

### 9.1 GM 역할 (GM Role)

- GM은 모든 페이지에 접근 가능
- GM 전용 기능 (게임 시작, 비밀 메시지 작성 등)

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

### 10.2 역할 전환 (Role Transitions)

- 게임 시작 후 역할은 변경되지 않음
- 게임 종료 후 새 게임 시작 시 역할 재할당

### 10.3 비밀 메시지 정의 (Secret Message Definition)

- 현재는 `sort` 필드로 구분
- 향후 더 세밀한 권한 시스템으로 확장 가능

---

## 11. 테스트 시나리오 (Test Scenarios)

1. **시나리오 1: 게임 시작 전**
   - 사용자 A, B가 슬롯에 참가 → Player
   - 사용자 C가 게임에 접속하지만 슬롯 미참가 → 역할 없음
   - 게임 시작 → C가 Spectator로 전환

2. **시나리오 2: Spectate 페이지 접근**
   - Spectator가 `/spectate/:gameId` 접근 → 성공
   - Player가 `/spectate/:gameId` 접근 → 거부, Room으로 리다이렉트
   - Guest가 `/spectate/:gameId` 접근 → 거부

3. **시나리오 3: 비밀 메시지**
   - GM이 비밀 메시지 전송
   - Player는 비밀 메시지 수신 안 됨
   - Spectator는 비밀 메시지 수신 및 표시

4. **시나리오 4: 게임 시작 후 접속**
   - 게임 시작 후 새로운 사용자 D 접속
   - D는 자동으로 Spectator 역할 할당
   - D는 Spectate 페이지 접근 가능

