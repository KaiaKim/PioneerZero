from fastapi import WebSocket
from ...util import conM, dbM
from ...services.game import position

attack_list = ["근거리공격", "원거리공격", "대기"]
skill_list = ["스킬1", "스킬2", "스킬3", "스킬4"]


# Main Entry Point
async def handle_chat(websocket: WebSocket, message: dict, game):
    """Handle chat messages and commands."""
    content = message.get("content", "")
    sender = message.get("sender")
    user_info = conM.get_user_info(websocket)
    user_id = user_info.get('id')
    
    # Check if message is a command
    if content and content[0] == "/":
        command, args = _parse_command(content)
        if command:
            result, err, action_data = await _route_command(command, args, websocket, game, user_id)
            await _save_and_broadcast_message(game, result, err, sender, user_id)
        else:
            # Empty command
            err = "명령어를 잘못 입력했습니다. 다시 시도해주세요."
            msg = dbM.save_chat(game.id, err, sort="error", user_id=user_id)
            await conM.broadcast_to_game(game.id, msg)
    else:
        # Regular chat message
        msg = _save_regular_chat(game, content, sender, user_id)
        await conM.broadcast_to_game(game.id, msg)


# Helper Functions
def _parse_command(content: str) -> tuple[str, list[str]]:
    """Extract command name and arguments from content string."""
    if not content or content[0] != "/":
        return "", []
    command_parts = content[1:].split()
    if not command_parts:
        return "", []
    return command_parts[0], command_parts[1:]


def _is_valid_combat_participant(game, user_id: str) -> bool:
    """Check if user is a combat participant."""
    player_ids = [player['info']['id'] for player in game.players]
    return user_id in player_ids


# Message Management Functions
def _save_regular_chat(game, content: str, sender: str, user_id: str) -> dict:
    """Save regular chat messages."""
    return dbM.save_chat(game.id, content, sender=sender, sort="user", user_id=user_id)


async def _save_and_broadcast_message(game, result: str, err: str, sender: str, user_id: str):
    """Handle message persistence and broadcasting."""
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


# Phase-Specific Command Handlers
def _handle_position_declaration(command: str, args: list[str], game, user_id: str) -> tuple[str, str]:
    """Handle position declaration commands."""
    if command == "위치" or command == "pos":
        return position.declare_position(game, user_id, [command] + args)
    return None, "사용 가능한 전투 명령어가 아닙니다."


async def _handle_action_declaration(command: str, args: list[str], websocket: WebSocket, game, user_id: str) -> tuple[str, str, dict]:
    """Handle action declaration commands (attack and skill)."""
    action_data = None
    result = None
    err = None
    
    if command in attack_list:
        # Extract target from args, default to "자신"
        target = args[0].strip() if args else "자신"
        
        # Declare attack with clean parameters
        action_data, err = game.declare_attack(user_id, command, target)
        
        if action_data and not err:
            # Format success message
            command_str = command
            if args:
                command_str = f"{command} {target}"
            result = f'행동 선언 완료: {command_str}'
            
            # Send WebSocket response
            await websocket.send_json({
                "type": "declared_attack",
                "attack_info": action_data
            })
            await conM.broadcast_to_game(game.id, {
                "type": "action_submission_update",
                "submitted": game.get_action_submission_status()
            })
        
        return result, err, action_data
    
    elif command in skill_list:
        result, err = game.declare_skill(user_id, [command] + args)
        if result and not err:
            await conM.broadcast_to_game(game.id, {
                "type": "action_submission_update",
                "submitted": game.get_action_submission_status()
            })
        return result, err, None
    
    return None, "사용 가능한 전투 명령어가 아닙니다.", None


# Game State Handlers
def _handle_preparation_command(command: str, args: list[str], game, user_id: str) -> tuple[str, str]:
    """Handle commands during preparation phase."""
    if command == "참여" or command == "join":
        # TODO: Implement join logic
        pass
        return None, None
    elif command == "관전" or command == "leave":
        # TODO: Implement leave logic
        pass
        return None, None
    else:
        return None, "사용 가능한 준비 명령어: 참여, 관전."


async def _handle_combat_command(command: str, args: list[str], websocket: WebSocket, game, user_id: str) -> tuple[str, str, dict]:
    """Route combat commands to phase-specific handlers."""
    if not _is_valid_combat_participant(game, user_id):
        return None, "전투 명령어는 전투 참여자만 사용할 수 있습니다.", None
    
    if game.phase == "position_declaration":
        result, err = _handle_position_declaration(command, args, game, user_id)
        return result, err, None
    
    elif game.phase == "action_declaration":
        return await _handle_action_declaration(command, args, websocket, game, user_id)
    
    return None, "현재 단계에서 사용할 수 없는 명령어입니다.", None


# Command Router
async def _route_command(command: str, args: list[str], websocket: WebSocket, game, user_id: str) -> tuple[str, str, dict]:
    """Route command to appropriate handler based on game state."""
    if not game.in_combat:
        result, err = _handle_preparation_command(command, args, game, user_id)
        return result, err, None
    else:
        return await _handle_combat_command(command, args, websocket, game, user_id)

