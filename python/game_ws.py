"""
Game WebSocket handlers
"""
from fastapi import WebSocket
from datetime import datetime
from .util import conmanager, dbmanager


async def handle_load_game(websocket: WebSocket, game):
    """Handle load_game action - loads game state and chat history"""
    vomit_data = game.vomit()
    # Send to requesting client only
    await websocket.send_json(vomit_data)
    
    # Send users list to the requesting client
    await websocket.send_json({
        "type": "users_list",
        "users": game.users
    })
    
    # Load and send chat history to the requesting client
    chat_history_rows = dbmanager.get_chat_history(game.id)
    chat_messages = []
    for row in chat_history_rows:
        # row format: (id, sender, time, content, sort)
        chat_messages.append({
            "type": "chat",
            "sender": row[1],
            "time": row[2],
            "content": row[3],
            "sort": row[4]
        })
    
    # Send chat history only to the requesting client
    await websocket.send_json({
        "type": "chat_history",
        "messages": chat_messages
    })


async def handle_end_game(websocket: WebSocket, game_id: str):
    """Send end game message to all clients in the game. Do not delete data or remove connections."""
    now = datetime.now().isoformat()
    msg = dbmanager.save_chat(game_id, "System", now, f"Game {game_id} ended.", "system")
    await conmanager.broadcast_to_game(game_id, msg)


async def handle_chat(websocket: WebSocket, message: dict, game):
    """Handle chat messages and commands"""
    now = datetime.now().isoformat()
    content = message.get("content", "")
    sender = message.get("sender")
    
    if content and content[0] == "/":
        # Handle commands
        command = content[1:]
        result = "unknown command"
        if "이동" in command:
            result = game.move_player(sender, command)
        elif "스킬" in command:
            result = "스킬 사용함"
        elif "행동" in command:
            result = "행동함"
        msg = dbmanager.save_chat(game.id, "System", now, result, "system")
    else:
        # Regular chat message
        msg = dbmanager.save_chat(game.id, sender, now, content, "user")
    
    await conmanager.broadcast_to_game(game.id, msg)

