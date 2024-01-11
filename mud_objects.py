# mud_objects.py

import sqlite3
import threading
import pickle
from datetime import datetime
import time
import random

from mud_shared import dice_roll, colourize, log_info, log_error, check_flag, first_to_upper
import mud_consts

# May want to consider if JSON is a better format for storing data
class PlayerDatabase:
    def __init__(self, db_name):
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.lock = threading.Lock()
        self.cursor = self.connection.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                name TEXT PRIMARY KEY,
                room_id TEXT,
                current_recall TEXT,
                created TEXT,
                lastlogin TEXT,
                title TEXT,
                character BLOB
            )
        ''')
        self.connection.commit()

    def save_player(self, player):
        with self.lock:
            character_data = pickle.dumps(player.character)
            self.cursor.execute('''
                INSERT OR REPLACE INTO players (name, room_id, current_recall, created, lastlogin, title, character)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (player.name, player.room_id, player.current_recall, player.created, player.lastlogin, player.title, character_data))
            self.connection.commit()

    def load_player(self, name):
        with self.lock:
            self.cursor.execute('''
            SELECT room_id, current_recall, created, lastlogin, title, character FROM players WHERE LOWER(name) = LOWER(?)
            ''', (name.lower(),))
            result = self.cursor.fetchone()
            if result is None:
                log_error(f"Error loading player data for {name}")
                return None
            else:
                room_id, current_recall, created, lastlogin, title, character_data = result
                character = pickle.loads(character_data)
                return {
                'name': name,
                'room_id': room_id,
                'current_recall': current_recall,
                'created': created,
                'lastlogin': lastlogin,
                'title': title,
                'character': character
                }
    
    def get_player_created_lastlogin(self, name):
        with self.lock:
            self.cursor.execute('''
                SELECT created, lastlogin FROM players WHERE LOWER(name) = LOWER(?)
            ''', (name.lower(),))
            result = self.cursor.fetchone()
            if result is None:
                return None
            else:
                created, lastlogin = result
                return datetime.strptime(created, '%Y-%m-%d %H:%M:%S.%f'), datetime.strptime(lastlogin, '%Y-%m-%d %H:%M:%S.%f')
    
player_db = PlayerDatabase('player_database.db')

class PlayerManager:
    def __init__(self):
        self.players = []

    def add_player(self, player):
        self.players.append(player)

    def remove_player(self, player):
        try:
            self.players.remove(player)
            return True
        except ValueError:
            return False
        
    def get_players(self):
        return self.players

    def get_player_by_name(self, name):
        for player in self.players:
            if player.name is None:
                continue
            if player.name.lower() == name.lower():
                return player
        return None
    
    def save_all_players(self):
        for player in self.players:
            player_db.save_player(player)

    def disconnect_player(self, player, msg=""):
        if msg:
            try:
                player.socket.send(msg.encode('utf-8'))
            except OSError:
                # The socket is already closed
                pass
        player.save()
            
        # Remove the player from the list of connected players
        return self.remove_player(player)



class Player:
    def __init__(self, fd):
        self.fd = fd
        self.socket = None
        self.loggedin = False
        self.reconnect_prompt = False
        self.awaiting_reconnect_confirmation = False
        self.awaiting_race = False
        self.awaiting_origin = False
        self.name = None
        self.room_id = 3001
        self.current_room = None
        self.current_recall = 0
        self.character = Character()
        
        self.created = datetime.now()
        self.lastlogin = datetime.now()
        self.title = ""

    def save(self):
        player_db.save_player(self)

    def load(self):
        player_data = player_db.load_player(self.name)
        if player_data is None:
            return False
        self.room_id = int(player_data['room_id'])
        self.set_room(room_manager.get_room_by_vnum(self.room_id))
        self.current_recall = int(player_data['current_recall'])
        self.created = player_data['created']
        self.lastlogin = datetime.now()
        self.title = player_data['title']
        self.character = player_data['character']
        return True
    
    def save_exists(self):
        return player_db.load_player(self.name) is not None

    def set_room(self, room):
        self.current_room = room

    def move_to_room(self, new_room):
        self.room_id = new_room.room_vnum
        if self.current_room is not None:
            self.current_room.remove_player(self)
        if new_room is not None:
            new_room.add_player(self)
            self.current_room = new_room
            
    def get_description(self):
        return self.name + " " + self.get_title()
    
    def get_title(self):
        if self.title == "":
            return f"the {self.character.origin}"
        return self.title
    
    def set_title(self, title):
        self.title = title
        
    def get_recall(self):
        return self.current_recall
    
    def set_recall(self, room=0):
        self.current_recall = room
        
    def get_prompt(self):
        return self.character.get_prompt()
    
    def get_hitroll(self):
        return self.character.hitroll
    
    def get_damroll(self):
        return 1, 4, (self.character.str - 10)
        # return self.character.damroll_dice, self.character.damroll_size, self.character.damroll_bonus
    
    def get_AC(self):
        return self.character.ac
    
        
class Character:
    def __init__(self, NPC=False):
        self.level = 1
        self.race = ""
        self.origin = ""
            
        self.NPC = NPC
        self.inventory = []
        self.equipment = Equipment()
        self.max_hitpoints = 30
        self.current_hitpoints = self.max_hitpoints
        self.max_mana = 100
        self.current_mana = self.max_mana
        self.max_stamina = 100
        self.current_stamina = self.max_stamina
        
        self.position = "Stand"
        
        self.combat_with = set()
        self.current_target = None
        
        self.str = 10
        self.dex = 10
        self.con = 10
        self.int = 10
        self.wis = 10
        self.cha = 10
        
        self.ac = 12
        self.hitroll = 2 
        
        self.xp = 0
        self.tnl = 1000
        self.gold = 0
        
        self.racials = []
        

    def get_prompt(self):
        c = colourize
        return c("\n<HP: ", "green") + c(f"{self.current_hitpoints}", "white") + c(f"/{self.max_hitpoints}", "green") + c(" MP: ", "green") + c(f"{self.current_mana}", "white") + c(f"/{self.max_mana}", "green") + c(" SP: ", "green") + c(f"{self.current_stamina}", "white") + c(f"/{self.max_stamina}", "green") + c(f" {self.tnl-self.xp}", "yellow") + c("> \n", "green")

    def set_racial_stats(self, str, dex, con, int, wis, cha, tnl, racials):
        self.str = str
        self.dex = dex
        self.con = con
        self.int = int
        self.wis = wis
        self.cha = cha
        self.tnl = tnl
        self.racials = racials
          
    def get_hitroll(self):
        return self.hitroll + self.dex - 10
    
    def get_AC(self):
        return self.ac + self.dex - 10
    
    def get_damroll(self):
        return 1, 4, (self.str - 10)
    
    def get_hp_pct(self):
        return (self.current_hitpoints / self.max_hitpoints)
    
    def apply_damage(self, damage):
        self.current_hitpoints -= damage
        
    def is_dead(self):
        return self.current_hitpoints <= 0
    
    def is_awake(self):
        return self.position != "Sleep"
    
    def get_position(self):
        return self.position
    
    def set_position(self, position):
        if position in ["Stand", "Rest", "Sleep"]:
            self.position = position
        else:
            log_error(f"Invalid position {position}")
    
    def gain_experience(self, xp):
        msg = ""
        self.xp += xp
        if self.xp >= self.tnl:
            while self.xp >= self.tnl:
                self.xp -= self.tnl
                msg += f"You have gained a level!!!\n"
                msg += self.level_up()      
        return msg
            
    def level_up(self):
        self.level += 1
        hp_gain = dice_roll(2, 5, self.con - 10)
        self.max_hitpoints += hp_gain
        self.current_hitpoints = self.max_hitpoints
        mana_gain = dice_roll(1, 10, self.int - 10)
        self.max_mana += mana_gain
        self.current_mana = self.max_mana
        # self.max_stamina += dice_roll(1, 10, self.str - 10)
        self.current_stamina = self.max_stamina
        return f"You have gained {hp_gain} hitpoints and {mana_gain} mana!\n"
    
    def regen_hp(self, amount):
        amount = round(amount)
        self.current_hitpoints = min(self.max_hitpoints, self.current_hitpoints + amount)
        
    def regen_mana(self, amount):
        amount = round(amount)
        self.current_mana = min(self.max_mana, self.current_mana + amount)
        
    def regen_stamina(self, amount):
        amount = round(amount)
        self.current_stamina = min(self.max_stamina, self.current_stamina + amount)
        
    def tick(self):
        # update spell lengths
        
        REGEN_HP_RATE = self.max_hitpoints / 4
        REGEN_MANA_RATE = self.max_mana / 4
        REGEN_STAMINA_RATE = self.max_stamina
        
        if self.position == "Sleep":
            self.regen_hp(REGEN_HP_RATE)
            self.regen_mana(REGEN_MANA_RATE)
            self.regen_stamina(REGEN_STAMINA_RATE)
        elif self.position == "Rest":
            self.regen_hp(REGEN_HP_RATE/2)
            self.regen_mana(REGEN_MANA_RATE/2)
            self.regen_stamina(REGEN_STAMINA_RATE/2)
        else:
            self.regen_hp(REGEN_HP_RATE/10)
            self.regen_mana(REGEN_MANA_RATE/10)
            self.regen_stamina(REGEN_STAMINA_RATE/4)

    # for debugging
    def __str__(self):
        str = f"Level: {self.level}, Race: {self.race}, Origin: {self.origin}\n"
        str += f"Str: {self.str}, Dex: {self.dex}, Con: {self.con}, Int: {self.int}, Wis: {self.wis}, Cha: {self.cha}\n"
        str += f"Hitroll: {self.hitroll}, AC: {self.ac}"
        str += self.get_prompt()
        return str
        
class Equipment:
    def __init__(self):
        self.slots = {
            "light": None,
            "ring_left": None,
            "ring_right": None,
            "neck_one": None,
            "neck_two": None,
            "body": None,
            "head": None,
            "legs": None,
            "feet": None,
            "hands": None,
            "arms": None,
            "off_hand": None,
            "about_body": None,
            "waist": None,
            "wrist_left": None,
            "wrist_right": None,
            "main_hand": None,
            "held": None,            
        }

    # placeholder methods for now
    def equip(self, slot, item):
        if slot in self.slots and self.slots[slot] is None:
            self.slots[slot] = item
        else:
            raise ValueError(f"Cannot equip {item} to {slot}")

    def unequip(self, slot):
        if slot in self.slots and self.slots[slot] is not None:
            item = self.slots[slot]
            self.slots[slot] = None
            return item
        else:
            raise ValueError(f"Cannot unequip from {slot}")
        
    def get_equipped_items(self):
        return [item for item in self.slots.values() if item is not None]
    
    def get_string_equipped_items(self):
        if self.get_equipped_items():
            msg = ""
            for item in self.get_equipped_items():
                msg += colourize(f"{mud_consts.EQ_SLOTS[int(item.template.wear_flags)]: <20}{item.template.short_description}\n", "yellow")
            return msg
        else:
            return None

# Note: managers are for managing the base templates, not the instances

class MobManager:
    def __init__(self):
        self.mob_templates = {}
        
    def add_mob_template(self, mob):
        self.mob_templates[mob.vnum] = mob

    def get_mob_template(self, vnum):
        return self.mob_templates.get(vnum)

    def remove_mob_template(self, vnum):
        if vnum in self.mob_templates:
            del self.mob_templates[vnum]

    def get_all_mob_templates(self):
        return self.mob_templates.values()
        
class ObjectManager:
    def __init__(self):
        self.objects = {}
        
    def add_object(self, obj):
        self.objects[obj.vnum] = obj

    def get_object(self, vnum):
        return self.objects.get(vnum)

    def remove_object(self, vnum):
        if vnum in self.objects:
            del self.objects[vnum]

    def get_all_objects(self):
        return self.objects.values()
        
class RoomManager:
    def __init__(self):
        self.rooms = {}
    
    def add_room(self, room):
        self.rooms[room.room_vnum] = room
        
    def get_room_by_vnum(self, room_vnum):
        ''' Returns a room object by its room_vnum, otherwise returns None'''
        return self.rooms.get(room_vnum)

    def remove_room(self, room_vnum):
        if room_vnum in self.rooms:
            del self.rooms[room_vnum]

    def get_all_rooms(self):
        return self.rooms.values()

    def get_rooms_by_attribute(self, attribute_name, value):
        return [room for room in self.rooms.values() if getattr(room, attribute_name, None) == value]

class MobTemplate:
    def __init__(self, vnum, keywords, short_desc, long_desc, desc, act_flags, aff_flags, align, level, hitroll, ac, hitdice_num, hitdice_size, hitdice_bonus, damdice_num, damdice_size, damdice_bonus, gold, xp, sex):
        self.vnum = vnum
        self.keywords = keywords
        self.short_desc = short_desc
        self.long_desc = long_desc
        self.desc = desc
        self.act_flags = act_flags
        self.aff_flags = aff_flags
        self.align = align
        self.level = level
        self.hitroll = hitroll
        self.ac = ac
        self.hitdice_num = hitdice_num
        self.hitdice_size = hitdice_size
        self.hitdice_bonus = hitdice_bonus
        self.damdice_num = damdice_num
        self.damdice_size = damdice_size
        self.damdice_bonus = damdice_bonus
        self.gold = gold
        self.xp = xp
        self.sex = sex
        self.speed = 3
        
    def check_if_move(self):
        if check_flag(self.act_flags, mud_consts.ACT_SENTINEL):
            return False # Sentinel mobs don't move
        
        if random.uniform(0, 1) < (0.01 * self.speed):
            return True

        return False
        
class ObjectTemplate:
    def __init__(self, vnum):
        self.vnum = vnum
        self.keywords = ""
        self.short_description = ""
        self.long_description = ""
        # Not used: self.action_description = ""
        self.item_type = 0
        self.extra_flags = 0
        self.wear_flags = 0
        self.value_0 = 0
        self.value_1 = 0
        self.value_2 = 0
        self.value_3 = 0
        self.weight = 0
        self.cost = 0
        # Note used: self.cost_per_day = 0
        # E and A are not used for now
    

        
class Room:
    def __init__(self, room_vnum):
        self.room_vnum = room_vnum
        self.name = ""
        self.description = ""
        self.area_number = 0
        self.room_flags = 0
        self.sector_type = 0
        self.cursed = False
        
        self.doors = {}
        self.extended_descriptions = []
    
        self.mob_list = set()
        self.object_list = set()
        self.player_list = set()

    def add_door(self, door_number, door_description, keywords, locks, key, to_room):
        self.doors[door_number] = {
            "description": door_description,
            "keywords": keywords,
            "locks": locks,
            "key": key,
            "to_room": to_room
        }

    def add_extended_description(self, keywords, description):
        self.extended_descriptions.append({
            "keywords": keywords,
            "description": description
        })
        
    def add_player(self, player):
        self.player_list.add(player)
        
    def remove_player(self, player):
        self.player_list.discard(player)
        
    def add_mob(self, mob):
        self.mob_list.add(mob)
        
    def remove_mob(self, mob):
        self.mob_list.discard(mob)
        
    def add_object(self, obj):
        self.object_list.add(obj)
        
    def remove_object(self, obj):
        self.object_list.discard(obj)
        
    def get_exit_names(self):
        exit_names = ["north", "east", "south", "west", "up", "down"]
        available_exits = []
        
        for i in range(len(exit_names)):
            if i in self.doors:
                if self.doors[i]["locks"] == 0:
                    available_exits.append(exit_names[i])
                else:
                    available_exits.append(exit_names[i] + " (locked)")
        
        available_exits_str = ', '.join(available_exits)
        return available_exits_str
    
    def choose_random_door(self, exclude_other_area=True):
        available_doors = []
        for door in self.doors:
            if exclude_other_area and room_manager.get_room_by_vnum(self.doors[door]["to_room"]).area_number != self.area_number:
                continue
            if self.doors[door]["locks"] == 0:
                available_doors.append(door)
        if available_doors:
            return random.choice(available_doors)
        else:
            return None
    
    def get_players(self):
        return self.player_list
    
    def get_mobs(self):
        return self.mob_list
    
    def get_player_names(self, excluded_player=None):
        player_names = []
        for player in self.player_list:
            if player != excluded_player:
                position_str = "."
                if player.character.position == "Sleep":
                    position_str = " is sleeping here."
                elif player.character.position == "Rest":
                    position_str = " is resting here."
                player_names.append((player.name, player.get_title() + position_str))
        if not player_names:  # Check if the list is empty
            return ""
        else:
            ret_str = '\n'.join(f'{name} {title}' for name, title in player_names) + '\n'
            return colourize(ret_str, "cyan")
    
    def get_mob_names(self):
        mob_names = [mob.template.long_desc for mob in self.mob_list]
        if not mob_names:  # Check if the list is empty
            return ""
        else:
            ret_str = ''.join(name for name in mob_names)
            return colourize(ret_str, "cyan")
        
    def get_object_names(self):
        object_names = [obj.template.short_description for obj in self.object_list]
        if not object_names:  # Check if the list is empty
            return ""
        else:
            return '\n'.join('\t' + first_to_upper(name) for name in object_names) + '\n'
    
    def process_keyword(self, keyword):
        keyword = keyword.lower()
        # Split the keyword into number and actual keyword if applicable
        number, keyword = (keyword.split('.', 1) + [None])[:2] if '.' in keyword else (None, keyword)
        number = int(number) - 1 if number is not None and number.isdigit() else None
        return keyword, number
    
    def process_search_output(self, number, matches):
        if number is None and matches:
            return matches[0]
        elif number is not None and number < len(matches):
            return matches[number]
        else:
            return None
    
    def search_mobs(self, keyword):
        keyword, number = self.process_keyword(keyword)
        matches = [mob for mob in self.mob_list if any(kw.startswith(keyword) for kw in mob.template.keywords.split())]
        return self.process_search_output(number, matches)
    
    def search_players(self, keyword):
        keyword, number = self.process_keyword(keyword)
        matches = [player for player in self.player_list if player.name.lower().startswith(keyword)]
        return self.process_search_output(number, matches)
    
    def search_objects(self, keyword):
        keyword, number = self.process_keyword(keyword)
        matches = [obj for obj in self.object_list if any(kw.startswith(keyword) for kw in obj.template.keywords.split())]
        return self.process_search_output(number, matches)

    def search_doors(self, keyword):
        keyword, number = self.process_keyword(keyword)
        matches = [door for door in self.doors if any(kw.startswith(keyword) for kw in self.doors[door]["keywords"].split())]
        return self.process_search_output(number, matches)
    
    def search_extended_descriptions(self, keyword):
        keyword, number = self.process_keyword(keyword)
        matches = [extended_description for extended_description in self.extended_descriptions if any(kw.startswith(keyword) for kw in extended_description["keywords"].split())]
        return self.process_search_output(number, matches)
    


class ResetMob:
    def __init__(self, mob_vnum, max_count, room_vnum, comment=""):
        self.mob_vnum = mob_vnum
        self.max_count = max_count
        self.room_vnum = room_vnum
        self.comment = comment
        
        self.equipment = Equipment()
        self.inventory = []
        
    def add_item(self, item):
        self.inventory.append(item)
        
class ResetObject:
    def __init__(self, obj_vnum, room_vnum):
        self.obj_vnum = obj_vnum
        self.room_vnum = room_vnum

class Resets:
    def __init__(self):
        self.mob_resets = []
        self.object_resets = []
        self.door_resets = []
        self.randomize_doors_resets = []
        
    def add_mob_reset(self, ResetMob):
        self.mob_resets.append(ResetMob)
        
    def add_object_reset(self, ResetObject):
        self.object_resets.append(ResetObject)

class MobInstanceManager:
    def __init__(self):
        self.mob_instances = {} # vnum: [mob_instance1, mob_instance2, ...]
    
    def add_mob_instance(self, mob_instance):
        if mob_instance.template.vnum not in self.mob_instances:
            self.mob_instances[mob_instance.template.vnum] = []
        self.mob_instances[mob_instance.template.vnum].append(mob_instance)

    def remove_mob_instance(self, mob_instance):
        if mob_instance.template.vnum in self.mob_instances:
            self.mob_instances[mob_instance.template.vnum].remove(mob_instance)
            if not self.mob_instances[mob_instance.template.vnum]:
                del self.mob_instances[mob_instance.template.vnum]

    def get_all_instances_by_vnum(self, vnum):
        return self.mob_instances.get(vnum, [])

    def get_instance_by_vnum(self, vnum, index):
        return self.mob_instances.get(vnum, [None])[index]
    
    def get_all_instances(self):
        return [mob for mob_list in self.mob_instances.values() for mob in mob_list]

class MobInstance:
    def __init__(self, template):
        self.template = template
        self.name = self.template.short_desc
        self.current_room = None
        
        self.max_hitpoints = dice_roll(template.hitdice_num, template.hitdice_size, template.hitdice_bonus)
        self.current_hitpoints = self.max_hitpoints
        self.max_mana = 100
        self.current_mana = self.max_mana
        
        self.character = Character(NPC=True)
        
        # todo move equipment and inventory to character
        self.equipment = Equipment()
        self.inventory = []
        
        self.aggro_list = []

    def set_room(self, room):
        self.current_room = room

    def move_to_room(self, new_room):
        if self.current_room is not None:
            self.current_room.remove_mob(self)
        if new_room is not None:
            new_room.add_mob(self)
            self.current_room = new_room
        
    def get_description(self):
        description = []
        description.append(self.template.desc)
        equipped = self.equipment.get_string_equipped_items()
        if equipped:
            description.append("They are wearing:")
            description.append(equipped)
        if self.inventory:
            description.append("You peek into their inventory and see:")
            for item in self.inventory:
                description.append(f"\t{item.template.short_description}")
        
        return "\n".join(description)
        
    def add_item(self, item):
        self.inventory.append(item)
        
    def get_hitroll(self):
        return self.template.hitroll
    
    def get_AC(self):
        return self.template.ac
    
    def get_damroll(self):
        return self.template.damdice_num, self.template.damdice_size, self.template.damdice_bonus
        
        
class ObjectInstanceManager:
    def __init__(self):
        self.object_instances = {} # vnum: [object_instance1, object_instance2, ...]

    def add_object_instance(self, object_instance):
        if object_instance.vnum not in self.object_instances:
            self.object_instances[object_instance.vnum] = []
        self.object_instances[object_instance.vnum].append(object_instance)

    def remove_object_instance(self, object_instance):
        if object_instance.vnum in self.object_instances:
            self.object_instances[object_instance.vnum].remove(object_instance)
            if not self.object_instances[object_instance.vnum]:
                del self.object_instances[object_instance.vnum]

    def get_all_instances_by_vnum(self, vnum):
        return self.object_instances.get(vnum, [])

    def get_instance_by_vnum(self, vnum, index):
        return self.object_instances.get(vnum, [None])[index]
    
    def get_all_instances(self):
        return [obj for obj_list in self.object_instances.values() for obj in obj_list]

# need to set up methods for room and mobs
class ObjectInstance:
    def __init__(self, template):
        self.template = template
        self.vnum = template.vnum
        self.current_room = None

    def set_room(self, room):
        self.current_room = room

    def move_to_room(self, new_room):
        if self.current_room is not None:
            self.current_room.remove_object(self)
        new_room.add_object(self)
        self.current_room = new_room
        
    def get_description(self):
        description = []
        description.append(self.template.long_description)
        return "\n".join(description)  

class CombatManager:
    def __init__(self):
        self.combat_dict = {}
        self.current_target = {}
        self.last_update = time.time()

    def start_combat(self, character, target):
        if character not in self.combat_dict:
            self.combat_dict[character] = set()
        self.combat_dict[character].add(target)
        if character not in self.current_target:
            self.current_target[character] = target

    def end_combat(self, character, target):
        if character in self.combat_dict:
            self.combat_dict[character].discard(target)
            if not self.combat_dict[character]:
                del self.combat_dict[character]
        if character in self.current_target and self.current_target[character] == target:
            del self.current_target[character]

    def is_in_combat_with(self, character, target):
        return character in self.combat_dict and target in self.combat_dict[character]

    def get_combat_targets(self, character):
        return self.combat_dict.get(character, set())

    def in_combat(self, character):
        return character in self.combat_dict and len(self.combat_dict[character]) > 0

    def end_all_combat(self, character):
        if character in self.combat_dict:
            self.combat_dict[character] = set()
        if character in self.current_target:
            del self.current_target[character]

    def get_current_target(self, character):
        return self.current_target.get(character)
    
    def get_characters_in_combat(self):
        return list(self.combat_dict.keys())
    
    def next_round(self):
        ROUNDS_IN_MILLISECONDS = 2000
        elapsed_time_ms = (time.time() - self.last_update) * 1000
        if elapsed_time_ms > ROUNDS_IN_MILLISECONDS:
            self.last_update = time.time()
            return True
        else:
            return False



room_manager = RoomManager()
mob_manager = MobManager()
reset_manager = Resets()
object_manager = ObjectManager()

mob_instance_manager = MobInstanceManager()
object_instance_manager = ObjectInstanceManager()

combat_manager = CombatManager()