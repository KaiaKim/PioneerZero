"""
Join/player management functions
Player slot management operations
"""
import time
from ...util.context import Player
from .characters import default_character, bots


def player_factory(slot: int = 0) -> Player:
    """Create a new empty player slot."""
    return Player(slot=slot)


def add_player(game, slot: int, slot_idx: int, user_info: dict):
    """Add a player to a specific slot"""
    existing_player_info = game.players[slot_idx].info
    occupy = game.players[slot_idx].occupy

    is_same_user = existing_player_info and existing_player_info.get('id') == user_info.get('id')

    if occupy == 1:
        if is_same_user:
            return {"success": True, "message": f"Player already in slot {slot}."}
        return {"success": False, "message": f"Slot {slot} is already occupied."}

    if occupy == 2:
        if is_same_user:
            game.players[slot_idx].occupy = 1
            game.connection_lost_timers.pop(slot, None)
            return {"success": True, "message": f"Player rejoined slot {slot}."}
        return {"success": False, "message": f"Slot {slot} is connection-lost. Please wait."}

    team = 1 if slot_idx < (game.player_num / 2) else 0
    game.players[slot_idx] = Player(
        info=user_info,
        character=default_character,
        slot=slot,
        ready=False,
        team=team,
        occupy=1,
    )
    game.connection_lost_timers.pop(slot, None)
    return {"success": True, "message": f"Player added to slot {slot}."}


def add_bot(game, slot: int, slot_idx: int):
    """Add a bot to a specific slot"""
    if game.players[slot_idx].occupy != 0:
        return {"success": False, "message": f"Slot {slot} is not empty."}

    bot_index = slot_idx % len(bots) if bots else 0
    bot_character = bots[bot_index] if bots else default_character
    bot_info = {
        'id': f'bot_{slot}',
        'name': bot_character.name or f'Bot_{slot}',
        'is_bot': True
    }
    team = 1 if slot_idx < (game.player_num / 2) else 0
    game.players[slot_idx] = Player(
        info=bot_info,
        character=bot_character,
        slot=slot,
        ready=True,
        team=team,
        occupy=1,
    )
    game.connection_lost_timers.pop(slot, None)
    return {"success": True, "message": f"Bot added to slot {slot}."}


def remove_player(game, slot: int, slot_idx: int):
    """Remove a player from a specific slot - sets status to empty"""
    if game.players[slot_idx].occupy == 0:
        return {"success": False, "message": f"Slot {slot} is already empty."}
    game.players[slot_idx] = player_factory(slot)
    game.connection_lost_timers.pop(slot, None)
    return {"success": True, "message": f"Player removed from slot {slot}."}


def set_player_connection_lost(game, slot: int):
    """Set a player slot to connection-lost status (2) and set ready to False"""
    slot_idx = slot - 1
    if game.players[slot_idx].occupy == 0:
        return {"success": False, "message": f"Slot {slot} is already empty."}
    game.players[slot_idx].occupy = 2
    game.players[slot_idx].ready = False
    game.connection_lost_timers[slot] = time.time()
    return {"success": True, "message": f"Player slot {slot} set to connection-lost."}


def clear_expired_connection_lost_slots(game, duration: float = 5.0):
    """Clear expired connection-lost slots after timeout"""
    current_time = time.time()
    slots_to_clear = []
    for slot, timestamp in game.connection_lost_timers.items():
        if current_time - timestamp >= duration:
            slot_idx = slot - 1
            if game.players[slot_idx].occupy == 2:
                game.players[slot_idx] = player_factory(slot)
                slots_to_clear.append(slot)
    for slot in slots_to_clear:
        game.connection_lost_timers.pop(slot, None)
    return len(slots_to_clear) > 0


def get_player_by_user_id(game, user_id: str):
    """Get the slot number for a user_id, or None if not found"""
    for i, player in enumerate(game.players):
        if player.info and player.info.get('id') == user_id:
            return i + 1
    return None


def set_player_ready(game, slot: int, slot_idx: int, user_info: dict, ready: bool):
    """Set ready state for a player. Only the player themselves can toggle their ready state."""
    player = game.players[slot_idx]
    if not player.info or player.info.get('id') != user_info.get('id'):
        return {"success": False, "message": "You don't own this slot."}
    if player.occupy not in [1, 2]:
        return {"success": False, "message": f"Slot {slot} is not occupied."}
    if player.info.get('is_bot') is True or (player.info.get('id') and str(player.info.get('id')).startswith('bot_')):
        return {"success": False, "message": "Bots are always ready."}
    game.players[slot_idx].ready = ready
    return {"success": True, "message": f"Ready state set to {ready}."}


def are_all_players_ready(game):
    """Check if all slots are filled AND all players are ready."""
    for player in game.players:
        if player.occupy != 1 or player.character is None:
            return False
        is_bot = player.info and (
            player.info.get('is_bot') is True or
            (player.info.get('id') and str(player.info.get('id')).startswith('bot_'))
        )
        if not is_bot and not player.ready:
            return False
    return True
