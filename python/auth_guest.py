"""
Authentication utility functions for guest session management
Uses client-provided guest_id (from localStorage) to assign persistent guest numbers
"""
from contextlib import nullcontext
from fastapi import WebSocket
from typing import Dict, Optional
from .util import conmanager

# Global mappings
_guest_id_to_number: Dict[str, int] = {}  # Maps client guest_id -> guest_number
_guest_counter = 0  # Counter for assigning new guest numbers


def get_or_assign_guest_number(guest_id: str) -> int:
    """
    Get existing guest number for a guest_id, or assign a new one if it doesn't exist.
    Prints the guest number to console.
    
    Args:
        guest_id: Unique ID provided by the client (from localStorage)
        
    Returns:
        The guest number assigned to this guest_id
    """
    global _guest_counter
    
    # Check if this guest_id already has a number
    if guest_id in _guest_id_to_number:
        guest_number = _guest_id_to_number[guest_id]
        print(f"Guest {guest_number} reconnected (guest_id: {guest_id})")
        return guest_number
    
    # Assign new guest number
    _guest_counter += 1
    guest_number = _guest_counter
    _guest_id_to_number[guest_id] = guest_number
    print(f"Guest {guest_number} connected (guest_id: {guest_id})")
    return guest_number


def get_guest_number(guest_id: str) -> Optional[int]:
    """
    Get the guest number for a given guest_id without assigning a new one.
    
    Args:
        guest_id: Unique ID provided by the client
        
    Returns:
        The guest number if exists, None otherwise
    """
    return _guest_id_to_number.get(guest_id)


def remove_guest(guest_id: str) -> None:
    """
    Remove a guest assignment when they disconnect.
    Prints the guest number to console.
    
    Note: This removes the mapping, so if they reconnect, they'll get a new number.
    If you want to keep the mapping (so they keep the same number on reconnect),
    you can skip calling this function.
    
    Args:
        guest_id: Unique ID provided by the client
    """
    guest_number = _guest_id_to_number.pop(guest_id, None)
    if guest_number:
        print(f"Guest {guest_number} disconnected (guest_id: {guest_id})")

async def handle_guest_auth(websocket: WebSocket, auth_message: dict):
    guest_id = auth_message.get('guest_id')

    if not guest_id:
        # Handle error - no guest_id provided
        await websocket.close()
        print("Error: no guest_id provided")
        return
    
    # Get or assign guest number
    guest_number = get_or_assign_guest_number(guest_id)
    conmanager.set_guest_number(websocket, guest_number)
    
    # Send guest_number back to client (optional, for display)
    await websocket.send_json({
        'type': 'auth_success',
        'user_info': {
            'id': guest_id,
            'name': 'Guest' + str(guest_number),
            'guest_number': guest_number,
            'isGuest': True
        }
    })