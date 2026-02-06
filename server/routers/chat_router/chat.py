"""
Chat and slash-command entry point.
Parse → route → handler; normal chat and commands are split at input.
"""
from fastapi import WebSocket

from ...util import conM, dbM
from .context import CommandContext
from .input import parse_input
from .router import CommandRouter
from . import commands

# --- Router setup: one handler per command name ---
_router = CommandRouter()

for _name in commands.attack.ATTACK_COMMANDS:
    _router.register(_name, commands.attack.attack_command)
for _name in commands.skill.SKILL_COMMANDS:
    _router.register(_name, commands.skill.skill_command)
for _name in commands.position.POSITION_COMMANDS:
    _router.register(_name, commands.position.position_command)
for _name in ("참여", "join", "관전", "leave"):
    _router.register(_name, commands.preparation.preparation_command)


async def handle_chat(websocket: WebSocket, message: dict, game) -> None:
    """Handle chat messages and slash commands. Input pipeline: parse → route → handler."""
    content = message.get("content", "")
    sender = message.get("sender")
    chat_type = message.get("chat_type", "dialogue")
    if chat_type not in ("dialogue", "communication", "chitchat"):
        chat_type = "dialogue"
    user_info = conM.get_user_info(websocket)
    user_id = user_info.get("id")

    command, args = parse_input(content)

    if command == "chat":
        # Normal chat
        msg = _save_regular_chat(game, content, sender, user_id, chat_type)
        await conM.broadcast_to_game(game.id, msg)
        return

    if command == "" or args is None:
        # Empty or invalid slash command
        err_msg = dbM.save_chat(game.id, "명령어를 잘못 입력했습니다. 다시 시도해주세요.", sort="error", user_id=user_id)
        await conM.broadcast_to_game(game.id, err_msg)
        return

    ctx = CommandContext(
        user_id=user_id,
        channel_id=game.id,
        raw=content,
        args=args,
        command=command,
        game=game,
        websocket=websocket,
        sender=sender,
    )

    try:
        result, err, action_data = await _router.dispatch(command, ctx)
    except ValueError as e:
        err = str(e) if str(e) else "알 수 없는 명령어입니다."
        result, action_data = None, None

    await _save_and_broadcast_message(game, result, err, sender, user_id)


def _save_regular_chat(game, content: str, sender: str, user_id: str, chat_type: str) -> dict:
    return dbM.save_chat(game.id, content, sender=sender, sort=chat_type, user_id=user_id)

## v dumb logic. I should fix this.
async def _save_and_broadcast_message(game, result: str | None, err: str | None, sender: str, user_id: str) -> None:
    secret_msg = None
    msg = None

    if result:
        secret_msg = dbM.save_chat(game.id, result, sender=sender, sort="secret", user_id=user_id)
    if err:
        msg = dbM.save_chat(game.id, err, sort="error", user_id=user_id)
    if not result and not err:
        err = "명령어를 잘못 입력했습니다. 다시 시도해주세요."
        msg = dbM.save_chat(game.id, err, sort="error", user_id=user_id)

    if secret_msg:
        await conM.broadcast_to_game(game.id, secret_msg)
    if msg:
        await conM.broadcast_to_game(game.id, msg)
