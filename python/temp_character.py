# In the final project, character data has to be pulled from a database. 
# For now, I will create a hard-coded global variable for each character.

player = {
    "name": "Pikita",
    "profile_image": "images/pikita_profile.png",
    "token_image": "images/pikita_token.png",
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

ally_A = {
    "name": "Bettel",
    "profile_image": "images/bettel_profile.png",
    "token_image": "images/bettel_token.png",
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

enemy_A = {
    "name": "Jade",
    "profile_image": "images/jade_profile.png",
    "token_image": "images/jade_token.png",
    "stats": {
        "vtl":1,
        "sen":1,
        "per":3,
        "tal":4,
        "mst":1
    },
    "class": "terraformer",
    "type": "none",
    "skills": ["Levitation","Misty Veil","Healing Wave"],
    "current_hp": 100,
    "pos": "X3"
}

enemy_B = {
    "name": "Crystal",
    "profile_image": "images/crystal_profile.png",
    "token_image": "images/crystal_token.png",
    "stats": {
        "vtl":2,
        "sen":2,
        "per":2,
        "tal":2,
        "mst":2
    },
    "class": "physical",
    "type": "none",
    "skills": ["Grappling","Jet-shoes","Contortion"],
    "current_hp": 100,
    "pos": "Y3"
}