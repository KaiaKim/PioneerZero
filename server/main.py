"""
Global variables and core server setup for the FastAPI server
"""
from fastapi import FastAPI, WebSocket
import uuid
import traceback
import asyncio
from dotenv import load_dotenv
from . import lobby_ws, game_ws, google_login, auth_user, game_core
from .util import conmanager, dbmanager

# Load environment variables from .env file
load_dotenv()

# Global game sessions dictionary: {game_id: Game object}
# Games are loaded lazily from the database when accessed
rooms = {}

# FastAPI app instance
app = FastAPI()

# Include OAuth router
app.include_router(google_login.router)

# Background task to periodically check for connection-lost timeouts
async def run_connection_lost_timeout_checks():
    """Periodically runs connection-lost timeout checks for all games"""
    while True:
        try:
            for game_id, game in rooms.items():
                if game.clear_expired_connection_lost_slots():
                    # Broadcast updated players list if any slots were cleared
                    await conmanager.broadcast_to_game(game_id, {
                        'type': 'players_list',
                        'players': game.players
                    })
            await asyncio.sleep(1)  # Check every second
        except Exception as e:
            print(f"Error in connection-lost timeout check: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup"""
    asyncio.create_task(run_connection_lost_timeout_checks())


# Main WebSocket endpoint - routes messages to appropriate handlers
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await conmanager.connect(websocket)

    try:
        # Wait for authentication message first
        auth_message = await websocket.receive_json()
        auth_action = auth_message.get('action')

        # Handle Google OAuth authentication
        if auth_action == 'google_login':
            await google_login.handle_google_login(websocket, auth_message)
        # Handle guest authentication (existing flow)
        elif auth_action == 'authenticate_user':
            await auth_user.handle_user_auth(websocket, auth_message)
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
                dbmanager.kill_all_chat_tables()
                rooms.clear()
                continue

            # Route lobby actions
            if action == "list_rooms":
                chat_tables = dbmanager.get_chat_tables()
                await lobby_ws.handle_list_rooms(websocket, chat_tables)
                continue

            if action == "create_room":
                game_id = uuid.uuid4().hex[:10].upper()  # generate a random session id
                player_num = message.get("player_num", 4)  # Get player_num from message, default to 4
                rooms[game_id] = await lobby_ws.handle_create_room(websocket, game_id, player_num)  # create a new game session
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
                rooms[game_id] = game_core.Game(game_id)
                game = rooms[game_id]

            # Route game actions
            if action == "join_room":
                print(f"Joining room {game_id}")
                await lobby_ws.handle_join_room(websocket, game_id, game)
                print("conmanager.game_connections:", conmanager.game_connections)
                continue

            if action == "load_room":
                print(f"Loading room {game_id}")
                await game_ws.handle_load_room(websocket, game)
                continue
            
            if action == "start_combat":
                print(f"Starting combat {game_id}")
                await game_ws.handle_start_combat(game)
                continue

            if action == "end_combat":
                await game_ws.handle_end_combat(websocket, game)
                continue
            
            if action == "chat":
                await game_ws.handle_chat(websocket, message, game)
                continue
            
            if action == "join_player_slot":
                await game_ws.handle_join_player_slot(websocket, message, game)
                continue
            
            if action == "add_bot_to_slot":
                await game_ws.handle_add_bot_to_slot(websocket, message, game)
                # Check if all players are ready and start combat if so
                if game.are_all_players_ready() and not game.combat_state['in_combat']:
                    await game_ws.handle_start_combat(game)
                continue
            
            if action == "leave_player_slot":
                await game_ws.handle_leave_player_slot(websocket, message, game)
                continue
            
            if action == "set_ready":
                await game_ws.handle_set_ready(websocket, message, game)
                # Check if all players are ready and start combat if so
                if game.are_all_players_ready() and not game.combat_state['in_combat']:
                    await game_ws.handle_start_combat(game)
                continue
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()
    finally:
        # Remove user from game users list and set player slot to connection-lost before disconnecting
        game_id, user_info = await conmanager.leave_game(websocket)
        if game_id and user_info and game_id in rooms:
            game = rooms[game_id]
            # Remove user from game users list
            game.users = [u for u in game.users if u.get('id') != user_info.get('id')]
            # Set player slot to connection-lost instead of removing
            user_slot = game.get_player_by_user_id(user_info.get('id'))
            if user_slot:
                game.set_player_connection_lost(user_slot)
            # Broadcast updated users list and players list to remaining clients
            await conmanager.broadcast_to_game(game_id, {
                'type': 'users_list',
                'users': game.users
            })
            await conmanager.broadcast_to_game(game_id, {
                'type': 'players_list',
                'players': game.players
            })
        # Always disconnect when WebSocket closes
        await conmanager.disconnect(websocket)

