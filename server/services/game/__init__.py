"""
Game service modules
"""
from .core import Game
from . import slot, position
from .characters import default_character, bots

__all__ = ['Game', 'slot', 'position', 'default_character', 'bots']
