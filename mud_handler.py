# mud_handler.py
from datetime import datetime

import mud_consts
from mud_comms import send_message, send_room_message, player_manager, handle_disconnection
from mud_shared import colourize, is_NPC, report_mob_health, first_to_upper, log_error

from mud_world import room_manager
from mud_objects import player_db, combat_manager
from mud_combat import test_kill_mob, attempt_flee
from mud_spells import do_cast

def kill_command(player, argument):
    if argument == '':
        send_message(player, "You must specify a mob name.\n")
        return
    
    current_position = player.character.get_position()
    if current_position != "Stand":
        send_message(player, "You need to be standing first!\n")
        return 
    
    mob = player.current_room.search_mobs(argument)

    if mob is None:
        send_message(player, "No mob with that name found.\n")
    else:
        test_kill_mob(player, mob)

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

def cast_command(player, argument):
    do_cast(player)
    
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

def inventory_command(player, argument):
    send_message(player, player.get_inventory_description())

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

def drop_object(player, object):
    # if object.is_droppable() == False:
    # etc
    
    object.drop(player)
    send_message(player, f"You drop {object.name}.\n")
    send_room_message(player.current_room, f"{player.name} drops {object.name}.\n", excluded_player=player)


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
    
    player_in_room = player.current_room.search_players(argument[1])
    mob_in_room = player.current_room.search_mobs(argument[1])
    
    if player_in_room is None and mob_in_room is None:
        send_message(player, "There's no one here with that name.\n")
        return
    
    object = player.search_objects(argument[0])
        
    if object is None:
        send_message(player, "No item with that name found.\n")
        return
    
    if player_in_room:
        send_message(player, f"You give {object.name} to {player_in_room.name}.\n")
        send_message(player_in_room, f"{player.name} gives you {object.name}.\n")
        send_room_message(player.current_room, f"{player.name} gives {object.name} to {player_in_room.name}.\n", excluded_player=[player, player_in_room])
        object.give(player, player_in_room)
    elif mob_in_room:
        send_message(player, f"You give {object.name} to {mob_in_room.name}.\n")
        send_room_message(player.current_room, f"{player.name} gives {object.name} to {mob_in_room.name}.\n", excluded_player=player)
        object.give(player, mob_in_room)


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

        object = player.current_room.search_objects(argument)
        
        if object is None:
            send_message(player, "No item with that name found.\n")
            return
        
        get_object(player, object)
        
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
        for object in list(player.inventory_list.values())[::-1]:
            print(object)
            drop_object(player, object)
        return
    
    object = player.search_objects(argument)
    
    if object is None:
        send_message(player, "No object with that name found.\n")
        return
    
    drop_object(player, object)

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

def save_command(player, argument):
    player.save()
    send_message(player, colourize("Player saved.\n", "green"))

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
        send_room_message(player.current_room, colourize(f"{player.name} arrives from the ether.\n", "green"), excluded_player=player)
    else:
        send_message(player, "Available commands are 'recall', 'recall set', 'recall show' and 'recall clear'\n")

def look_command(player, argument):
    if is_NPC(player):
        return
    
    if player.character.is_awake() == False:
        send_message(player, "You see 42 sheep dancing in your dreams.\n")
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
        # bug: 2. only works within a group (ie will look at second mob but won't look at second object if one in room and one in inventory)) 
        
        mob = room.search_mobs(argument)
        if mob is not None:
            send_message(player, f"{mob.get_description()}\n")
            send_message(player, report_mob_health(mob))
            return
        
        object = room.search_objects(argument) 
        if object is not None:
            send_message(player, f"{object.get_description()}\n")
            return
        
        players_in_room = room.search_players(argument)
        if players_in_room is not None:
            send_message(player, f"{players_in_room.get_description()}\n")
            return
        
        door = room.search_doors(argument)
        if door is not None:
            send_message(player, f"{room.doors[door]["description"]}\n")
            return
        
        extended_description = room.search_extended_descriptions(argument)
        if extended_description is not None:
            send_message(player, f"{extended_description["description"]}\n")
            return
        
        inventory = player.search_objects(argument)
        if inventory is not None:
            send_message(player, f"{inventory.get_description()}\n")
            return
        
        send_message(player, colourize("You don't see that here.\n", "green"))     

def scan_command(player, argument):
    scan_msg = player.current_room.scan(player)
    print(scan_msg)
    if scan_msg != '':
        send_message(player, scan_msg)


def motd_command(player, argument):
    send_message(player, mud_consts.MOTD)

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
                send_room_message(room_manager.get_room_by_vnum(room_instance.doors[direction]["to_room"]) , colourize(f"{first_to_upper(player.name)} arrives from the {mud_consts.DIRECTIONS_REVERSE[direction]}.\n", "green"), excluded_player=player)
            else:
                send_message(player, "The door is locked.\n")
        else:
            send_message(player, "There is no exit that way.\n")
            
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

def test_command(player, argument):
    send_message(player, "Test command.\n")
    if argument == '':
        return
    mob = player.current_room.search_mobs(argument)
    if mob is None:
        send_message(player, "No mob with that name found.\n")
    else:
        send_message(player, f"Mob found: {mob.name}\n")
                 


commands = {
    'kill': [kill_command],
    'flee': [flee_command],
    'cast': [cast_command],
    'stand': [stand_command],
    'wake': [stand_command],
    'rest': [rest_command],
    'sleep': [sleep_command],
    'inventory' : [inventory_command],
    'give': [give_command],
    'get': [get_command],
    'drop': [drop_command],
    'say': [say_command],
    'chat' : [chat_command],
    'who': [who_command],
    'title':[title_command],
    'last': [last_command],
    'score': [score_command],
    'recall': [recall_command],
    'quit': [quit_command],
    'save': [save_command],
    'look': [look_command],
    'scan': [scan_command],
    'motd': [motd_command],
    'north': [north_command],
    'east': [east_command],
    'south': [south_command],
    'west': [west_command],
    'up': [up_command],
    'down': [down_command],
    'goto': [goto_command],
    'cmds' : [cmds_command],
    'test' : [test_command],
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
        'j': 'scan',
        'x': 'scan'
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
        
        
        
def move_player(player, old_room_vnum, new_room_vnum, msg_to_room=None, msg_to_player=None):
    """move player from old_room to new_room, use room vnums"""
    send_room_message(room_manager.get_room_by_vnum(old_room_vnum), msg_to_room, excluded_player=player, excluded_msg=msg_to_player)
    player.move_to_room(room_manager.get_room_by_vnum(new_room_vnum))
    look_command(player, "")