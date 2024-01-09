# mud_objects.py

import sqlite3
import threading
import pickle
from datetime import datetime

from mud_shared import dice_roll, colourize, log_info, log_error
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
                current_room TEXT,
                current_recall TEXT,
                character BLOB
            )
        ''')
        self.connection.commit()

    def save_player(self, player):
        with self.lock:
            character_data = pickle.dumps(player.character)
            self.cursor.execute('''
                INSERT OR REPLACE INTO players (name, current_room, current_recall, character)
                VALUES (?, ?, ?, ?)
            ''', (player.name.lower(), player.current_room, player.current_recall, character_data))
            self.connection.commit()

    def load_player(self, name):
        with self.lock:
            self.cursor.execute('''
                SELECT current_room, current_recall, character FROM players WHERE name = ?
            ''', (name.lower(),))
            result = self.cursor.fetchone()
            if result is None:
                log_error(f"Error loading player data for {name}")
                return None
            current_room, current_recall, character_data = result
            character = pickle.loads(character_data)
            return {'name': name, 'current_room': current_room, 'current_recall': current_recall, 'character': character}

    def get_last_login(self, name):
        with self.lock:
            self.cursor.execute('''
                SELECT character FROM players WHERE name = ?
            ''', (name.lower(),))
            result = self.cursor.fetchone()
            if result is None:
                return None
            character_data = result[0]
            character = pickle.loads(character_data)
            return character.lastlogin
    
    
player_db = PlayerDatabase('player_database.db')

class PlayerManager:
    def __init__(self):
        self.players = []

    def add_player(self, player):
        self.players.append(player)

    def remove_player(self, player):
        try:
            self.players.remove(player)
        except ValueError:
            pass
        
    def get_players(self):
        return self.players

    def get_player_by_name(self, name):
        for player in self.players:
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
        self.remove_player(player)



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
        self.current_room = 3001
        self.current_recall = 0
        self.character = PlayerCharacter()

    def save(self):
        player_db.save_player(self)

    def load(self):
        player_data = player_db.load_player(self.name)
        if player_data is None:
            return False
        self.current_room = int(player_data['current_room'])
        self.current_recall = int(player_data['current_recall'])
        self.character = player_data['character']
        self.character.lastlogin = datetime.now()
        return True
    
    def save_exists(self):
        return player_db.load_player(self.name) is not None

    def move_to_room(self, room):
        self.current_room = room
        
    def get_recall(self):
        return self.current_recall
    
    def set_recall(self, room=0):
        self.current_recall = room
        
    def get_prompt(self):
        return self.character.get_prompt()
        
class PlayerCharacter:
    def __init__(self):
        self.level = 1
        self.race = ""
        self.origin = ""    
        
        self.inventory = []
        self.equipment = Equipment()
        self.max_hitpoints = 30
        self.current_hitpoints = self.max_hitpoints
        self.max_mana = 100
        self.current_mana = self.max_mana
        self.max_stamina = 100
        self.current_stamina = self.max_stamina
        
        self.str = 0
        self.dex = 0
        self.con = 0
        self.int = 0
        self.wis = 0
        self.cha = 0
        
        self.xp = 0
        self.tnl = 1000
        self.gold = 0
        
        self.racials = []
        
        
        self.created = datetime.now()
        self.lastlogin = datetime.now()
        
    def get_prompt(self):
        c = colourize
        return c("\n<HP: ", "green") + c(f"{self.current_hitpoints}", "white") + c(f"/{self.max_hitpoints}", "green") + c(" MP: ", "green") + c(f"{self.current_mana}", "white") + c(f"/{self.max_mana}", "green") + c(" SP: ", "green") + c(f"{self.current_stamina}", "white") + c(f"/{self.max_stamina}", "green") + c("> \n", "green")

    def set_racial_stats(self, str, dex, con, int, wis, cha, tnl, racials):
        self.str = str
        self.dex = dex
        self.con = con
        self.int = int
        self.wis = wis
        self.cha = cha
        self.tnl = tnl
        self.racials = racials
        

        
        
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
                msg += colourize(f"<{mud_consts.EQ_SLOTS[int(item.template.wear_flags)] + ">": <20}{item.template.short_description}\n", "yellow")
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
        
        self.mobs = []
        self.players = []
        self.objects = []
    
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
        
    def get_exit_names(self):
        exit_names = ["North", "East", "South", "West", "Up", "Down"]
        available_exits = []
        
        for i in range(len(exit_names)):
            if i in self.doors:
                if self.doors[i]["locks"] == 0:
                    available_exits.append(exit_names[i])
                else:
                    available_exits.append(exit_names[i] + " (locked)")
        
        available_exits_str = ', '.join(available_exits)
        return available_exits_str
    
    def get_players(self):
        return self.player_list
    
    def get_player_names(self, excluding_player=None):
        player_names = []
        for player in self.player_list:
            if player != excluding_player:
                player_names.append(player.name)
        return player_names
    
    def get_mob_names(self):
        mob_names = []
        for mob in self.mob_list:
            mob_names.append(mob.template.long_desc)
        mob_names_str = ''.join('\t' + name for name in mob_names)
        return mob_names_str
    
    def get_mob_keywords(self):
        mob_keywords = []
        for mob in self.mob_list:
            mob_keywords.append(mob.template.keywords)
        return mob_keywords
    
    def get_mob_description_by_keyword(self, keyword):
        for mob in self.mob_list:
            if keyword in mob.template.keywords:
                return mob.get_description()
        return None
    
    def get_door_keywords(self):
        door_keywords = []
        for door in self.doors:
            door_keywords.append(self.doors[door]["keywords"])
        return door_keywords
    
    def get_door_description_by_keyword(self, keyword):
        for door in self.doors:
            if keyword in self.doors[door]["keywords"]:
                return self.doors[door]["description"]
        return None
    
    def get_extended__description_keywords(self):
        extended_keywords = []
        for extended_description in self.extended_descriptions:
            extended_keywords.append(extended_description["keywords"])
        return extended_keywords
    
    def get_extended_description_by_keyword(self, keyword):
        for extended_description in self.extended_descriptions:
            if keyword in extended_description["keywords"]:
                return extended_description["description"]
        return None


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
        


class Resets:
    def __init__(self):
        self.mob_resets = []
        self.object_resets = []
        self.door_resets = []
        self.randomize_doors_resets = []
        
    def add_mob_reset(self, ResetMob):
        self.mob_resets.append(ResetMob)

class MobInstanceManager:
    def __init__(self):
        self.mob_instances = {}
    
    def add_mob_instance(self, mob_instance):
        if mob_instance.template.vnum not in self.mob_instances:
            self.mob_instances[mob_instance.template.vnum] = []
        self.mob_instances[mob_instance.template.vnum].append(mob_instance)

    def remove_mob_instance(self, mob_instance):
        if mob_instance.template.vnum in self.mob_instances:
            self.mob_instances[mob_instance.template.vnum].remove(mob_instance)
            if not self.mob_instances[mob_instance.template.vnum]:
                del self.mob_instances[mob_instance.template.vnum]

    def get_all_instances(self, vnum):
        return self.mob_instances.get(vnum, [])

    def get_instance(self, vnum, index):
        return self.mob_instances.get(vnum, [None])[index]

class MobInstance:
    def __init__(self, template):
        self.template = template
        self.current_room = None
        
        self.max_hitpoints = dice_roll(template.hitdice_num, template.hitdice_size, template.hitdice_bonus)
        self.current_hitpoints = self.max_hitpoints
        self.max_mana = 100
        self.current_mana = self.max_mana
        
        
        self.equipment = Equipment()
        self.inventory = []
        
        self.aggro_list = []

    def set_room(self, room):
        self.current_room = room

    def move_to_room(self, new_room):
        if self.current_room is not None:
            self.current_room.remove_mob(self)
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
                description.append(f"\t{item.name}")
        
        return "\n".join(description)
        
    def add_item(self, item):
        self.inventory.append(item)
        
        
class ObjectInstanceManager:
    def __init__(self):
        self.object_instances = {}

    def add_object_instance(self, object_instance):
        if object_instance.vnum not in self.object_instances:
            self.object_instances[object_instance.vnum] = []
        self.object_instances[object_instance.vnum].append(object_instance)

    def remove_object_instance(self, object_instance):
        if object_instance.vnum in self.object_instances:
            self.object_instances[object_instance.vnum].remove(object_instance)
            if not self.object_instances[object_instance.vnum]:
                del self.object_instances[object_instance.vnum]

    def get_all_instances(self, vnum):
        return self.object_instances.get(vnum, [])

    def get_instance(self, vnum, index):
        return self.object_instances.get(vnum, [None])[index]

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
        