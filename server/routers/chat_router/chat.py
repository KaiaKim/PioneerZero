"""
Chat and slash-command entry point.
Parse → route → handler; normal chat and commands are split at input.
"""
from fastapi import WebSocket

from ...util import conM, dbM
from ...util.models import CommandContext
from .input import parse_input
from .command import cmdM
from . import commands

# --- Router setup: one handler per command name ---
for _name in commands.position.POSITION_COMMANDS:
    cmdM.register(_name, commands.position.PositionCommand)
'''
for _name in commands.attack.ATTACK_COMMANDS:
    cmdM.register(_name, commands.attack.AttackCommand)
for _name in commands.skill.SKILL_COMMANDS:
    cmdM.register(_name, commands.skill.SkillCommand)

for _name in commands.preparation.PREPARATION_COMMANDS:
    cmdM.register(_name, commands.preparation.PreparationCommand)
'''

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
        msg = dbM.save_chat(game.id, content, sender=sender, sort=chat_type, user_id=user_id)
        await conM.broadcast_to_game(game.id, msg)
        return

    if command == "" or args is None:
        # Empty or invalid slash command
        msg = dbM.save_chat(game.id, "올바른 명령어 양식이 아닙니다.", sort="error", user_id=user_id)
        await conM.broadcast_to_game(game.id, msg)
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

    cmd = cmdM.get_handler(command)
    if cmd is None:
        msg = dbM.save_chat(game.id, f"등록되지 않은 명령어입니다.: {command}", sort="error", user_id=user_id)
        await conM.broadcast_to_game(game.id, msg)
        return

    error = await cmd.validate(ctx)
    if error:
        msg = dbM.save_chat(game.id, error, sort="error", user_id=user_id)
        await conM.broadcast_to_game(game.id, msg)
        return
    
    result = await cmd.run(ctx)
    msg = dbM.save_chat(game.id, result, sender=sender, sort="secret", user_id=user_id)
    await conM.broadcast_to_game(game.id, msg)

