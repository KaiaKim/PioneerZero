"""
Character data constants
In the final project, character data has to be pulled from a database.
For now, hard-coded global variables for each character.
"""
from ...util.models import Character

# stats order: vtl, sen, per, tal, mst
default_character = Character(
    name="Pikita",
    profile_image="/images/pikita_profile.png",
    token_image="/images/pikita_token.png",
    stats=[4, 1, 1, 2, 2],
    character_class="physical",
    type="none",
    skills=["Medikit", "Acceleration", "Contortion"],
    initial_hp=100,
    initial_pos="A1",
)

bots = [
    Character(
        name="Bot_A",
        profile_image="/images/bettel_profile.png",
        token_image="/images/bot_white_token.png",
        stats=[3, 2, 1, 1, 3],
        character_class="psychic",
        type="none",
        skills=["Telekinesis", "Will-o-Wisp", "Inference"],
        initial_hp=100,
        initial_pos="B2",
    )
]
