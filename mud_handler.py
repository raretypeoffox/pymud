# mud_handler.py
from datetime import datetime
import pickle
import random

import mud_consts
from mud_consts import RoomFlags
from mud_comms import send_message, send_room_message, handle_disconnection
from mud_shared import colourize, is_NPC, read_motd, first_to_upper, log_error, search_items, check_flag

from mud_world import room_manager
from mud_objects import player_db, player_manager, combat_manager
from mud_combat import kill_mob, attempt_flee
from mud_spells import do_cast
from mud_socials import handle_social, list_socials
from mud_abilities import ScrollsAndSpellbooks, AbilityType
from mud_mprog import mprog_room_check


def cast_command(player, argument):
    do_cast(player, argument)
    
def chat_command(player, argument):
    if argument == '':
        send_message(player, "It's easier to chat when you say something.\n")
        return
    
    for other_player in player_manager.get_players():
        if other_player != player and other_player.loggedin:
            msg = colourize(f"{player.name} chats '{argument}'\n", "cyan")
            send_message(other_player, f"{msg}")
        elif other_player == player:
            msg = colourize(f"You chat '{argument}'\n", "cyan")
            send_message(player, msg)
            
def cmds_command(player, argument):
    send_message(player, "Commands implemented:\n")
    for cmds in commands:
        send_message(player, f"{cmds}\n")
        
def drop_object(player, object):
    # if object.is_droppable() == False:
    # etc
    
    object.drop(player)
    send_message(player, f"You drop {object.name}.\n")
    send_room_message(player.current_room, f"{player.name} drops {object.name}.\n", excluded_player=player)
    
def drop_command(player, argument):
    if argument == '':
        send_message(player, "Drop what?\n")
        return
    
    current_position = player.character.get_position()
    if current_position == "Sleep":
        send_message(player, "You are sleeping!\n")
        return
    
    if argument.split()[0].lower() == 'all':
        print("drop all")
        for object in list(player.get_objects())[::-1]:
            print(object)
            drop_object(player, object)
        return
    
    object = search_items(player.get_objects(), argument)
    
    if object is None:
        send_message(player, "No object with that name found.\n")
        return
    
    drop_object(player, object)

def flee_command(player, argument):
    if combat_manager.in_combat(player) == False:
        send_message(player, "You aren't fighting anyone!\n")
        return
    
    random_door = player.current_room.choose_random_door(exclude_other_area=False)

    if random_door is None:
        send_message(player, "There's no where to flee to!\n")
        return
    
    flee_success = attempt_flee(player, combat_manager.get_current_target(player), random_door)
    
    if flee_success:
        # todo add to mob's aggro list
        
        send_message(player, colourize(player.character.flee_xp_loss(), "red"))
        look_command(player, "")
    else:
        send_message(player, "You fail to flee!\n")
        send_message(player, colourize(player.character.flee_xp_loss(), "red"))
        pass  
          
def follow_command(player, argument):
    if player.character.is_awake() == False:
        send_message(player, "You are sleeping!\n")
        return
    
    if argument == '':
        send_message(player, "Follow who?\n")
        return
    
    if argument == 'self':
        if player.follow is None:
            send_message(player, "You are already following yourself!\n")
            return
        else:
            send_message(player, f"You no longer follow {player.follow.name}.\n")
            player.follow = None
            return

    target = search_items((player.current_room.get_players() | player.current_room.get_mobs()), argument)
    if target is not None:
        if target.follow is not None:
            send_message(player, f"{target.name} is already following someone.\n")
            return
        player.follow=target
        send_message(player, f"You now follow {target.name}.\n")
        return
    else:
        send_message(player, "There's no one here with that name.\n")
        return

def get_object(player, object):
    # if object.is_takeable() == False:
    #     send_message(player, "You can't take that.\n")
    #     return
    
    # if player.character.is_carrying(object):
    #     send_message(player, "You are already carrying that.\n")
    #     return
    
    # if player.character.can_carry(object) == False:
    #     send_message(player, "You can't carry any more.\n")
    #     return
    object.pickup(player)
    send_message(player, f"You get {object.name}.\n")
    send_room_message(player.current_room, f"{player.name} gets {object.name}.\n", excluded_player=player)

def get_command(player, argument):
    if argument == '':
        send_message(player, "Get what?\n")
        return
    
    current_position = player.character.get_position()
    if current_position == "Sleep":
        send_message(player, "You are sleeping!\n")
        return
    
    if len(argument.split()) > 1:
        # todo, implement bags
        pass

    else: # picking up from ground
        if argument.split()[0].lower() == 'all':
            # todo add functionality for "you get several items"
            for object in set(player.current_room.object_list):
                get_object(player, object)
            return

        object = search_items(player.current_room.get_objects(), argument)
        
        if object is None:
            send_message(player, "No item with that name found.\n")
            return
        
        get_object(player, object)
        
def give_command(player, argument):
    current_position = player.character.get_position()
    if current_position == "Sleep":
        send_message(player, "You are sleeping!\n")
        return
    
    if argument == '':
        send_message(player, "Give what?\n")
        return
    
    argument = argument.lower().split()
    
    if len(argument) < 2:
        send_message(player, "Give what to whom?\n")
        return
    
    object = search_items(player.get_objects(), argument[0])
        
    if object is None:
        send_message(player, "No item with that name found.\n")
        return
    
    target = search_items((player.current_room.get_players() | player.current_room.get_mobs()), argument[1])
    
    if target is not None:
        send_room_message(player.current_room, f"{player.name} gives {object.name} to {target.name}.\n", excluded_player=player, excluded_msg=f"You give {object.name} to {target.name}.\n")
        object.give(player, target)
    else:
        send_message(player, "There's no one here with that name.\n")
        return
    
def goto_command(player, argument):
    if argument == '':
        send_message(player, "You must specify a room number.\n")
    else:
        room_id = int(argument)
        room = room_manager.get(room_id)

        if room is None:
            send_message(player, "No room with that number found.\n")
            return
              
        msg = colourize(f"{player.name} utters the word 'goto' and suddenly disappears!\n", "green")
        excluded_msg = colourize("You feel a strange sensation as you are magically transported.\n", "green")
        move_player(player, player.room_id, room_id, msg_to_room=msg, msg_to_player=excluded_msg)
        
def inventory_command(player, argument):
    if len(player.inventory.uuids) == 0:
        send_message(player, "You are not carrying anything.\n")
        return
    
    msg = "You are carrying:\n"
    msg += player.get_inventory_description()
    send_message(player, msg)
                 
def kill_command(player, argument):
    if argument == '':
        send_message(player, "You must specify a mob name.\n")
        return
    
    current_position = player.character.get_position()
    if current_position != "Stand":
        send_message(player, "You need to be standing first!\n")
        return 
    
    mob = search_items(player.current_room.get_mobs(), argument)

    if mob is None:
        send_message(player, "No mob with that name found.\n")
    else:
        kill_mob(player, mob)

def last_command(player, argument):
    if argument == '':
        send_message(player, "You must specify a player name.\n")
        return
    
    result = player_db.query_player(player.name, ["created", "lastlogin", "character"])
    if result is None:
        send_message(player, f"No player with the name {argument} found.\n")
        return
    
    created, lastlogin, character = result
    created = datetime.strptime(created, '%Y-%m-%d %H:%M:%S.%f')
    lastlogin = datetime.strptime(lastlogin, '%Y-%m-%d %H:%M:%S.%f')
    character = pickle.loads(character)
    
    today = datetime.now().date()
    if created.date() == today:
        formatted_created = "today"
    else:
        formatted_created = created.strftime("%B %d, %Y")
        
    if lastlogin.date() == today:
        formatted_lastlogin = "today"
    else:
        formatted_lastlogin = lastlogin.strftime("%B %d, %Y")
        
    if hasattr(character, 'level') is False or hasattr(character, 'race') is False:
        log_error(f"last_command: {argument} has no character level or race")
    else:    
        send_message(player, f"{first_to_upper(argument)} is a level {character.level} {character.race} ")
        
    send_message(player, f"created {formatted_created} and last logged in {formatted_lastlogin}\n")

def look_command(player, argument):
    if is_NPC(player):
        return
    
    if player.character.is_awake() == False:
        send_message(player, colourize(random.choice(mud_consts.LOOK_SLEEPING_MSGS) + "\n", "green"))
        return
    
    room = player.current_room
    
    if argument == '':
    
        if room is not None:
            exit_names = "[Exits: " + room.get_exit_names() + "]"
            send_message(player, f"{colourize(room.name,"yellow")}\n{exit_names}\n{room.description}")
            
            object_names = room.get_object_names()
            if object_names != '':
                send_message(player, f"{object_names}")
            
            player_names = room.get_player_names(excluded_player=player)
            if player_names != '':
                send_message(player, f"{player_names}")
                
            mob_names = room.get_mob_names()
            if mob_names != '':
                send_message(player, f"{mob_names}")
    else:
        # Create a list of all items in the room and in the player's inventory
        all_items = (room.get_players() | player.get_objects() | room.get_mobs() | room.get_objects() | room.get_doors() | room.get_extended_descriptions())

        # Search for the item in the list of all items
        item = search_items(all_items, argument)
        if item is not None:
            send_message(player, f"{item.get_description()}\n")
            return
        
        send_message(player, colourize("You don't see that here.\n", "green"))    

def quit_command(player, argument):
    handle_disconnection(player, colourize(random.choice(mud_consts.GOODBYE_MSGS) + "\n", "bright cyan"))

def recall_command(player, argument):
    if player.character.is_awake() == False:
        send_message(player, "You can't recall while sleeping.\n")
        return
    
    argument = argument.lower()
    if argument == 'show':
        # print a message to player showing the room name (based on the room_vnum from player.get_recall()
        recall_room_vnum = player.get_recall()
        if recall_room_vnum == 0:
            send_message(player, "You have no recall set.\n")
            return
        room_instance = room_manager.get(recall_room_vnum)
        send_message(player, f"Recall is set to: {room_instance.name}.\n")
        return
    elif argument == 'clear':
        # clear the recall room
        player.set_recall(0)
        send_message(player, "Recall cleared.\n")
        return        
    
    if check_flag(room_manager.get(player.room_id).room_flags, RoomFlags.NO_RECALL):
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
        send_room_message(player.current_room, colourize(f"{player.name} arrives from the ether.\n", "green"), excluded_player=player)
    else:
        send_message(player, "Available commands are 'recall', 'recall set', 'recall show' and 'recall clear'\n")

def rest_command(player, argument):
    current_position = player.character.get_position()
    if current_position == "Rest":
        send_message(player, "You are already resting.\n")
        return
    
    if combat_manager.in_combat(player):
        send_message(player, "You are fighting someone!!\n")
        return
    
    player.character.set_position("Rest")
    send_room_message(player.current_room, colourize(f"{player.name} sits down and rests.\n", "green"), excluded_player=player, excluded_msg=colourize("You sit down and rest.\n", "green"))

def save_command(player, argument):
    player.save()
    send_message(player, colourize("Player saved.\n", "green"))

def say_command(player, argument):
    if argument == '':
        send_message(player, "Say what??\n")
        return
    
    if player.character.is_awake() == False:
        send_message(player, colourize("You mumble something in your sleep.\n", "green"))
        send_room_message(player.current_room, colourize(f"{player.name} mumbles something in their sleep.\n", "green"))
        return
    
    msg = colourize(f"{player.name} says '{argument}'\n", "yellow")
    excluded_msg = colourize(f"You say '{argument}'\n", "yellow")
    send_room_message(player.current_room, msg, excluded_player=player, excluded_msg=excluded_msg)

def scan_command(player, argument):
    if player.character.is_awake() == False:
        send_message(player, colourize(random.choice(mud_consts.LOOK_SLEEPING_MSGS) + "\n", "green"))
        return
    send_message(player, "You scan your surroundings...\n")
    scan_msg = player.current_room.scan(player)
    if scan_msg != '':
        send_message(player, scan_msg)
    else:
        send_message(player, "... and you don't see anything.\n")

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
  
def sleep_command(player, argument):
    current_position = player.character.get_position()
    if current_position == "Sleep":
        send_message(player, "You are already sleeping.\n")
        return
    
    if combat_manager.in_combat(player):
        send_message(player, "You are fighting someone!!\n")
        return
    
    send_room_message(player.current_room, colourize(f"{player.name} lies down and goes to sleep.\n", "green"), excluded_player=player, excluded_msg=colourize("You lie down and fall asleep.\n", "green"))
    player.character.set_position("Sleep")

def stand_command(player, argument):
    current_position = player.character.get_position()
    if current_position == "Stand":
        send_message(player, "You are already standing.\n")
        return
    
    player.character.set_position("Stand")
    send_room_message(player.current_room, colourize(f"{player.name} stands up, ready for adventure.\n", "green"), excluded_player=player, excluded_msg=colourize("You stand up.\n", "green"))
    
def study_command(player, argument):
    if argument == '':
        send_message(player, player.character.abilities.list_spells())
        return

    if player.character.is_awake() == False:
        send_message(player, colourize("You fumble groggily with the scroll, but your drowsy mind cannot comprehend the mystical runes. The words blur before your eyes as you drift back into the comforting embrace of sleep, the knowledge of the scroll remaining just out of reach in your slumbering state.\n", "green"))
        return
    
    object = search_items(player.get_objects(), argument.lower())
        
    if object is None:
        send_message(player, "No scroll or spellbook with that name found.\n")
        return

    
    if object.vnum in ScrollsAndSpellbooks:
        spell_name = ScrollsAndSpellbooks[object.vnum]
        if player.character.abilities.has_ability(spell_name):
            send_message(player, f"You already know the spell {spell_name}.\n")
            return
        else:
            study_msg = player.character.abilities.learn_ability(spell_name, AbilityType.SPELL) + "\n"
            send_message(player, colourize(study_msg, "bright magenta"))
            send_message(player, f"With a poof of smoke, {object.name} disappears!\n")
            object.imp()
            
            
    else:
        send_message(player, "You can't study that.\n")
        return 
    
def title_command(player, argument):
    if argument == '':
        send_message(player, "title usage: title <title>, title reset\n")
        return
    
    if argument.split()[0].lower() == 'reset':
        player.title = "the" + player.character.origin
        send_message(player, "Your title has been reset.\n")
        return
    
    if len(argument) > 50:
        send_message(player, "Your title cannot be longer than 50 characters.\n")
        return

    player.set_title(argument)
    send_message(player, f"Your title is now: {player.get_title()}\n")
       
def who_command(player, argument):
    send_message(player, colourize("Heroes...\n", "green"))
    send_message(player, colourize("---------\n", "green"))
    count = 0
    for other_player in player_manager.get_players():
        if other_player is None:
            log_error("Who: other_player is None")
            continue
        if other_player.loggedin == False:
            continue
        if other_player.character.race == '':
            log_error("Who: why are we here?")
            continue
        send_message(player, colourize(f"[{other_player.character.level : >4} {mud_consts.RACES_ABV[other_player.character.race]: <5}] {other_player.name} {other_player.get_title()}\n", "green"))
        count += 1
    send_message(player, colourize(f"\n{count} players online.\n", "green"))


def player_movement(player, direction):
    current_position = player.character.get_position()
    if current_position == "Sleep":
        send_message(player, "You dream of moving, unfortunately you're still lying in your bed.\n")
        return
    if current_position == "Rest":
        send_message(player, "You can't move while resting, best stand up first.\n")
        return
    if combat_manager.in_combat(player):
        send_message(player, "You are fighting someone!\n")
        return
    
    # todo: add private room check if functionality desired
    
    room_instance = player.current_room
    if room_instance is not None:
        if direction in room_instance.doors:
            if room_instance.doors[direction]["locks"] == 0:
                move_player(player, room_instance.vnum, room_instance.doors[direction]["to_room"], msg_to_room=colourize(f"{first_to_upper(player.name)} leaves to the {mud_consts.DIRECTIONS[direction]}.\n", "green"))
                send_room_message(room_manager.get(room_instance.doors[direction]["to_room"]) , colourize(f"{first_to_upper(player.name)} arrives from the {mud_consts.DIRECTIONS_REVERSE[direction]}.\n", "green"), excluded_player=player)
                for other_player in set(room_instance.get_players()):
                    if other_player.follow == player:
                        send_message(other_player, f"You follow {player.name} {mud_consts.DIRECTIONS[direction]}.\n")
                        player_movement(other_player, direction)                            
            else:
                send_message(player, "The door is locked.\n")
        else:
            send_message(player, "There is no exit that way.\n")

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
    
              

def test_command(player, argument):
    pass

commands = {
    'cast': [cast_command],
    'chat' : [chat_command],
    'cmds' : [cmds_command],
    'drop': [drop_command],
    'down': [down_command],
    'east': [east_command],
    'flee': [flee_command],
    'follow': [follow_command],
    'get': [get_command],
    'give': [give_command],
    'goto': [goto_command],
    'inventory' : [inventory_command],
    'kill': [kill_command],
    'last': [last_command],
    'look': [look_command],
    'motd': [lambda player, argument: send_message(player, read_motd() + "\n")],
    'north': [north_command],
    'quit': [quit_command],
    'recall': [recall_command],
    'rest': [rest_command],
    'save': [save_command],
    'say': [say_command],
    'scan': [scan_command],
    'score': [score_command],
    'sleep': [sleep_command],
    'socials': [list_socials],
    'south': [south_command],
    'stand': [stand_command],
    'study': [study_command],
    'test':[test_command],
    'title':[title_command],
    'up': [up_command],
    'wake': [stand_command],
    'west': [west_command],
    'who': [who_command],
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
        'i': 'inventory',
        'c': 'cast',
        'st': 'stand',
        'sc': 'score',
        'j': 'scan',
        'x': 'scan',
        
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
        return
    else:
        social_check = handle_social(player, command, argument)
        if social_check:
            return
        else:   
            send_message(player, "I'm sorry, I don't understand you.\n")
            return
        
def move_player(player, old_room_vnum, new_room_vnum, msg_to_room=None, msg_to_player=None):
    """move player from old_room to new_room, use room vnums"""
    current_position = player.character.get_position()
    if current_position == "Sleep" or current_position == "Rest":
        return

    send_room_message(room_manager.get(old_room_vnum), msg_to_room, excluded_player=player, excluded_msg=msg_to_player)
    player.move_to_room(room_manager.get(new_room_vnum))
    look_command(player, "")
    
    # check for aggie mob
    if player.character.NPC is not True:
        for mob in player.current_room.get_mobs():
            if player in mob.aggro_list and mob.current_room.flag(RoomFlags.SAFE) == False:
                send_message(player, colourize(f"\n{first_to_upper(mob.name)} glares and snarls!\n", "bright red"))
                kill_mob(mob, player)
    
    mprog_room_check(player)