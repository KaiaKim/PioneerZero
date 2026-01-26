from fastapi import WebSocket
from ...util import conM, dbM

attack_list = ["근거리공격", "원거리공격", "대기"]
skill_list = ["스킬1", "스킬2", "스킬3", "스킬4"]


async def handle_chat(websocket: WebSocket, message: dict, game):
    """Handle chat messages and commands"""
    content = message.get("content", "")
    sender = message.get("sender")
    user_info = conM.get_user_info(websocket)
    user_id = user_info.get('id')
    msg = None
    secret_msg = None

    if content[0] == "/": #we've already checked if content is not empty
        # Handle commands
        command = content[1:].split()
        result = None
        err = None
        if game.in_combat == False:
            if command[0] == "참여" or command[0] == "join":
                pass
            elif command[0] == "관전" or command[0] == "leave":
                pass
            else:
                err = "사용 가능한 준비 명령어: 참여, 관전."

        elif game.in_combat == True:
            player_ids = [player['info']['id'] for player in game.players]
            if user_id in player_ids:
                if game.phase == "position_declaration":
                    if command[0] == "위치" or command[0] == "pos":
                        result, err = game.Pos.declare_position(user_id, command)
                elif game.phase == "action_declaration":
                    if command[0] in attack_list:
                        result, action_data, err = game.declare_attack(user_id, command)
                        if result and not err:
                            await websocket.send_json({
                                "type": "declared_attack",
                                "attack_info": action_data
                            })
                            await conM.broadcast_to_game(game.id, {
                                "type": "action_submission_update",
                                "submitted": game.get_action_submission_status()
                            })
                    elif command[0] in skill_list:
                        result, err = game.declare_skill(user_id, command)
                        if result and not err:
                            await conM.broadcast_to_game(game.id, {
                                "type": "action_submission_update",
                                "submitted": game.get_action_submission_status()
                            })

                    else:
                        err = "사용 가능한 전투 명령어가 아닙니다."
            else:
                err = "전투 명령어는 전투 참여자만 사용할 수 있습니다."
        
        # Save and broadcast the result as system message (visible to all)
        if result:
            secret_msg = dbM.save_chat(game.id, result, sender=sender, sort="secret", user_id=user_id)
            # Save the user's command as secret (only visible to the user)
        if err:
            msg = dbM.save_chat(game.id, err, sort="error", user_id=user_id)
        if not result and not err:
            err = "명령어를 잘못 입력했습니다. 다시 시도해주세요."
            msg = dbM.save_chat(game.id, err, sort="error", user_id=user_id)
    else:
        # Regular chat message
        msg = dbM.save_chat(game.id, content, sender=sender, sort="user", user_id=user_id)
    
    if secret_msg:
        await conM.broadcast_to_game(game.id, secret_msg)

    await conM.broadcast_to_game(game.id, msg)
