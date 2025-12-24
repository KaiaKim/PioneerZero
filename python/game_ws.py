"""
Game WebSocket handlers
"""
from fastapi import WebSocket
from datetime import datetime
from .util import manager
from .main import sessions
from .game_chat import save_chat, get_chat_history


async def handle_load_game(websocket: WebSocket, game_id: str, game):
    """Handle load_game action - loads game state and chat history"""
    vomit_data = game.vomit()
    # Send to requesting client only
    await websocket.send_json(vomit_data)
    
    # Load and send chat history to the requesting client
    chat_history_rows = get_chat_history(game_id)
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
    """Handle end_game action - ends a game session"""
    now = datetime.now().isoformat()
    msg = save_chat(game_id, "System", now, f"Game {game_id} ended.", "system")
    await manager.broadcast_to_game(game_id, msg)
    
    # Remove all connections from this game
    connections = manager.get_game_connections(game_id)
    for conn in connections:
        manager.connection_to_game.pop(conn, None)
    manager.game_connections.pop(game_id, None)
    del sessions[game_id]


async def handle_chat(websocket: WebSocket, message: dict, game_id: str):
    """Handle chat messages and commands"""
    now = datetime.now().isoformat()
    content = message.get("content", "")
    sender = message.get("sender")
    
    if content and content[0] == "/":
        # Handle commands
        command = content[1:]
        result = "unknown command"
        if "이동" in command:
            result = sessions[game_id].move_player(sender, command)
        elif "스킬" in command:
            result = "스킬 사용함"
        elif "행동" in command:
            result = "행동함"
        msg = save_chat(game_id, "System", now, result, "system")
    else:
        # Regular chat message
        msg = save_chat(game_id, sender, now, content, "user")
    
    await manager.broadcast_to_game(game_id, msg)
