# 전투 단계 관리 시스템 (Combat Phase Management System)

## 개요 (Overview)

전투 단계 관리를 `PhaseManager` 클래스로 분리하여 코드를 모듈화하고 유지보수성을 향상시킵니다. `Game` 클래스는 `PhaseManager` 인스턴스를 가지고, 이를 통해 전투 단계 관리 기능을 사용합니다.

Phase management is separated into a `PhaseManager` class to modularize code and improve maintainability. The `Game` class has a `PhaseManager` instance and uses it for combat phase management functionality.

---

## 클래스 구조 (Class Structure)

### PhaseManager 클래스

```python
class PhaseManager:
    """
    전투 단계 관리를 담당하는 클래스.
    Game 인스턴스를 받아 Game의 상태에 접근합니다.
    
    PhaseManager manages combat phase transitions. Takes a Game instance to access game state.
    """
    
    # Phase 상수 정의
    PHASE_PREPARATION = 'preparation'
    PHASE_POSITION_DECLARATION = 'position_declaration'
    PHASE_ACTION_DECLARATION = 'action_declaration'
    PHASE_RESOLUTION = 'resolution'
    PHASE_WRAP_UP = 'wrap-up'
    
    def __init__(self, game):
        """
        Args:
            game: Game 인스턴스 (combat_state, timer, players에 접근하기 위해)
        """
        self.game = game
    
    def advance_combat_phase(self, to_phase=None):
        """
        전투 단계를 전환하고 플레이어에게 알림 메시지를 반환하는 마스터 함수.
        실제 WebSocket 전송은 game_ws.py에서 처리 (PLAN_WEBSOCKET.md 참고).
        
        Args:
            to_phase: 전환할 단계. None이면 현재 단계에 따라 자동 전환.
                가능한 값: 'position_declaration', 'action_declaration', 'resolution', 'wrap-up'
                
        Returns:
            {
                "success": bool,
                "phase": str,  # 새로운 단계
                "round": int,  # 현재 라운드
                "message": str,  # 플레이어에게 보낼 메시지
                "notification_type": str,  # WebSocket 메시지 타입
                "additional_data": dict  # 추가 데이터 (combat_board, timer 등)
            }
        """
        current_phase = self.game.combat_state['phase']
        current_round = self.game.combat_state['current_round']
        
        # to_phase가 지정되지 않으면 현재 단계에 따라 자동 전환
        # Flow: preparation → position_declaration → action_declaration → resolution → (loop) → wrap-up
        if to_phase is None:
            if current_phase == self.PHASE_PREPARATION:
                to_phase = self.PHASE_POSITION_DECLARATION
            elif current_phase == self.PHASE_POSITION_DECLARATION:
                to_phase = self.PHASE_ACTION_DECLARATION
            elif current_phase == self.PHASE_ACTION_DECLARATION:
                to_phase = self.PHASE_RESOLUTION
            elif current_phase == self.PHASE_RESOLUTION:
                to_phase = self.PHASE_ACTION_DECLARATION
            else:
                return {"success": False, "message": "유효하지 않은 단계 전환"}
        
        additional_data = {}
        
        if to_phase == self.PHASE_POSITION_DECLARATION:
            return self._handle_position_declaration_phase(additional_data)
        
        elif to_phase == self.PHASE_ACTION_DECLARATION:
            return self._handle_action_declaration_phase(additional_data)
        
        elif to_phase == self.PHASE_RESOLUTION:
            return self._handle_resolution_phase(additional_data)
        
        elif to_phase == self.PHASE_WRAP_UP:
            return self._handle_wrap_up_phase(additional_data)
        
        return {"success": False, "message": "알 수 없는 단계"}
    
    def _handle_position_declaration_phase(self, additional_data):
        """위치 선언 단계 처리"""
        self.game.combat_state['phase'] = self.PHASE_POSITION_DECLARATION
        self.game.combat_state['in_combat'] = True
        self.game.combat_state['current_round'] = 0
        message = '위치 선언 페이즈입니다. 시작 위치를 선언해주세요.'
        notification_type = 'position_declaration_phase'
        
        return {
            "success": True,
            "phase": self.game.combat_state['phase'],
            "round": self.game.combat_state['current_round'],
            "message": message,
            "notification_type": notification_type,
            "additional_data": additional_data
        }
    
    def _handle_action_declaration_phase(self, additional_data):
        """행동 선언 단계 처리"""
        self.game.combat_state['phase'] = self.PHASE_ACTION_DECLARATION
        if self.game.combat_state['current_round'] == 0:
            self.game.combat_state['current_round'] = 1
        message = '라운드 {} 선언 페이즈입니다. 스킬과 행동을 선언해주세요.'.format(self.game.combat_state['current_round'])
        notification_type = 'action_declaration_phase'
        
        # 타이머 시작 (60초)
        import time
        self.game.timer = {
            'type': 'action_declaration',
            'start_time': time.time(),
            'duration': 60,
            'is_running': True,
            'paused_at': None,
            'elapsed_before_pause': 0
        }
        additional_data['timer'] = self.game.timer
        
        return {
            "success": True,
            "phase": self.game.combat_state['phase'],
            "round": self.game.combat_state['current_round'],
            "message": message,
            "notification_type": notification_type,
            "additional_data": additional_data
        }
    
    def _handle_resolution_phase(self, additional_data):
        """해결 단계 처리"""
        self.game.combat_state['phase'] = self.PHASE_RESOLUTION
        message = '라운드 {} 선언이 끝났습니다. 계산을 시작합니다.'.format(self.game.combat_state['current_round'])
        notification_type = 'resolution_phase'
        
        # 타이머 정지
        import time
        if self.game.timer.get('is_running'):
            self.game.timer['is_running'] = False
            self.game.timer['elapsed_before_pause'] = time.time() - self.game.timer['start_time']
        
        return {
            "success": True,
            "phase": self.game.combat_state['phase'],
            "round": self.game.combat_state['current_round'],
            "message": message,
            "notification_type": notification_type,
            "additional_data": additional_data
        }
    
    def _handle_wrap_up_phase(self, additional_data):
        """전투 종료 단계 처리"""
        self.game.combat_state['phase'] = self.PHASE_WRAP_UP
        self.game.combat_state['in_combat'] = False
        message = '전투가 종료되었습니다.'
        notification_type = 'combat_ended'
        
        return {
            "success": True,
            "phase": self.game.combat_state['phase'],
            "round": self.game.combat_state['current_round'],
            "message": message,
            "notification_type": notification_type,
            "additional_data": additional_data
        }
    
    def get_combat_start_message(self):
        """전투 시작 메시지 반환"""
        return {
            "success": True,
            "phase": self.game.combat_state['phase'],
            "round": self.game.combat_state['current_round'],
            "message": '전투를 시작합니다.',
            "notification_type": "combat_starting"
        }
    
    def start_position_declaration_phase(self):
        """위치 선언 단계 시작 (전투 시작 후 호출)"""
        return self.advance_combat_phase(self.PHASE_POSITION_DECLARATION)
    
    def start_action_declaration_phase(self):
        """행동 선언 단계 시작 (위치 선언 완료 후 호출)"""
        return self.advance_combat_phase(self.PHASE_ACTION_DECLARATION)
    
    def start_resolution_phase(self):
        """해결 단계 시작 (행동 선언 완료 후 호출)"""
        return self.advance_combat_phase(self.PHASE_RESOLUTION)
    
    def get_round_summary_message(self):
        """라운드 요약 메시지 반환 (phase는 변경하지 않음)"""
        return {
            "success": True,
            "phase": self.game.combat_state['phase'],
            "round": self.game.combat_state['current_round'],
            "message": '라운드 {} 결과를 요약합니다.'.format(self.game.combat_state['current_round']),
            "notification_type": "round_summary"
        }
    
    def check_all_players_defeated(self):
        """
        한 팀의 모든 플레이어가 전투불능인지 확인
        
        Returns:
            tuple: (is_team_defeated: bool, defeated_team: int or None)
                - is_team_defeated: 한 팀이 전투불능인지 여부
                - defeated_team: 0=white team defeated, 1=blue team defeated, None=no team defeated
        """
        white_team_defeated = True
        blue_team_defeated = True
        
        for player in self.game.players:
            if player.get('occupy') != 1:
                continue
            if not player.get('character'):
                continue
            
            team = player.get('team')
            current_hp = player['character'].get('current_hp', 0)
            
            if team == 0:
                if current_hp > 0:
                    white_team_defeated = False
            elif team == 1:
                if current_hp > 0:
                    blue_team_defeated = False
        
        if white_team_defeated:
            return True, 0
        elif blue_team_defeated:
            return True, 1
        else:
            return False, None
    
    def end_round(self):
        """
        라운드 종료 처리 및 다음 단계로 전환
        
        Returns:
            dict: {
                "success": bool,
                "phase": str,
                "round": int,
                "message": str,
                "notification_type": str,
                "next_phase": dict or None
            }
        """
        summary_result = self.get_round_summary_message()
        is_team_defeated, defeated_team = self.check_all_players_defeated()
        
        if is_team_defeated:
            wrap_up_result = self.advance_combat_phase(self.PHASE_WRAP_UP)
            return {
                **summary_result,
                "next_phase": wrap_up_result
            }
        else:
            self.game.combat_state['current_round'] += 1
            action_decl_result = self.start_action_declaration_phase()
            return {
                **summary_result,
                "next_phase": action_decl_result
            }
```

---

## Game 클래스 통합 (Game Class Integration)

### 조합 구조 (Composition)

```python
# server/game_core.py

from server.phase_manager import PhaseManager

class Game:
    """
    게임 세션 관리 및 전투 시스템.
    PhaseManager 인스턴스를 가지고 전투 단계 관리 기능을 사용합니다.
    """
    
    def __init__(self, id, player_num=4):
        # ... 기존 코드 (players, game_board 등) ...
        
        # 전투 상태 초기화
        self.combat_state = {
            'in_combat': False,
            'current_round': 0,
            'phase': PhaseManager.PHASE_PREPARATION,
            'action_queue': [],
            'resolved_actions': []
        }
        
        self.timer = {
            'type': None,
            'start_time': None,
            'duration': None,
            'is_running': False,
            'paused_at': None,
            'elapsed_before_pause': 0
        }
        
        # PhaseManager 인스턴스 생성
        self.phase_manager = PhaseManager(self)
        
        # ... 나머지 초기화 코드 ...
```

---

## 설계 검증 (Design Validation)

### ✅ 장점 (Advantages)

1. **관심사 분리 (Separation of Concerns)**
   - 전투 단계 관리 로직이 `PhaseManager`에 집중
   - `Game` 클래스는 게임 전반의 상태 관리에 집중

2. **명확한 네임스페이스 (Clear Namespace)**
   - `game.phase_manager.method()` 형태로 호출하여 메서드 출처가 명확함
   - 여러 Manager 클래스 (PhaseManager, PosManager, SkillManager 등)를 사용할 때 혼동 방지

3. **느슨한 결합 (Loose Coupling)**
   - `PhaseManager`는 `Game` 인스턴스에만 의존
   - Manager를 교체하거나 Mock하기 쉬움

4. **확장성 (Extensibility)**
   - 여러 Manager 클래스를 조합하여 사용 가능
   - 다중 상속 문제 없음
   - 각 Manager를 독립적으로 테스트 가능

5. **유지보수성 (Maintainability)**
   - Phase 관련 로직 수정 시 `PhaseManager`만 수정
   - 코드 가독성 향상

---

## 구현 순서 (Implementation Order)

1. **PhaseManager 클래스 생성**
   - `server/phase_manager.py` 파일 생성
   - PhaseManager 클래스 및 모든 메서드 구현

2. **Game 클래스 수정**
   - `Game.__init__()`에서 `self.phase_manager = PhaseManager(self)` 추가
   - `from server.phase_manager import PhaseManager` 추가

3. **기존 코드에서 PhaseManager 메서드 제거**
   - `game_core.py`에서 phase 관리 관련 메서드 제거

4. **호출부 업데이트**
   - 기존 `game.method()` → `game.phase_manager.method()` 형태로 변경

5. **테스트**
   - Phase 전환 로직 테스트
   - Game 클래스와의 통합 테스트

---

## 사용 예시 (Usage Examples)

```python
# game_ws.py에서 사용 예시

from server.game_core import Game

# Game 인스턴스 생성
game = Game(game_id, player_num=4)

# 전투 시작
game.start_combat()  # Game 메서드
combat_start_msg = game.phase_manager.get_combat_start_message()
position_phase_result = game.phase_manager.start_position_declaration_phase()

# WebSocket 브로드캐스트
await conmanager.broadcast_to_game(game.id, {
    "type": position_phase_result['notification_type'],
    "phase": position_phase_result['phase'],
    "round": position_phase_result['round'],
    "message": position_phase_result['message'],
    **position_phase_result['additional_data']
})

# 라운드 종료
round_end_result = game.phase_manager.end_round()
if round_end_result.get('next_phase'):
    next_phase = round_end_result['next_phase']
    await conmanager.broadcast_to_game(game.id, {
        "type": next_phase['notification_type'],
        "phase": next_phase['phase'],
        "round": next_phase['round'],
        "message": next_phase['message'],
        **next_phase['additional_data']
    })
```

---

## 참고사항 (Notes)

- Phase 상수는 `PhaseManager` 클래스 변수로 정의하여 타입 안정성과 유지보수성을 향상시킵니다.
- `_handle_*_phase()` 메서드는 private 메서드 (Python naming convention)로, 내부 구현 세부사항을 숨깁니다.
- `PhaseManager`는 `self.game`을 통해 Game 인스턴스의 상태에 접근합니다.
- 여러 Manager 클래스를 사용할 때도 동일한 패턴으로 확장 가능합니다.
- 실제 WebSocket 전송은 `game_ws.py`에서 처리합니다 (PLAN_WEBSOCKET.md 참고).
