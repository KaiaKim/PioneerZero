"""
Join/player management functions
Player slot management operations
"""
import time
from ...util.models import PlayerSlot, UserInfo
from .characters import default_character, bots


def add_player(game, slot_idx: int, user_info: UserInfo):
    """Add a player to a specific slot"""
    existing_player_info = game.players[slot_idx].info
    occupy = game.players[slot_idx].occupy
    num = slot_idx + 1

    is_same_user = existing_player_info and existing_player_info.id == user_info.id

    if occupy == 1:
        if is_same_user:
            return {"success": True, "message": f"Player already in slot {num}."}
        return {"success": False, "message": f"Slot {num} is already occupied."}

    if occupy == 2:
        if is_same_user:
            game.players[slot_idx].occupy = 1
            game.connection_lost_timers.pop(slot_idx, None)
            return {"success": True, "message": f"Player rejoined slot {num}."}
        return {"success": False, "message": f"Slot {num} is connection-lost. Please wait."}

    team = 1 if slot_idx < (game.player_num / 2) else 0
    game.players[slot_idx] = PlayerSlot(
        index=slot_idx,
        info=user_info,
        character=default_character,
        ready=False,
        team=team,
        occupy=1,
        current_hp=default_character.initial_hp,
        pos=default_character.initial_pos,
    )
    game.connection_lost_timers.pop(slot_idx, None)
    return {"success": True, "message": f"Player added to slot {num}."}


def add_bot(game, slot_idx: int):
    """Add a bot to a specific slot (0-based index)"""
    num = slot_idx + 1
    if game.players[slot_idx].occupy != 0:
        return {"success": False, "message": f"Slot {num} is not empty."}

    bot_index = slot_idx % len(bots) if bots else 0
    bot_character = bots[bot_index] if bots else default_character
    bot_info = UserInfo(
        id=f'bot_{slot_idx}',
        name=bot_character.name or f'Bot_{num}',
        is_bot=True,
    )
    team = 1 if slot_idx < (game.player_num / 2) else 0
    game.players[slot_idx] = PlayerSlot(
        index=slot_idx,
        info=bot_info,
        character=bot_character,
        ready=True,
        team=team,
        occupy=1,
        current_hp=bot_character.initial_hp,
        pos=bot_character.initial_pos,
    )
    game.connection_lost_timers.pop(slot_idx, None)
    return {"success": True, "message": f"Bot added to slot {num}."}


def remove_player(game, slot_idx: int):
    """Remove a player from a specific slot - sets status to empty"""
    num = slot_idx + 1
    if game.players[slot_idx].occupy == 0:
        return {"success": False, "message": f"Slot {num} is already empty."}
    game.players[slot_idx] = PlayerSlot(index=slot_idx)
    game.connection_lost_timers.pop(slot_idx, None)
    return {"success": True, "message": f"Player removed from slot {num}."}


def set_player_connection_lost(game, slot_idx: int):
    """Set a player slot to connection-lost status (2) and set ready to False"""
    num = slot_idx + 1
    if game.players[slot_idx].occupy == 0:
        return {"success": False, "message": f"Slot {num} is already empty."}
    game.players[slot_idx].occupy = 2
    game.players[slot_idx].ready = False
    game.connection_lost_timers[slot_idx] = time.time()
    return {"success": True, "message": f"Player slot {num} set to connection-lost."}


def clear_expired_connection_lost_slots(game, duration: float = 5.0):
    """Clear expired connection-lost slots after timeout"""
    current_time = time.time()
    indices_to_clear = []
    for slot_idx, timestamp in game.connection_lost_timers.items():
        if current_time - timestamp >= duration:
            if game.players[slot_idx].occupy == 2:
                game.players[slot_idx] = PlayerSlot(index=slot_idx)
                indices_to_clear.append(slot_idx)
    for slot_idx in indices_to_clear:
        game.connection_lost_timers.pop(slot_idx, None)
    return len(indices_to_clear) > 0


def set_player_ready(game, slot_idx: int, user_info: UserInfo, ready: bool):
    """Set ready state for a player. Only the player themselves can toggle their ready state."""
    num = slot_idx + 1
    player = game.players[slot_idx]
    if not player.info or player.info.id != user_info.id:
        return {"success": False, "message": f"You don't own slot {num}."}
    if player.occupy not in [1, 2]:
        return {"success": False, "message": f"Slot {num} is not occupied."}
    if player.info.is_bot or str(player.info.id).startswith('bot_'):
        return {"success": False, "message": "Bots are always ready."}
    game.players[slot_idx].ready = ready
    return {"success": True, "message": f"Ready state set to {ready} for slot {num}."}


def are_all_players_ready(game):
    """Check if all slots are filled AND all players are ready."""
    for player in game.players:
        if player.occupy != 1 or player.character is None:
            return False
        is_bot = player.info and (player.info.is_bot or str(player.info.id).startswith('bot_'))
        if not is_bot and not player.ready:
            return False
    return True
