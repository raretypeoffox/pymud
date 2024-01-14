# mud_socials.py




from mud_shared import first_to_upper, colourize, search_items
from mud_comms import send_message, send_room_message
from mud_objects import room_manager





SOCIALS = {
    
    'sing': [
        "You lift your voice in song, letting the melody flow from your heart.",
        "$A starts to sing, their voice filling the air with sweet music.",
        "You serenade $D with a beautiful song, your eyes twinkling with joy.",
        "$A sings to you, their voice resonating with a melody that touches your soul.",
        "$A sings a melodious tune for $D, their voice warm and inviting." 
    ],

    'laugh': [
        "You throw your head back and laugh heartily.",
        "$A laughs heartily, filling the room with joy.",
        "You laugh at $D, finding humor in the situation.",
        "$A laughs at you, their mirth infectious.",
        "$A laughs at $D, sharing a moment of humor."
    ],

    'nod': [
        "You nod in agreement.",
        "$A nods solemnly.",
        "You nod at $D, signaling your agreement.",
        "$A nods at you, acknowledging your presence.",
        "$A nods at $D in agreement."
    ],

    'wave': [
        "You wave your hand cheerfully.",
        "$A waves cheerfully at the room.",
        "You wave at $D, greeting them warmly.",
        "$A waves at you, greeting you warmly.",
        "$A waves at $D, greeting them."
    ],

    'shrug': [
        "You shrug nonchalantly.",
        "$A shrugs, seemingly indifferent.",
        "You shrug at $D, unsure of what to say.",
        "$A shrugs at you, a look of uncertainty on their face.",
        "$A shrugs at $D, expressing their uncertainty."
    ],

    'smile': [
        "You smile broadly.",
        "$A smiles warmly.",
        "You smile at $D.",
        "$A smiles at you.",
        "$A smiles at $D."
    ],

    'frown': [
        "You frown in concern.",
        "$A frowns, looking worried.",
        "You frown at $D.",
        "$A frowns at you.",
        "$A frowns at $D."
    ],

    'wink': [
        "You wink slyly.",
        "$A winks mischievously.",
        "You wink at $D.",
        "$A winks at you.",
        "$A winks at $D."
    ],

    'gasp': [
        "You gasp in surprise.",
        "$A gasps aloud.",
        "You gasp at $D.",
        "$A gasps at you.",
        "$A gasps at $D."
    ],

    'bow': [
        "You bow respectfully.",
        "$A bows gracefully.",
        "You bow before $D.",
        "$A bows before you.",
        "$A bows before $D."
    ],

    'clap': [
        "You clap your hands together enthusiastically.",
        "$A claps their hands together with enthusiasm.",
        "You clap for $D, showing your appreciation.",
        "$A claps for you, showing their appreciation.",
        "$A claps for $D, applauding them."
    ],

    'ponder': [
        "You ponder the situation deeply.",
        "$A looks deep in thought.",
        "You ponder what $D said.",
        "$A ponders your words carefully.",
        "$A ponders what $D said."
    ],

    'yawn': [
        "You yawn widely, feeling tired.",
        "$A yawns, looking tired.",
        "You yawn at $D, unable to hide your tiredness.",
        "$A yawns at you, clearly tired.",
        "$A yawns at $D, looking bored."
    ],

    'cheer': [
        "You cheer loudly, full of excitement.",
        "$A cheers loudly, filled with enthusiasm.",
        "You cheer $D on, encouraging them.",
        "$A cheers you on enthusiastically.",
        "$A cheers for $D loudly."
    ],

    'sigh': [
        "You let out a long, deep sigh.",
        "$A sighs deeply.",
        "You sigh at $D.",
        "$A sighs at you.",
        "$A sighs at $D."
    ],

    'blush': [
        "You blush a deep shade of red.",
        "$A blushes, their cheeks turning red.",
        "You blush at $D's words.",
        "$A blushes at your words.",
        "$A blushes at what $D says."
    ],

    'grin': [
        "You grin mischievously.",
        "$A grins mischievously.",
        "You grin at $D.",
        "$A grins at you.",
        "$A grins at $D."
    ],

    'gaze': [
        "You gaze off into the distance, lost in thought.",
        "$A gazes off into the distance.",
        "You gaze into $D's eyes.",
        "$A gazes into your eyes.",
        "$A gazes into $D's eyes."
    ],

    'groan': [
        "You groan loudly in frustration.",
        "$A groans loudly.",
        "You groan at $D's actions.",
        "$A groans at you.",
        "$A groans at what $D does."
    ],

    'stretch': [
        "You stretch your arms wide.",
        "$A stretches their arms wide.",
        "You stretch and yawn at $D.",
        "$A stretches and yawns at you.",
        "$A stretches and yawns at $D."
    ],
    
    'tip': [
        "You tip your hat in a courteous gesture.",
        "$A tips their hat courteously.",
        "You tip your hat to $D in a respectful manner.",
        "$A tips their hat to you respectfully.",
        "$A tips their hat to $D in a sign of respect."
    ],
    
    'thank': [
        "You express your heartfelt thanks.",
        "$A expresses heartfelt thanks.",
        "You thank $D sincerely.",
        "$A thanks you sincerely.",
        "$A thanks $D with sincerity."
    ],
        
    'grovel': [
        "You fall to your knees, groveling.",
        "$A falls to their knees, groveling.",
        "You grovel before $D, seeking favor.",
        "$A grovels before you, seeking favor.",
        "$A grovels before $D."
    ],
    
    'dance': [
        "You start dancing joyously.",
        "$A starts dancing joyously.",
        "You dance around $D happily.",
        "$A dances around you happily.",
        "$A dances around $D with joy."
    ],
    
     'glare': [
        "You glare around fiercely.",
        "$A glares around fiercely.",
        "You glare fiercely at $D.",
        "$A glares fiercely at you.",
        "$A glares fiercely at $D."
    ],
    
    'pat': [
        "You pat yourself on the back.",
        "$A pats themselves on the back.",
        "You pat $D on the back.",
        "$A pats you on the back.",
        "$A pats $D on the back."
    ],
    
    'whistle': [
        "You whistle a cheerful tune.",
        "$A whistles a cheerful tune.",
        "You whistle a tune at $D.",
        "$A whistles a tune at you.",
        "$A whistles a tune at $D."
    ],
    
    'giggle': [
        "You giggle to yourself.",
        "$A giggles softly.",
        "You giggle at $D.",
        "$A giggles at you.",
        "$A giggles at $D."
    ],
    
    'cough': [
        "You cough to clear your throat.",
        "$A coughs loudly.",
        "You cough in $D's direction.",
        "$A coughs in your direction.",
        "$A coughs in $D's direction."
    ],
    
    'sneer': [
        "You sneer contemptuously.",
        "$A sneers contemptuously.",
        "You sneer at $D.",
        "$A sneers at you.",
        "$A sneers at $D."
    ],
    
    'stare': [
        "You stare into space.",
        "$A stares blankly into space.",
        "You stare intently at $D.",
        "$A stares intently at you.",
        "$A stares intently at $D."
    ],
    
    'shiver': [
        "You shiver from the cold.",
        "$A shivers from the cold.",
        "You shiver visibly next to $D.",
        "$A shivers visibly next to you.",
        "$A shivers visibly next to $D."
    ],
    
    'salute': [
        "You stand at attention and offer a crisp salute.",
        "$A stands straight and salutes sharply.",
        "You salute $D with respect and dignity.",
        "$A salutes you, a gesture of respect and formality.",
        "$A raises their hand in a salute to $D."
    ]

    
}

# Callbacks for socials that require special processing

def sing_callback(player, argument):
    if player.current_room.vnum == 3103:
        msg = "\nThe Ancient Oak seems to listen intently as you sing. Its leaves rustle, creating a melody that harmonizes with your tune. With a final note, a verdant glow envelops you, and you are whisked away, finding yourself before the enchanting entrance of Whisperwood Hollow.\n"
        msg_to_room = f"\nAs {player.name} sings to the Ancient Oak, a whirlwind of leaves and light envelops them, and in a blink, they vanish, leaving a faint echo of their song behind.\n"
        msg = colourize(msg, "bright magenta")
        msg_to_room = colourize(msg_to_room, "bright magenta")
        
        send_room_message(player.current_room, msg_to_room, excluded_player=player, excluded_msg=msg)
        
        if not hasattr(player.character, 'death_room'):
            setattr(player.character, 'death_room', 3399)
        elif player.character.death_room is None or player.character.death_room == 3000:
            player.character.death_room = 3399
        
        player.move_to_room(room_manager.get_room_by_vnum(3300))
        send_room_message(player.current_room, f"{player.name} appears in a whirlwind of leaves and light, their eyes wide with wonder.\n", excluded_player=player)
    pass

SOCIALS_CALLBACKS = {
    'sing': sing_callback,
}

def process_message(msg, player_name="", target_name=""):
    msg = msg.replace("$A", player_name)
    msg = msg.replace("$D", target_name)
    return msg + "\n"


def handle_social(player, social, argument):
        
    if social not in SOCIALS:
        return False
    
    if argument == '':
        msg_to_player = process_message(SOCIALS[social][0], player.name)
        msg_to_room = process_message(SOCIALS[social][1], player.name)
        send_room_message(player.current_room, msg_to_room, excluded_player=player, excluded_msg=msg_to_player)
        # return True
    else:
        target = search_items((player.current_room.get_players() | player.current_room.get_mobs()), argument)
        if target is not None:
            msg_to_player = process_message(SOCIALS[social][2], player.name, target.name)
            msg_to_target = process_message(SOCIALS[social][3], player.name, target.name)
            msg_to_room = process_message(SOCIALS[social][4], player.name, target.name)
            send_room_message(player.current_room, first_to_upper(msg_to_room), excluded_player=[player, target], excluded_msg=[first_to_upper(msg_to_player), first_to_upper(msg_to_target)])
        else:
            send_message(player, "You can't find them!\n")
            return False
        
    # Check if there's a callback for the social
    if social in SOCIALS_CALLBACKS:
        # Call the callback function
        SOCIALS_CALLBACKS[social](player, argument)
        
    return True
        
def list_socials(player, argument):
    send_message(player, "Available socials:\n")
    for social in SOCIALS:
        send_message(player, f"{social}\n")
    