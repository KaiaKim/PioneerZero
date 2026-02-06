슬래시 커맨드는 **입력 파이프라인을 분리**해서 설계 

## 1. 전체 흐름 개요

```
raw chat input
 ├─ normal chat message
 └─ slash command (/...)
        ↓
    tokenize
        ↓
    command router
        ↓
    command handler
        ↓
    result (message / state change / error)
```

핵심은 **채팅 메시지 처리와 커맨드 처리를 처음부터 분리**하는 것입니다.

---

## 2. 입력 파싱 단계

### 규칙

* `/` 로 시작하면 커맨드
* 공백 기준으로 토큰화
* 첫 토큰 = command name
* 나머지 = args

```python
from dataclasses import dataclass
from typing import List


@dataclass
class CommandContext:
    user_id: str
    channel_id: str
    raw: str
    args: List[str]


def parse_input(text: str) -> tuple[str, CommandContext | None]:
    if not text.startswith("/"):
        return "chat", None

    tokens = text[1:].split()
    command = tokens[0].lower()
    args = tokens[1:]

    ctx = CommandContext(
        user_id="user_id",
        channel_id="channel_id",
        raw=text,
        args=args,
    )

    return command, ctx
```

---

## 3. 커맨드 라우터

**dict 기반 디스패치**가 가장 단순하고 강력합니다.

```python
from typing import Callable, Dict


CommandHandler = Callable[[CommandContext], None]


class CommandRouter:
    def __init__(self):
        self._handlers: Dict[str, CommandHandler] = {}

    def register(self, name: str, handler: CommandHandler) -> None:
        self._handlers[name] = handler

    def dispatch(self, command: str, ctx: CommandContext) -> None:
        if command not in self._handlers:
            raise ValueError(f"Unknown command: {command}")
        self._handlers[command](ctx)
```

---

## 4. 커맨드 핸들러 구조

### 규칙

* **한 커맨드 = 한 파일**
* 로직은 얇게, 실제 처리는 서비스 계층으로 위임

```python
def move_command(ctx: CommandContext) -> None:
    sides = int(ctx.args[0]) if ctx.args else 6
    result = random.randint(1, sides)
    send_message(ctx.channel_id, f"Rolled: {result}")
```

등록:

```python
router = CommandRouter()
router.register("move", move_command)
router.register("attack", attack_command)
```

---

## 5. 권장 디렉터리 구조

```
chat/
 ├─ input.py          # parse_input
 ├─ router.py         # CommandRouter
 ├─ context.py        # CommandContext
 └─ commands/
      ├─ move.py
      ├─ attack.py
      └─ skill.py
```

이 구조의 장점:

* 커맨드 추가 시 **파일 하나만 추가**
* 테스트가 쉬움
* 권한/쿨타임/로그 삽입이 간단

---

## 6. 권한, 쿨타임 확장 포인트

### Decorator 패턴

```python
def require_admin(handler: CommandHandler) -> CommandHandler:
    def wrapper(ctx: CommandContext):
        if not is_admin(ctx.user_id):
            raise PermissionError("Permission denied")
        return handler(ctx)
    return wrapper
```

```python
router.register("shutdown", require_admin(shutdown_command))
```

---

## 7. 비동기 환경 (WebSocket / FastAPI)

이미 잘 보신 구조입니다.
**파싱 → 라우팅 → 실행**을 task로 분리하면 됩니다.

```python
async def handle_message(text: str):
    command, ctx = parse_input(text)

    if command == "chat":
        await handle_chat(text)
    else:
        asyncio.create_task(router.dispatch(command, ctx))
```

