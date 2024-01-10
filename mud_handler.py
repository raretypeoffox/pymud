# mud_handler.py
import difflib
from functools import partial
from datetime import datetime

import mud_consts
from mud_comms import send_message, send_room_message, player_manager, handle_disconnection
from mud_shared import colourize, match_keyword

from mud_world import room_manager
from mud_objects import player_db
from mud_combat import test_kill_mob

def kill_command(player, argument):
    if argument == '':
        send_message(player, "You must specify a mob name.\n")
        return
    
    room_instance = room_manager.get_room_by_vnum(player.room_id)
    # compare argument against mob keywords in room and if there's a match, return instance
    mob_list = room_instance.get_mob_keywords_and_instances()

    target_mob = None
    for keywords, mob_instance in mob_list:
        if match_keyword(keywords, argument):
            target_mob = mob_instance
            break

    if target_mob is None:
        send_message(player, "No mob with that name found.\n")
    else:
        # Proceed with the combat
        test_kill_mob(player, target_mob)
    
    


def say_command(player, argument):
    if argument == '':
        send_message(player, "Say what??\n")
        return
    
    msg = colourize(f"{player.name} says '{argument}'\n", "yellow")
    excluded_msg = colourize(f"You say '{argument}'\n", "yellow")
    send_room_message(player.room_id, msg, excluded_player=player, excluded_msg=excluded_msg)
            
def chat_command(player, argument):
    if argument == '':
        send_message(player, "It's easier to chat when you say something.\n")
        return
    
    for other_player in player_manager.get_players():
        if other_player != player:
            msg = colourize(f"{player.name} chats '{argument}'\n", "cyan")
            send_message(other_player, f"{msg}")
        else:
            msg = colourize(f"You chat '{argument}'\n", "cyan")
            send_message(player, msg)

def score_command(player, argument):
    send_message(player, colourize(f"You are {player.name}, {player.character.origin}\n", "cyan"))
    send_message(player, f"Level {player.character.level}, {player.character.race}\tEXP/TNL: {player.character.xp}/{player.character.tnl}\n")
    send_message(player, colourize(f"-----------------------------------------------------------------------------\n", "yellow"))
    send_message(player, f"Str\t:\t{player.character.str}\tYou have {player.character.current_hitpoints}/{player.character.max_hitpoints} hitpoints.\n")
    send_message(player, f"Dex\t:\t{player.character.dex}\tYou have {player.character.current_mana}/{player.character.max_mana} mana.\n")
    send_message(player, f"Con\t:\t{player.character.con}\tYou have {player.character.current_stamina}/{player.character.max_stamina} stamina.\n")
    send_message(player, f"Int\t:\t{player.character.int}\n")
    send_message(player, f"Wis\t:\t{player.character.wis}\n")
    send_message(player, f"Cha\t:\t{player.character.cha}\n")
    send_message(player, colourize(f"-----------------------------------------------------------------------------\n", "yellow"))   
    
         
def who_command(player, argument):
    send_message(player, colourize("Heroes...\n", "green"))
    send_message(player, colourize("---------\n", "green"))
    count = 0
    for other_player in player_manager.get_players():
        send_message(player, colourize(f"[{other_player.character.level : >4} {mud_consts.RACES_ABV[other_player.character.race]: <5}] {other_player.name}, {other_player.character.origin}\n", "green"))
        count += 1
    send_message(player, colourize(f"\n{count} players online.\n", "green"))

def last_command(player, argument):
    if argument == '':
        send_message(player, "You must specify a player name.\n")
        return
    
    result = player_db.get_player_created_lastlogin(argument)
    if result is None:
        send_message(player, f"No player with the name {argument} found.")
    else:
        created, lastlogin = result
        today = datetime.now().date()

        if created.date() == today:
            formatted_created = "today"
        else:
            formatted_created = created.strftime("%B %d, %Y")

        if lastlogin.date() == today:
            formatted_lastlogin = "today"
        else:
            formatted_lastlogin = lastlogin.strftime("%B %d, %Y")

        send_message(player, f'Player was created {formatted_created} and last logged in {formatted_lastlogin}\n')
                   
def quit_command(player, argument):
    handle_disconnection(player, "Goodbye! Hope to see you soon...\n")

def recall_command(player, argument):
    argument = argument.lower()
    if argument == 'show':
        # print a message to player showing the room name (based on the room_vnum from player.get_recall()
        recall_room_vnum = player.get_recall()
        if recall_room_vnum == 0:
            send_message(player, "You have no recall set.\n")
            return
        room_instance = room_manager.get_room_by_vnum(recall_room_vnum)
        send_message(player, f"Recall is set to: {room_instance.name}.\n")
        return
    elif argument == 'clear':
        # clear the recall room
        player.set_recall(0)
        send_message(player, "Recall cleared.\n")
        return        
    
    if room_manager.get_room_by_vnum(player.room_id).cursed:
        send_message(player, "Room is cursed and you cannot recall here.\n")
        return

    if argument == 'set':
        # set the recall room to the current room
        player.set_recall(player.room_id)
        send_message(player, "Recall set.\n")
        return
    
    if argument == '':    
        recall_room_vnum = player.get_recall()
        if recall_room_vnum == 0:
            send_message(player, "You have no recall set.\n")
            return
        
        if recall_room_vnum == player.room_id:
            send_message(player, "You are already there!\n")
            return
        
        msg = colourize(f"{player.name} utters the word 'recall' and suddenly disappears!\n", "green")
        excluded_msg = colourize("You feel a strange sensation as you are magically transported.\n", "green")
        move_player(player, player.room_id, recall_room_vnum, msg_to_room=msg, msg_to_player=excluded_msg)
        send_room_message(recall_room_vnum, colourize(f"{player.name} arrives from the ether.\n", "green"), excluded_player=player)
    else:
        send_message(player, "Available commands are 'recall', 'recall set', 'recall show' and 'recall clear'\n")

def look_command(player, argument):
    
    if argument == '':
        room_instance = room_manager.get_room_by_vnum(player.room_id)
        
        if room_instance is not None:
            exit_names = colourize("Exits: [" + room_instance.get_exit_names() + "]", "yellow")
            send_message(player, f"{colourize(room_instance.name,"yellow")}\n{exit_names}\n{room_instance.description}")
            player_names = room_instance.get_player_names(excluding_player=player)
            if player_names != '':
                player_names_str = '\n'.join('\t' + name for name in player_names)
                send_message(player, f"{player_names_str}\n")
            mob_names = room_instance.get_mob_names()
            if mob_names != '':
                send_message(player, f"{mob_names}\n")
    else:
        room_instance = room_manager.get_room_by_vnum(player.room_id)
        if room_instance is not None:
            userinput = argument.split()[0]
            keywords = room_instance.get_door_keywords()
            match = match_keyword(keywords, userinput)
            if match:
                msg = room_instance.get_door_description_by_keyword(match)
                send_message(player, f"{msg}\n")
                return
            keywords = room_instance.get_extended__description_keywords()
            match = match_keyword(keywords, userinput)
            if match:
                msg = room_instance.get_extended_description_by_keyword(match)
                send_message(player, f"{msg}\n")
                return
            keywords = room_instance.get_mob_keywords()
            match = match_keyword(keywords, userinput)
            if match:
                msg = room_instance.get_mob_description_by_keyword(match)
                send_message(player, f"{msg}\n")
                return
            # todo add objects
            
            
            
    
def motd_command(player, argument):
    send_message(player, mud_consts.MOTD)


def player_movement(player, direction):
    room_instance = room_manager.get_room_by_vnum(player.room_id)
    if room_instance is not None:
        if direction in room_instance.doors:
            if room_instance.doors[direction]["locks"] == 0:
                move_player(player, player.room_id, room_instance.doors[direction]["to_room"], msg_to_room=colourize(f"{player.name} leaves to the {mud_consts.DIRECTIONS[direction]}.\n", "green"))
                send_room_message(room_instance.doors[direction]["to_room"], colourize(f"{player.name} arrives from the {mud_consts.DIRECTIONS_REVERSE[direction]}.\n", "green"), excluded_player=player)
            else:
                send_message(player, "The door is locked.\n")
        else:
            send_message(player, "There is no door that way.\n")
            
def goto_command(player, argument):
    if argument == '':
        send_message(player, "You must specify a room number.\n")
    else:
        room_id = int(argument)
        try:
            room = room_manager.get_room_by_vnum(room_id)
        except:
            room = None
        if room is None:
            send_message(player, "No room with that number found.\n")
              
        msg = colourize(f"{player.name} utters the word 'goto' and suddenly disappears!\n", "green")
        excluded_msg = colourize("You feel a strange sensation as you are magically transported.\n", "green")
        move_player(player, player.room_id, room_id, msg_to_room=msg, msg_to_player=excluded_msg)


def north_command(player, argument):
    player_movement(player, 0)

def east_command(player, argument):
    player_movement(player, 1)
            
def south_command(player, argument):
    player_movement(player, 2)

def west_command(player, argument):
    player_movement(player, 3)

def up_command(player, argument):
    player_movement(player, 4)

def down_command(player, argument):
    player_movement(player, 5)
    
def cmds_command(player, argument):
    send_message(player, "Commands implemented:\n")
    for cmds in commands:
        send_message(player, f"{cmds}\n")

commands = {
    'kill': [kill_command], 
    'say': [say_command],
    'chat' : [chat_command],
    'who': [who_command],
    'last': [last_command],
    'score': [score_command],
    'recall': [recall_command],
    'quit': [quit_command],
    'look': [look_command],
    'motd': [motd_command],
    'north': [north_command],
    'east': [east_command],
    'south': [south_command],
    'west': [west_command],
    'up': [up_command],
    'down': [down_command],
    'goto': [goto_command],
    'cmds' : [cmds_command],
    # Add more commands here...
}


def handle_player(player, msg):
    # Strip the msg of whitespace and newlines then split into command and argument
    msg = msg.rstrip()
    parts = msg.split(' ', 1)
    command = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else ''

    if msg == '':
        return

    # Define command shortcuts
    shortcuts = {
        'n': 'north',
        'e': 'east',
        's': 'south',
        'w': 'west',
        'u': 'up',
        'd': 'down',
        'l': 'look',
        # Add more shortcuts here...
    }

    # Define full commands
    full_commands = {'quit'}

    # Get the command function
    if command in shortcuts:
        command_func = commands[shortcuts[command]][0]
    elif command in full_commands:
        command_func = commands[command][0] if command in commands else None
    else:
        # Find the first command that starts with the command entered by the player
        matches = [cmd for cmd in commands if cmd.startswith(command)]
        if matches:
            if matches[0] in full_commands:
                send_message(player, f"You need to type the full command '{matches[0]}' for it to work.\n")
                return
            command_func = commands[matches[0]][0]
        else:
            command_func = None

    # If the command exists, execute it
    if command_func:
        command_func(player, argument)
    else:
        send_message(player, "I'm sorry, I don't understand you.\n")
        
    send_message(player, player.get_prompt())
        
        
def move_player(player, old_room_vnum, new_room_vnum, msg_to_room=None, msg_to_player=None):
    """move player from old_room to new_room, use room vnums"""
    
    send_room_message(old_room_vnum, msg_to_room, excluded_player=player, excluded_msg=msg_to_player)
    player.move_to_room(room_manager.get_room_by_vnum(new_room_vnum))
    look_command(player, "")