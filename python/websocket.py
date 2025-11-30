"""
FastAPI server with WebSocket support for game initialization
"""
from re import A
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .game import Game
import json
import uuid

app = FastAPI()

# Store active game sessions
game_sessions = {}

@app.get("/")
async def read_root():
    return FileResponse("index.html")

# Serve static files
app.mount("/style", StaticFiles(directory="style"), name="style")
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/javaScript", StaticFiles(directory="javaScript"), name="javaScript")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = None
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data) 
            
            if message.get("action") == "start_game":
                session_id = uuid.uuid4().hex[:10].upper() # generate a random session id
                game_sessions[session_id] = Game(session_id) # create a new game session
                vomit_data = game_sessions[session_id].vomit()
                await websocket.send_json(vomit_data)
                await websocket.send_json({
                        "type": "system_message",
                        "content": f"Game session {session_id} started."
                    })

            elif message.get("action") == "load_game":
                # Since there's only one session at a time, check if any session exists
                print("Checking session:", game_sessions)
                if game_sessions:
                    # Get the first (and only) session
                    session_id, game = next(iter(game_sessions.items()))
                    vomit_data = game.vomit()
                    # session_id is already in vomit_data from Game.vomit()
                    await websocket.send_json(vomit_data)
                else:
                    await websocket.send_json({
                        "type": "no_session"
                    })
            elif message.get("action") == "end_game":
                session_id = message.get("session_id")
                if session_id and session_id in game_sessions:
                    del game_sessions[session_id]
                    await websocket.send_json({
                        "type": "system_message",
                        "content": f"Game session {session_id} ended"
                    })


            elif message.get("type") == "user_chat":
                content = message.get("content", "")
                sender = message.get("sender")
                if content and content[0] == "/":
                    command = content[1:]
                    if "이동" in command:
                        system_message = game_sessions[session_id].move_player(sender, command)
                        await websocket.send_json(system_message)
                else:
                    await websocket.send_json(message)


    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        pass

