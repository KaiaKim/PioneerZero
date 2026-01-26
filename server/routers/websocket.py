"""
WebSocket endpoint routing and message handling
"""
from fastapi import WebSocket
import uuid
import traceback
from ..util import conM, dbM
from ..services.game.core import Game
from . import auth, lobby
from .game import chat, flow, slot

# Global game sessions dictionary: {game_id: Game object}
# Games are loaded lazily from the database when accessed
rooms = {}


async def websocket_endpoint(websocket: WebSocket):
    await conM.connect(websocket)

    try:
        # Wait for authentication message first
        auth_message = await websocket.receive_json()
        auth_action = auth_message.get('action')

        # Handle Google OAuth authentication
        if auth_action == 'google_login':
            await auth.handle_google_login(websocket, auth_message)
        # Handle guest authentication (existing flow)
        elif auth_action == 'authenticate_user':
            await auth.handle_user_auth(websocket, auth_message)
        else:
            await websocket.close()
            print("Error: invalid authentication action")
            return


        # Now continue with normal message loop
        while True:
            message = await websocket.receive_json()
            action = message.get("action")

            if action == "kill_db":
                #Clean up chat tables for prototype purpose only. Do not use in production.
                dbM.kill_all_chat_tables()
                rooms.clear()
                continue

            # Route lobby actions
            if action == "list_rooms":
                chat_tables = dbM.get_chat_tables()
                await lobby.handle_list_rooms(websocket, chat_tables)
                continue

            if action == "create_room":
                game_id = uuid.uuid4().hex[:10].upper()  # generate a random session id
                player_num = message.get("player_num", 4)  # Get player_num from message, default to 4
                rooms[game_id] = await lobby.handle_create_room(websocket, game_id, player_num)  # create a new game session
                continue

            # Get the game_id from message only (required for all game actions)
            game_id = message.get("game_id")
            if not game_id:
                print(f"No game_id")
                #await websocket.send_json({"type": "no_game_id"})
                continue
            
            try:
                game = rooms[game_id]
            except KeyError:
                print(f"Game {game_id} not found")
                rooms[game_id] = Game(game_id)
                game = rooms[game_id]

            # Route game actions
            if action == "join_room":
                print(f"Joining room {game_id}")
                await lobby.handle_join_room(websocket, game_id, game)
            elif action == "load_room":
                print(f"Loading room {game_id}")
                await lobby.handle_load_room(websocket, game)
            elif action == "chat":
                await chat.handle_chat(websocket, message, game)
            elif action == "join_player_slot":
                await slot.handle_join_player_slot(websocket, message, game)
            elif action == "add_bot_to_slot":
                await slot.handle_add_bot_to_slot(websocket, message, game)
                await flow.handle_phase(game)
            elif action == "leave_player_slot":
                await slot.handle_leave_player_slot(websocket, message, game)
            elif action == "set_ready":
                await slot.handle_set_ready(websocket, message, game)
                await flow.handle_phase(game)
            
            vomit_data = game.vomit()
            await websocket.send_json(vomit_data)
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()
    finally:
        # Remove user from game users list and set player slot to connection-lost before disconnecting
        game_id, user_info = await conM.leave_game(websocket)
        if game_id and user_info and game_id in rooms:
            game = rooms[game_id]
            # Remove user from game users list
            game.users = [u for u in game.users if u.get('id') != user_info.get('id')]
            # Set player slot to connection-lost instead of removing
            user_slot = game.Slot.get_player_by_user_id(user_info.get('id'))
            if user_slot:
                game.Slot.set_player_connection_lost(user_slot)
            # Broadcast updated users list and players list to remaining clients
            await conM.broadcast_to_game(game_id, {
                'type': 'users_list',
                'users': game.users
            })
            await conM.broadcast_to_game(game_id, {
                'type': 'players_list',
                'players': game.players
            })
        # Always disconnect when WebSocket closes
        await conM.disconnect(websocket)
