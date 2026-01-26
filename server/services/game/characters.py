"""
Character data constants
In the final project, character data has to be pulled from a database.
For now, hard-coded global variables for each character.
"""

default_character = {
    "name": "Pikita",
    "profile_image": "/images/pikita_profile.png",
    "token_image": "/images/pikita_token.png",
    "stats": {
        "vtl":4,
        "sen":1,
        "per":1,
        "tal":2,
        "mst":2
    },
    "class": "physical",
    "type": "none",
    "skills": ["Medikit","Acceleration","Contortion"],
    "current_hp": 100,
    "pos": "A1"
}

bots = [
    {
    "name": "Bot_A",
    "profile_image": "/images/bettel_profile.png",
    "token_image": "/images/bot_white_token.png",
    "stats": {
        "vtl":3,
        "sen":2,
        "per":1,
        "tal":1,
        "mst":3
    },
    "class": "psychic",
    "type": "none",
    "skills": ["Telekinesis","Will-o-Wisp","Inference"],
    "current_hp": 100,
    "pos": "B2"
}
]
