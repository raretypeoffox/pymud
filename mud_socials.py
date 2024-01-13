# mud_socials.py




from mud_shared import first_to_upper, log_error, log_info
from mud_comms import send_message, send_room_message, send_room_message_processing





SOCIALS = {
    
    'sing': [
        "You lift your voice in song, letting the melody flow from your heart.",
        "$A starts to sing, their voice filling the air with sweet music.",
        "You serenade $D with a beautiful song, your eyes twinkling with joy.",
        "$A sings to you, their voice resonating with a melody that touches your soul.",
        "$A sings a melodious tune for $D, their voice warm and inviting." 
    ]
   
}

def process_message(msg, player_name="", target_name=""):
    msg = msg.replace("$A", first_to_upper(player_name))
    msg = msg.replace("$D", first_to_upper(target_name))
    return msg + "\n"


def handle_social(player, social, argument):
        
    if social not in SOCIALS:
        return False
    
    if argument == '':
        msg_to_player = process_message(SOCIALS[social][0], player.name)
        msg_to_room = process_message(SOCIALS[social][1], player.name)
        send_room_message(player.current_room, msg_to_room, excluded_player=player, excluded_msg=msg_to_player)
        return True
    else:
        player_target = player.current_room.search_players(argument)
        mob_target = player.current_room.search_mobs(argument)
        if player_target is None and mob_target is None:
            send_message(player, "You can't find them!\n")
            return False
        elif player_target is not None:
            msg_to_player = process_message(SOCIALS[social][2], player.name, player_target.name)
            msg_to_target = process_message(SOCIALS[social][3], player.name, player_target.name)
            msg_to_room = process_message(SOCIALS[social][4], player.name, player_target.name)
            send_room_message(player.current_room, msg_to_room, excluded_player=[player, player_target], excluded_msg=[msg_to_player, msg_to_target])
            return True
        elif mob_target is not None:
            msg_to_player = process_message(SOCIALS[social][2], player.name, mob_target.name)
            msg_to_room = process_message(SOCIALS[social][4], player.name, mob_target.name)
            send_room_message(player.current_room, msg_to_room, excluded_player=player, excluded_msg=msg_to_player)
            return True
        
def list_socials(player, argument):
    send_message(player, "Available socials:\n")
    for social in SOCIALS:
        send_message(player, f"{social}\n")
    