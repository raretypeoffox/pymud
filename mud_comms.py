# mud_comms.py

import sys

# import local files
import mud_password
import mud_consts


from mud_objects import Player, PlayerManager
from mud_world import room_manager
from mud_shared import log_info, log_error, colourize

player_manager = PlayerManager()

def send_room_message(room_vnum, msg, excluded_player=None, excluded_msg=None):
    room = room_manager.get_room_by_vnum(room_vnum)
    for player in room.get_players():
        if player != excluded_player:
            send_message(player, msg)
        else:
            if excluded_msg is not None:
                send_message(player, excluded_msg)

def send_global_message(msg):
    for player in player_manager.players:
        send_message(player, msg)
        
def send_message(player, msg):
    try:
        player.socket.sendall(msg.encode('utf-8'))
    except (BrokenPipeError, OSError):
        handle_disconnection(player)
    
# Character login functions
    
def handle_client_login(player, msg):
    print("Handle_client_login", player.fd, ":", msg)
    if player.name is None:
        handle_new_character(player, msg)
    elif player.reconnect_prompt:
        handle_reconnect_prompt(player, msg)
    elif player.awaiting_reconnect_confirmation:
        handle_reconnect_confirmation(player, msg)
    elif player.awaiting_race:
        handle_race_set(player, msg)
    elif player.awaiting_origin:
        handle_origin_set(player, msg)
    else:
        handle_password_verification(player, msg)

def handle_new_character(player, msg):
    player.name = msg.strip()
    stored_password = mud_password.load_password(player.name)
    if stored_password is not None:
        handle_existing_player(player)
    else:
        send_message(player, "New Character! Welcome, " + player.name + "!\n")
        send_message(player, "Please set your password: ")

def handle_existing_player(player):
    existing_player = player_manager.get_player_by_name(player.name)
    if existing_player and existing_player.loggedin:
        player.reconnect_prompt = True
    send_message(player, "Welcome back, " + player.name + "!\n")
    send_message(player, "What is your password? ")

def handle_reconnect_prompt(player, msg):
    stored_password = mud_password.load_password(player.name)
    if mud_password.verify_password(stored_password, msg.strip()):
        send_message(player, "This character is already connected. Do you wish to reconnect? (Y/N) ")
        player.reconnect_prompt = False
        player.awaiting_reconnect_confirmation = True
    else:
        send_message(player, "Invalid password.\n")
        send_message(player, "What is your password? ")

def handle_reconnect_confirmation(player, msg):
    if msg.strip().lower() == 'y':
        existing_player = player_manager.get_player_by_name(player.name)
        handle_disconnection(existing_player, "Reconnected from another location.\n")
        finish_login(player, "Reconnected successfully!\n", f"{player.name} reconnected.")
    else:
        send_message(player, "Please choose a different name: ")
        player.name = None
    player.awaiting_reconnect_confirmation = False

def handle_password_verification(player, msg):
    stored_password = mud_password.load_password(player.name)
    if stored_password is None:
        # Create a new character
        mud_password.save_password(player.name, msg.strip())
        player.awaiting_race = True
        send_message(player, mud_consts.RACE_MSG)
    elif mud_password.verify_password(stored_password, msg.strip()):
        # Check if player exists in PlayerDatabase
        if not player.save_exists():
            player.awaiting_race = True
            send_message(player, mud_consts.RACE_MSG)
        else:
            finish_login(player, "Login successful!\n", f"{player.name} logged in.")
    else:
        send_message(player, "Incorrect password! Please try again: \n")

def handle_race_set(player, msg):
    comp = msg.strip().lower().rstrip("s")
    matching_races = [race for race in mud_consts.RACES if comp in race.lower()]
    if matching_races:
        player.character.race = matching_races[0].capitalize()
        player.character.set_racial_stats(*mud_consts.RACES[player.character.race])
        player.awaiting_race = False
        player.awaiting_origin = True
        send_message(player, mud_consts.ORIGIN_MSG)
    else:
        send_message(player, "Invalid race! Please choose a valid race.\n")
        send_message(player, mud_consts.RACE_MSG)
        
def handle_origin_set(player, msg):
    try:
        comp = int(msg.strip())
        comp -= 1
        if mud_consts.ORIGINS[comp]:
            player.character.origin = mud_consts.ORIGINS[comp]
            player.awaiting_origin = False
            player.save()
            finish_login(player, "Character created successfully!\n", f"New character created: {player.name}")
        else:
            send_message(player, "Invalid origin! Please choose a valid origin.\n")
            send_message(player, mud_consts.ORIGIN_MSG)
    except ValueError:
        send_message(player, "Invalid origin! Please choose a valid origin.\n")
        send_message(player, mud_consts.ORIGIN_MSG)
        return

def finish_login(player, msg, log_msg):
    player.loggedin = True
    if player.awaiting_reconnect_confirmation is False:
        send_message(player, mud_consts.MOTD)
    room_manager.get_room_by_vnum(player.current_room).add_player(player)
    player.load()
    send_message(player, msg)
    log_info(log_msg)
    send_global_message(colourize(f"[INFO: {player.name} has entered the game.]\n", "red"))
    send_room_message(player.current_room, colourize(f"{player.name} suddenly appears in the room.\n", "green"), player)
    del player.reconnect_prompt
    del player.awaiting_reconnect_confirmation
    del player.awaiting_race
    del player.awaiting_origin
    
            
def handle_disconnection(player, msg=""):
    print(f"{player.fd}: Player {player.name} disconnected: {msg}")
    log_info(f"{player.name} disconnected: {msg}")
    new_room_instance = room_manager.get_room_by_vnum(player.current_room)
    new_room_instance.remove_player(player)   
    player_manager.disconnect_player(player, msg)
    player.socket.close()
    send_global_message(colourize(f"[INFO: {player.name} has left the game.]\n", "red"))
        
def handle_new_client(client_socket):
    player = Player(client_socket.fileno())
    player.socket = client_socket
    player_manager.add_player(player)

    send_message(player, mud_consts.Greeting)
    
    send_message(player, "What name is your character known by? ")            
    
def handle_shutdown(signum, frame):
    print("Shutting down...")
    log_info("Shutting down...")
    if signum:
        log_error("Received signal " + str(signum))
    player_manager.save_all_players()
    sys.exit(0)
    
