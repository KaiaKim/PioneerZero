"""
Join/player management functions
Player slot management operations
"""
import time
from .characters import default_character, bots


def player_factory(slot: int = 0):
    """Factory function to create a new player slot dict. Each call returns a fresh dict."""
    return {
        'info': None,
        'character': None,
        'slot': slot,
        'ready': False,
        'team': 0,  # 0=white, 1=blue
        'occupy': 0,  # 0=empty, 1=occupied, 2=connection-lost
        'pos': None  # position on the game board
    }


def add_player(game, slot: int, slot_idx: int, user_info: dict):
    """Add a player to a specific slot"""
    existing_player_info = game.players[slot_idx]['info']
    occupy = game.players[slot_idx]['occupy']
    
    # Check if it's the same user trying to rejoin
    is_same_user = existing_player_info and existing_player_info.get('id') == user_info.get('id')
    
    # Check if slot is occupied (status 1)
    if occupy == 1:
        if is_same_user:
            # Same user rejoining - already occupied by them, no change needed
            return {"success": True, "message": f"Player already in slot {slot}."}
        return {"success": False, "message": f"Slot {slot} is already occupied."}
    
    # Check if slot is connection-lost (status 2)
    if occupy == 2:
        if is_same_user:
            # Same user rejoining - update status to occupied
            game.players[slot_idx]['occupy'] = 1
            game.connection_lost_timers.pop(slot, None)
            return {"success": True, "message": f"Player rejoined slot {slot}."}
        return {"success": False, "message": f"Slot {slot} is connection-lost. Please wait."}
    
    # Slot is empty (status 0) - add player
    # Create player object with user_info and slot number
    # Team logic: first half = blue (1), second half = white (0)
    team = 1 if slot_idx < (game.player_num / 2) else 0  # 0=white, 1=blue
    player_obj = {
        'info': user_info,
        'character': default_character,
        "slot": slot,
        'ready': False,  # Players must check ready checkbox
        'team': team,
        'occupy': 1  # 0=empty, 1=occupied, 2=connection-lost
    }
    game.players[slot_idx] = player_obj
    game.connection_lost_timers.pop(slot, None)  # Clear any connection-lost timer
    return {"success": True, "message": f"Player added to slot {slot}."}


def add_bot(game, slot: int, slot_idx: int):
    """Add a bot to a specific slot"""
    occupy = game.players[slot_idx]['occupy']
    
    # Check if slot is occupied (status 1) or connection-lost (status 2)
    if occupy != 0:
        return {"success": False, "message": f"Slot {slot} is not empty."}
    
    # Slot is empty (status 0) - add bot
    # Get a bot from the bots array (use first available bot, or cycle as needed)
    bot_index = slot_idx % len(bots) if bots else 0
    bot_character = bots[bot_index] if bots else default_character
    
    # Create bot info similar to user_info structure
    bot_info = {
        'id': f'bot_{slot}',  # Unique bot ID based on slot
        'name': bot_character.get('name', f'Bot_{slot}'),
        'is_bot': True
    }
    
    # Create player object with bot info and bot character
    # Team logic: first half = blue (1), second half = white (0)
    team = 1 if slot_idx < (game.player_num / 2) else 0  # 0=white, 1=blue
    player_obj = {
        'info': bot_info,
        'character': bot_character,
        'slot': slot,
        'ready': True, #bots are always ready
        'team': team,
        'occupy': 1  # 0=empty, 1=occupied, 2=connection-lost
    }
    game.players[slot_idx] = player_obj
    game.connection_lost_timers.pop(slot, None)  # Clear any connection-lost timer
    return {"success": True, "message": f"Bot added to slot {slot}."}


def remove_player(game, slot: int, slot_idx: int):
    """Remove a player from a specific slot - sets status to empty"""
    if game.players[slot_idx]['occupy'] == 0:
        return {"success": False, "message": f"Slot {slot} is already empty."}
    
    game.players[slot_idx] = player_factory(slot)
    game.connection_lost_timers.pop(slot, None)  # Clear any connection-lost timer
    return {"success": True, "message": f"Player removed from slot {slot}."}


def set_player_connection_lost(game, slot: int):
    """Set a player slot to connection-lost status (2) and set ready to False"""
    slot_idx = slot - 1
    if game.players[slot_idx]['occupy'] == 0:
        return {"success": False, "message": f"Slot {slot} is already empty."}
    
    game.players[slot_idx]['occupy'] = 2  # Set status to connection-lost
    game.players[slot_idx]['ready'] = False  # Set ready to False when connection is lost
    game.connection_lost_timers[slot] = time.time()  # Record timestamp
    return {"success": True, "message": f"Player slot {slot} set to connection-lost."}


def clear_expired_connection_lost_slots(game, duration: float = 5.0):
    """Clear expired connection-lost slots after timeout"""
    current_time = time.time()
    slots_to_clear = []
    
    for slot, timestamp in game.connection_lost_timers.items():
        if current_time - timestamp >= duration:  # default 5 seconds timeout
            slot_idx = slot - 1
            if game.players[slot_idx]['occupy'] == 2:  # Still connection-lost
                game.players[slot_idx] = player_factory(slot)
                slots_to_clear.append(slot)
    
    # Remove cleared slots from timers
    for slot in slots_to_clear:
        game.connection_lost_timers.pop(slot, None)
    
    return len(slots_to_clear) > 0  # Return True if any slots were cleared


def get_player_by_user_id(game, user_id: str):
    """Get the slot number for a user_id, or None if not found"""
    for i, player in enumerate(game.players):
        if player.get('info') and player['info'].get('id') == user_id:
            return i + 1  # Return slot number (1-based)
    return None


def set_player_ready(game, slot: int, slot_idx: int, user_info: dict, ready: bool):
    """Set ready state for a player. Only the player themselves can toggle their ready state."""
    # Verify the slot belongs to the user
    player = game.players[slot_idx]
    if not player.get('info') or player['info'].get('id') != user_info.get('id'):
        return {"success": False, "message": "You don't own this slot."}
    
    # Check if slot is occupied or connection-lost (can set ready in both states)
    if player['occupy'] not in [1, 2]:
        return {"success": False, "message": f"Slot {slot} is not occupied."}
    
    # Check if it's a bot (bots are always ready, can't be changed)
    if player['info'].get('is_bot') == True or (player['info'].get('id') and player['info'].get('id').startswith('bot_')):
        return {"success": False, "message": "Bots are always ready."}
    
    # Set ready state
    game.players[slot_idx]['ready'] = ready
    return {"success": True, "message": f"Ready state set to {ready}."}


def are_all_players_ready(game):
    """
    Check if all slots are filled AND all players are ready.
    - All slots must have characters (occupy == 1 and character is not None)
    - All players must be ready (ready == True)
    - Bots are always considered ready
    """
    for player in game.players:
        # Check if slot is filled with a character
        if player['occupy'] != 1 or player['character'] is None:
            return False
        
        # Check if player is ready (bots are always ready by design, so we only check non-bots)
        is_bot = player.get('info') and (player['info'].get('is_bot') == True or 
                                        (player['info'].get('id') and player['info'].get('id').startswith('bot_')))
        
        if not is_bot and not player.get('ready', False):
            return False
    
    return True
