# mud_comms.py

import sys
import socket


# import local files
import mud_password
import mud_consts

from mud_objects import Player, player_manager
from mud_world import room_manager
from mud_shared import log_info, log_error, colourize, first_to_upper, read_motd



def send_room_message_processing(player, target, msg):
    
    target_name = ""
    if target is not None:
        target_name = target.name
    
    if player.current_room is None:
        log_error(f"{player.name} has no room instance")
        return
    
    
    msg_to_player = msg
    msg_to_player = msg_to_player.replace("$A", "you")
    msg_to_player = msg_to_player.replace("$e", "")
    msg_to_player = msg_to_player.replace("$s", "")
    msg_to_player = msg_to_player.replace("$D", target_name)
    msg_to_player = first_to_upper(msg_to_player)
    
    msg = msg.replace("$s", "s")
    msg = msg.replace("$e", "e")
    msg = msg.replace("$A", player.name)
    
    msg_to_room = msg
    msg_to_room = msg_to_room.replace("$D", target_name)
    msg_to_room = first_to_upper(msg_to_room)
    
    if target is not None:
        msg_to_target = msg
        msg_to_target = msg_to_target.replace("$D", "you")
        msg_to_target = first_to_upper(msg_to_target)
        
        send_room_message(player.current_room, msg_to_room, [player, target], [msg_to_player, msg_to_target])
    else:
        send_room_message(player.current_room, msg_to_room, player, msg_to_player)
    

def send_room_message(room, msg, excluded_player=None, excluded_msg=None):
    """
    Sends a message to all players in a room, excluding specified players.

    This function iterates over all players in the given room and sends them the message. 
    If a player is in the excluded_player list, they receive the corresponding excluded_msg instead of the main message.

    Args:
        room (Room): The room where the message should be sent.
        msg (str): The message to be sent.
        excluded_player (Player or list of Player, optional): A player or list of players who should not receive the main message. Defaults to None.
        excluded_msg (str or list of str, optional): A message or list of messages to be sent to the excluded players. Defaults to None.

    Returns:
        None
    """
    if not isinstance(excluded_player, list):
        excluded_player = [excluded_player]
    if isinstance(excluded_msg, str):
        excluded_msg = [excluded_msg]
    
    if room is None:
        log_error("Room is None")
        return
    
    for player in room.get_players():
        if not player.character.is_awake() or player.character.NPC:
            continue
        if player not in excluded_player:
            room_msg = msg
            send_message(player, room_msg)
        else:
            if excluded_msg is not None:
                index = excluded_player.index(player)
                if index < len(excluded_msg):
                    send_message(player, excluded_msg[index])
       
def send_info_message(msg, InfoType="INFO", colour="red"):
    send_global_message(colourize(f"[{InfoType}]: {msg}\n", colour))
             
def send_global_message(msg):
    for player in player_manager.get_players(LoggedIn=True):
            send_message(player, msg)
        
def send_message(player, msg):
    """
    Sends a message to a specific player.

    This function checks if the player's character is not an NPC, and if so, appends the message to the player's output buffer.
    The actual sending of the message is handled elsewhere (in the process_output function).

    Args:
        player (Player): The player to whom the message should be sent.
        msg (str): The message to be sent.

    Returns:
        None
    """
    if player.character is not None and player.character.NPC is True:
        return
    player.output_buffer += msg
    
def process_output(NewLineAtStart=True):
    for player in player_manager.get_players(LoggedIn=False):
        if player.output_buffer != "":
            if player.loggedin:
                if NewLineAtStart:
                    player.output_buffer = "\n" + player.output_buffer
                player.output_buffer += player.character.get_prompt()
            try:
                player.socket.sendall(player.output_buffer.encode('utf-8'))
            except (BrokenPipeError, OSError):
                handle_disconnection(player)
            except socket.timeout:
                log_error(f"Socket operation timed out for player {player.fd}")
            except UnicodeEncodeError:
                log_error(f"Failed to encode message for player {player.fd}")
            except Exception as e:  # This will catch any other types of exceptions
                log_error(f"Unexpected error while sending player output: {e}")
            finally:
                player.output_buffer = ""
                

              
# Character login functions

def handle_new_client(client_socket):
    player = Player(client_socket.fileno(), client_socket)
    player_manager.add(client_socket, player)

    send_message(player, mud_consts.Greeting)
    
    send_message(player, "What name is your character known by? ")      
    
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
    player.name = first_to_upper(msg).strip()
    if player.name.isalpha() == False:
        send_message(player, "Invalid name! Please choose alpha characters only: ")
        player.name = None
        return
    elif len(player.name) < 3:
        send_message(player, "Name must be at least 3 characters long! Please choose a different name: ")
        player.name = None
        return
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
            finish_login(player, "\nLogin successful!\n", f"{player.name} logged in.")
    else:
        send_message(player, "Incorrect password! Please try again: \n")

def handle_race_set(player, msg):
    comp = msg.strip().lower().rstrip("s")
    matching_races = [race for race in mud_consts.RACES if comp in race.lower()]
    if matching_races and comp != '':
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
            finish_login(player, "Character created successfully!\n", f"New character created: {player.name}")
        else:
            send_message(player, "Invalid origin! Please choose a valid origin.\n")
            send_message(player, mud_consts.ORIGIN_MSG)
    except ValueError:
        send_message(player, "Invalid origin! Please choose a valid origin.\n")
        send_message(player, mud_consts.ORIGIN_MSG)
        return

from mud_abilities import Abilities

def finish_login(player, msg, log_msg):    
    player.loggedin = True
    if player.awaiting_reconnect_confirmation is False:
        send_message(player, read_motd() + "\n")
    player.load()
    #DB Hack - when adding new things to character, use this to ensure all old characters get it:
    if hasattr(player.character, 'alignment') == False:
        log_info("finish_login(): adding alignment to player " + player.name)
        player.character.alignment = 0
    if hasattr(player.character, 'abilities') == False:
        player.character.abilities = Abilities()
        log_info("finish_login(): adding abilities to player " + player.name)

    # #DB Hack end
    player.save()
    if player.character.race == '':
        log_error("finish_login(): why did a player make it here without a race?")
    room = room_manager.get(player.room_id)
    room.add_player(player)
    player.set_room(room)
    send_message(player, msg)
    log_info(log_msg)
    send_info_message(f"{player.name} has entered the game.")
    send_room_message(player.current_room, colourize(f"\n{player.name} suddenly appears in the room.", "green"), excluded_player=player)
    del player.reconnect_prompt
    del player.awaiting_reconnect_confirmation
    del player.awaiting_race
    del player.awaiting_origin
    
            
def handle_disconnection(player, msg=""):
    if player is None:
        return
    log_info(f"{player.fd}: {player.name} disconnected: {msg}")
    if player.current_room is not None:
        player.current_room.remove_player(player)
    if player_manager.disconnect_player(player, msg) and player.name != None:
        send_info_message(f"{player.name} has left the game.")
        send_room_message(player.current_room, colourize(f"\n{player.name} has left the game.", "green"), player)
    try:
        player.socket.close()
    except OSError:
        log_error(f"Error when closing socket for player {player.name}")
    except Exception as e:
        log_error(f"Unexpected error when closing socket for player {player.name}: {e}")      
    
def handle_shutdown(signum, frame):
    print("Shutting down...")
    log_info("Shutting down...")
    if signum:
        log_error("Received signal " + str(signum))
    player_manager.save_all_players()
    sys.exit(0)
    
