"""
Authentication utility functions for guest session management
"""
from fastapi import WebSocket
from .util import conM

async def handle_user_auth(websocket: WebSocket, auth_message: dict):
    """
    Handle guest authentication - accepts either guest_id or user_info.
    For guests without user_info, uses guest_id. For authenticated users, uses user_info.
    """
    user_info = auth_message.get('user_info')
    guest_id = auth_message.get('guest_id')
    
    # If user_info is provided (from quickAuth), use it directly
    if user_info:
        if isinstance(user_info, str):
            import json
            user_info = json.loads(user_info)
        
        print(f"User authenticated: {user_info.get('name') or user_info.get('email')} (id: {user_info.get('id')})")
        # Store user_info with the connection
        conM.set_user_info(websocket, user_info)
        await websocket.send_json({
            'type': 'auth_success',
            'user_info': user_info
        })
        return
    
    # Otherwise, use guest_id (fallback for guests)
    if not guest_id:
        await websocket.close()
        print("Error: no guest_id or user_info provided")
        return
    
    print(f"Guest connected (guest_id: {guest_id})")
    guest_user_info = {
        'id': guest_id,
        'name': 'Guest',
        'isGoogle': False,
        'isGuest': True
    }
    # Store user_info with the connection
    conM.set_user_info(websocket, guest_user_info)
    await websocket.send_json({
        'type': 'auth_success',
        'guest_id': guest_id,
        'user_info': guest_user_info
    })