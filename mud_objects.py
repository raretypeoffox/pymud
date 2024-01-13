# mud_objects.py

import sqlite3
import threading
import pickle
from datetime import datetime
import time
import random
import uuid
import json

from mud_shared import dice_roll, colourize, log_info, log_error, check_flag, first_to_upper, process_keyword, process_search_output
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
                inventory TEXT,
                character BLOB
            )
        ''')
        self.connection.commit()

    def save_player(self, player):
        with self.lock:
            character_data = pickle.dumps(player.character)
            inventory = [str(i) for i in player.inventory]
            self.cursor.execute('''
                INSERT OR REPLACE INTO players (name, room_id, current_recall, created, lastlogin, title, inventory, character)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (player.name, player.room_id, player.current_recall, player.created, player.lastlogin, player.title, json.dumps(inventory), character_data))
            self.connection.commit()

    def load_player(self, name):
        with self.lock:
            self.cursor.execute('''
            SELECT room_id, current_recall, created, lastlogin, title, inventory, character FROM players WHERE LOWER(name) = LOWER(?)
            ''', (name.lower(),))
            result = self.cursor.fetchone()
            if result is None:
                log_error(f"Error loading player data for {name}")
                return None
            else:
                room_id, current_recall, created, lastlogin, title, inventory, character_data = result
                inventory = set(uuid.UUID(i) for i in json.loads(inventory))
                character = pickle.loads(character_data)
                return {
                'name': name,
                'room_id': room_id,
                'current_recall': current_recall,
                'created': created,
                'lastlogin': lastlogin,
                'title': title,
                'inventory' : inventory,
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

class ObjectDatabase:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                uuid TEXT PRIMARY KEY,
                vnum INTEGER,
                name TEXT,
                description TEXT,
                action_description TEXT,
                state INTEGER,
                insured TEXT,
                location TEXT,
                location_type TEXT,
                max_hitpoints INTEGER,
                current_hitpoints INTEGER,
                enchantments TEXT
            )
        """)

    def save_object(self, obj):
        self.cursor.execute("""
            INSERT OR REPLACE INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(obj.uuid),
            obj.vnum,
            obj.name,
            obj.description,
            obj.action_description,
            obj.state,
            obj.insured,
            obj.location,
            obj.location_type,
            obj.max_hitpoints,
            obj.current_hitpoints,
            json.dumps(obj.enchantments)
        ))
        self.conn.commit()
        log_info(f"Saved object {obj.name} {obj.uuid} to database")
        
    def save_objects(self, objects):
        if self.conn is None:
            log_error("Object DB Error: Database connection is not open")
            return

        data = [(str(obj.uuid), obj.vnum, obj.name, obj.description, obj.action_description, obj.state, obj.insured, obj.location, obj.location_type, obj.max_hitpoints, obj.current_hitpoints, json.dumps(obj.enchantments)) for obj in objects]

        self.cursor.executemany("""
            INSERT OR REPLACE INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

        self.conn.commit()

    def load_objects(self):
        # print("Object DB Loading...")
        if self.conn is None:
            log_error("Object DB Error: Database connection is not open")
            return []
        self.cursor.execute("SELECT * FROM objects")
        rows = self.cursor.fetchall()
        objects = []
        for row in rows:
            try:
                obj_uuid = uuid.UUID(row[0])
            except ValueError:
                log_error(f"Object DB Error: Invalid UUID: {row[0]}")
                continue
            obj = ObjectInstance(object_manager.get_object(row[1]), instance_uuid=obj_uuid)
            if obj is None:
                log_error(f"Object DB Error: no object template found with vnum {row[0]}")
                continue
            obj.vnum = row[1]
            if row[2] is not None:
                obj.name = row[2]
            if row[3] is not None:
                obj.description = row[3]
            if row[4] is not None:
                obj.action_description = row[4]
            obj.state = row[5]
            obj.insured = row[6]
            obj.location = row[7]
            obj.location_type = row[8]
            obj.max_hitpoints = row[9]
            obj.current_hitpoints = row[10]
            try:
                obj.enchantments = json.loads(row[11])
            except json.JSONDecodeError:
                log_error(f"Object DB Error: Invalid JSON in enchantments: {row[11]}")
                continue
            # print(obj)
            objects.append(obj)
        return objects
    
    def delete_object(self, uuid):
        if self.conn is None:
            log_error("Object DB Error: Database connection is not open")
            return

        self.cursor.execute("""
            DELETE FROM objects WHERE uuid = ?
        """, (str(uuid),))

        self.conn.commit()

player_db = PlayerDatabase('player_database.db')
object_db = ObjectDatabase('object_database.db')

class PlayerManager:
    def __init__(self):
        self.players = []
        self.player_sockets = {}   
        

    def add_player(self, player):
        self.players.append(player)
        self.player_sockets[player.socket] = player

    def remove_player(self, player):
        try:
            self.players.remove(player)
            del self.player_sockets[player.socket]
            return True
        except ValueError:
            return False
        
    def get_player_by_socket(self, socket):
        return self.player_sockets.get(socket)        
        
    def get_players(self, LoggedIn=False):
        if not LoggedIn:
            return self.players
        else:
            return [player for player in self.players if player.loggedin]

    def get_player_by_name(self, name):
        for player in self.players:
            if player.name is None:
                continue
            if player.name.lower() == name.lower():
                return player
        return None
    
    def save_all_players(self):
        start_time = time.time()
        for player in self.players:
            player_db.save_player(player)
        log_info(f"Player Manager: saved all players in {time.time() - start_time:.2f} seconds")

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
        self.output_buffer = ""
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
        
        self.inventory = set() # set of object UUIDs (saved)
        self.inventory_list = {} # key: UUID, value: ObjectInstance (not saved)
        
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
        self.inventory = player_data['inventory']
        self.character = player_data['character']
        
        # load inventory_list
        for uuid in self.inventory:
            # print(f"Loading object {uuid}")
            obj = object_instance_manager.get_object_by_uuid(uuid)
            # print(f"Loaded object {obj}")
            if obj is not None:
                self.inventory_list[uuid] = obj
        
        return True
        
    def save_exists(self):
        return player_db.load_player(self.name) is not None

    def set_room(self, room):
        self.current_room = room

    def move_to_room(self, new_room):
        self.room_id = new_room.vnum
        if self.current_room is not None:
            self.current_room.remove_player(self)
        if new_room is not None:
            new_room.add_player(self)
            self.current_room = new_room
            
    def get_keywords(self):
        return [self.name.lower()]
            
    def get_description(self):        
        description = []
        description.append(self.name + " " + self.get_title() + "\n")
        #equipped = self.equipment.get_string_equipped_items()
        equipped = None
        if equipped:
            description.append("They are wearing:")
            description.append(equipped)
        if self.inventory:
            description.append(self.get_inventory_description(player_name=self.name))

        return "\n".join(description)
    
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
    
    def get_AC(self):
        return self.character.ac
    
    def add_inventory(self, obj_uuid):
        self.inventory.add(obj_uuid)
        obj = object_instance_manager.get_object_by_uuid(obj_uuid)
        if obj is not None:
            self.inventory_list[obj_uuid] = obj
        
    def remove_inventory(self, obj_uuid):
        self.inventory.remove(obj_uuid)
        del self.inventory_list[obj_uuid]
        
    def search_objects(self, keyword):
        keyword, number = process_keyword(keyword)
        matches = [obj for obj in self.inventory_list.values() if any(kw.startswith(keyword) for kw in obj.template.keywords.split())]
        return process_search_output(number, matches)

    def get_inventory_description(self, player_name=None):
        if player_name is None:
            if len(self.inventory_list) == 0:
                return "You are not carrying anything.\n"    
            msg = "You are carrying:\n"
        else:
            if len(self.inventory_list) == 0:
                return f"{player_name} is not carrying anything.\n"
            msg = f"{player_name} is carrying:\n"
        
        inventory_items = {}
        for obj in self.inventory_list.values():
            if obj.name in inventory_items:
                inventory_items[obj.name] += 1
            else:
                inventory_items[obj.name] = 1

        for name, count in inventory_items.items():
            count_str = f"({count:2})" if count > 1 else "     "
            msg += f"  {count_str} {name}\n"
                
        return msg
    
    def tick(self):
        self.character.tick(self.current_room)
    
        
class Character:
    def __init__(self, NPC=False):
        self.level = 1
        self.race = ""
        self.origin = ""
        self.death_room = 3000
            
        self.NPC = NPC
        self.inventory = set() # set of object UUIDs
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
        
        self.damdice_num = 1
        self.damdice_size = 4
        self.damdice_bonus = 2
        
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
        self.damdice_bonus = 2
        return self.damdice_num, self.damdice_size + (self.str - 10), self.damdice_bonus + self.level
    
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
    
    def death_xp_loss(self):
        death_xp_loss = dice_roll(self.level, 10, 25)
        self.xp -= death_xp_loss
        return f"You have lost {death_xp_loss} experience!\n"
    
    def flee_xp_loss(self):
        flee_xp_loss = dice_roll(self.level, 5, 10)
        self.xp -= flee_xp_loss
        return f"You have lost {flee_xp_loss} experience!\n"
            
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
        
    def tick(self, room):
        # update spell lengths
        
        REGEN_HP_RATE = self.max_hitpoints / 4
        REGEN_MANA_RATE = self.max_mana / 4
        REGEN_STAMINA_RATE = self.max_stamina
        
        if room.is_haven():
            REGEN_HP_RATE *= 2
            REGEN_MANA_RATE *= 2
            
        
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
        self.rooms[room.vnum] = room
        
    def get_room_by_vnum(self, vnum):
        ''' Returns a room object by its vnum, otherwise returns None'''
        return self.rooms.get(vnum)

    def remove_room(self, vnum):
        if vnum in self.rooms:
            del self.rooms[vnum]

    def get_all_rooms(self):
        return self.rooms.values()

    def get_rooms_by_attribute(self, attribute_name, value):
        return [room for room in self.rooms.values() if getattr(room, attribute_name, None) == value]

    def __str__(self):
        msg = ""
        for room in self.rooms.values():
            msg += f"Room {room.vnum}: {room.name}\n"
        return msg
    

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
    
    
    def get_max_hitpoints(self):
        return dice_roll(self.hitdice_num, self.hitdice_size, self.hitdice_bonus)
        
        
    def get_max_hitpoints(self):
        return dice_roll(self.hitdice_num, self.hitdice_size, self.hitdice_bonus)
        
class ObjectTemplate:
    def __init__(self, vnum):
        self.vnum = vnum
        self.keywords = ""
        self.short_description = ""
        self.long_description = ""
        self.action_description = ""
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
        
        self.max_hitpoints = 100 # in the future, can use this for object condition
    

        
class Room:
    def __init__(self, vnum):
        self.vnum = vnum
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
        
        available_exits_str = ' '.join(available_exits)
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
        
    def scan(self, player=None):
        msg = ""
        for exit in self.doors:
            if self.doors[exit]["locks"] == 0:
                msg += f"{first_to_upper(mud_consts.EXIT_NAMES[exit]): <10}"
                if self.doors[exit]["description"] != "":
                    msg += f"({self.doors[exit]["description"]})"
                msg += "\n"
                for mob in room_manager.get_room_by_vnum(self.doors[exit]["to_room"]).mob_list:
                    msg += f"    {mob.template.short_desc}\n"
            else:
                msg += f"{first_to_upper(mud_consts.EXIT_NAMES[exit]): <10} Locked\n"
        return msg
    
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
        if len(self.object_list) == 0:
            return ""    
        
        inventory_items = {}
        for obj in self.object_list:
            if obj.name in inventory_items:
                inventory_items[obj.name] += 1
            else:
                inventory_items[obj.name] = 1
        msg = ""
        for name, count in inventory_items.items():
            count_str = f"({count:2})" if count > 1 else "     "
            msg += f"  {count_str} {first_to_upper(name)}\n"
                
        return msg
    def search_mobs(self, keyword):
        keyword, number = process_keyword(keyword)
        matches = [mob for mob in self.mob_list if any(kw.startswith(keyword) for kw in mob.template.keywords.split())]
        return process_search_output(number, matches)
    
    def search_players(self, keyword):
        keyword, number = process_keyword(keyword)
        matches = [player for player in self.player_list if player.name.lower().startswith(keyword)]
        return process_search_output(number, matches)
    
    def search_objects(self, keyword):
        keyword, number = process_keyword(keyword)
        matches = [obj for obj in self.object_list if any(kw.startswith(keyword) for kw in obj.template.keywords.split())]
        return process_search_output(number, matches)

    def search_doors(self, keyword):
        keyword, number = process_keyword(keyword)
        matches = [door for door in self.doors if any(kw.startswith(keyword) for kw in self.doors[door]["keywords"].split())]
        return process_search_output(number, matches)
    
    def search_extended_descriptions(self, keyword):
        keyword, number = process_keyword(keyword)
        matches = [extended_description for extended_description in self.extended_descriptions if any(kw.startswith(keyword) for kw in extended_description["keywords"].split())]
        return process_search_output(number, matches)
    
    def is_haven(self):
        return check_flag(self.room_flags, mud_consts.ROOM_HAVEN)
    


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
        
        self.mob_repop_queue = set()
        self.obj_repop_queue = set()
        
    def add_mob_reset(self, ResetMob):
        self.mob_resets.append(ResetMob)
        
    def add_object_reset(self, ResetObject):
        self.object_resets.append(ResetObject)
        
    def add_to_mob_repop_queue(self, mob_reset):
        self.mob_repop_queue.add(mob_reset)
        
    def add_to_obj_repop_queue(self, obj_reset):
        self.obj_repop_queue.add(obj_reset)
        
    def process_mob_repop_queue(self):
        if len(self.mob_repop_queue) == 0:
            return False
        while self.mob_repop_queue:
            mob_reset = self.mob_repop_queue.pop()
            mob_template = mob_manager.get_mob_template(mob_reset.mob_vnum)
            room = room_manager.get_room_by_vnum(mob_reset.room_vnum)
            MobInstance(mob_template, mob_reset, room)
            
            # todo
            # for item in mob_reset.inventory:
            #     mob.add_item(item)
            # mob.mob_reset = mob_reset
            # mob_reset.equipment = Equipment()
            # for item in mob_reset.equipment:
            #     mob_reset.equipment.equip(item)
            # mob_reset.inventory = []
            # mob_reset.comment = ""
        return True
    
    def process_obj_repop_queue(self):
        if len(self.mob_repop_queue) == 0 and len(self.obj_repop_queue) == 0:
            return False
        while self.obj_repop_queue:
            obj_reset = self.obj_repop_queue.pop()
            room = room_manager.get_room_by_vnum(obj_reset.room_vnum)
            ObjectInstance(object_manager.get_object(obj_reset.obj_vnum), obj_reset=obj_reset, room=room)
            # todo
            # code for objects within containers
        return True
    
    def process_repop_queue(self):
        self.process_mob_repop_queue()
        self.process_obj_repop_queue()

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
    def __init__(self, template, mob_reset, room):
        self.template = template
        self.mob_reset = mob_reset
        self.name = self.template.short_desc
        self.current_room = None
        
        self.max_mana = 100
        self.current_mana = self.max_mana
        
        self.character = Character(NPC=True)
        
        self.character.max_hitpoints = dice_roll(template.hitdice_num, template.hitdice_size, template.hitdice_bonus)
        self.character.current_hitpoints = self.character.max_hitpoints
        self.character.ac = template.ac
        self.character.hitroll = template.hitroll
        self.character.damdice_num = template.damdice_num
        self.character.damdice_size = template.damdice_size
        self.character.amdice_bonus = template.damdice_bonus
        self.character.level = template.level
        
        self.set_room(room)
        mob_instance_manager.add_mob_instance(self)
        
        # todo
        self.equipment = Equipment()
        self.inventory = set() # set of object UUIDs (saved)
        self.inventory_list = {} # key: UUID, value: ObjectInstance (not saved)
        
        self.aggro_list = []
        
    def get_keywords(self):
        return self.template.keywords.split()

    def set_room(self, room):
        self.current_room = room
        room.add_mob(self)

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
            for item in self.inventory_list.values():
                description.append(f"\t{item.name}")

        return "\n".join(description) + "\n"
        
    def add_inventory(self, obj_uuid):
        self.inventory.add(obj_uuid)
        obj = object_instance_manager.get_object_by_uuid(obj_uuid)
        if obj is not None:
            self.inventory_list[obj_uuid] = obj
        
    def remove_inventory(self, obj_uuid):
        self.inventory.remove(obj_uuid)
        del self.inventory_list[obj_uuid]
        
    def get_hitroll(self):
        return self.template.hitroll
    
    def get_AC(self):
        return self.template.ac
    
    def get_damroll(self):
        return self.template.damdice_num, self.template.damdice_size, self.template.damdice_bonus
        
    def tick(self):
        self.character.tick(self.current_room)
        
class ObjectInstanceManager:
    def __init__(self):
        self.object_instances = {} # vnum: [object_instance1, object_instance2, ...]
        self.object_uuids = {} # uuid: object_instance
        
    def load_objects(self):
        object_instances = object_db.load_objects()
        for object_instance in object_instances:
            # self.add_object(object_instance)
            object_instance.load()
            
    def save_objects(self):
        objects = []
        start_time = time.time()
        for vnum in self.object_instances:
            for obj in self.object_instances[vnum]:
                if obj.state == 0: 
                    # don't save objects that are in OBJ_STATE_NORMAL
                    continue
                
                # if an object's descriptions are the same as the template, set them to None
                if obj.name == obj.template.short_description:
                    obj.name = None
                if obj.description == obj.template.long_description:
                    obj.description = None
                if obj.action_description == obj.template.action_description:
                    obj.action_description = None
                
                objects.append(obj)
                
                if obj.name is None:
                    obj.name = obj.template.short_description
                if obj.description is None:
                    obj.description = obj.template.long_description
                if obj.action_description is None:
                    obj.action_description = obj.template.action_description
 
        object_db.save_objects(objects)
        log_info(f"Saved {len(objects)} objects in {time.time() - start_time:.2f} seconds")

    def add_object(self, object_instance):
        # add to vnum dict
        if object_instance.vnum not in self.object_instances:
            self.object_instances[object_instance.vnum] = []
        self.object_instances[object_instance.vnum].append(object_instance)
        # add to uuid dict
        self.object_uuids[object_instance.uuid] = object_instance
        
    def remove_object(self, object_instance):
        #remove from vnum dict
        if object_instance.vnum in self.object_instances:
            self.object_instances[object_instance.vnum].remove(object_instance)
            if not self.object_instances[object_instance.vnum]:
                del self.object_instances[object_instance.vnum]
        # remove from uuid dict
        if object_instance.uuid in self.object_uuids:
            del self.object_uuids[object_instance.uuid]
    
    def get_object_by_uuid(self, uuid):
        return self.object_uuids.get(uuid)

    def get_all_instances_by_vnum(self, vnum):
        return self.object_instances.get(vnum, [])

    def get_instance_by_vnum(self, vnum, index):
        return self.object_instances.get(vnum, [None])[index]
    
    def get_all_instances(self):
        return [obj for obj_list in self.object_instances.values() for obj in obj_list]
    
class ObjectInstance:
    def __init__(self, template, obj_reset=None, room=None, instance_uuid=None):
        self.template = template
        self.vnum = template.vnum
        self.uuid = instance_uuid if instance_uuid is not None else uuid.uuid1()
        self.name = self.template.short_description
        self.description = self.template.long_description
        self.action_description = self.template.action_description
        
        self.state = mud_consts.OBJ_STATE_NORMAL
        self.insured = None # set to Player name if insured
        
        self.location = None
        self.location_type = None
        self.location_instance = None
        
        self.max_hitpoints = template.max_hitpoints
        self.current_hitpoints = self.max_hitpoints
        
        self.enchantments = {}
        
        if obj_reset is not None:
            self.obj_reset = obj_reset
            
        if room is not None:
            self.update_location("room", room.vnum, room)
            room.add_object(self)
        
        object_instance_manager.add_object(self)
                 
                    
    def save(self):
        object_db.save_object(self)
       
    def load(self):
        if self.location_type == "room":
            self.location = int(self.location)
            room = room_manager.get_room_by_vnum(self.location)
            if room is not None:
                self.location_instance = room
            else:
                log_error(f"Object load: couldn't load {self.name} ({self.vnum}) to room {self.location}")
        # we're probably not going to use these
        # elif self.location_type == "mob":
        #     self.location_instance = mob_instance_manager.get_instance_by_vnum(self.location, 0)
        # elif self.location_type == "object":
        #     self.location_instance = object_instance_manager.get_instance_by_vnum(self.location, 0)
        
        # todo locker code
        # for players, will be loaded via update location when they log in        
    
    def imp(self):
        if self.insured is not None:
            log_error(f"Object imp: object {self.vnum} {self.name} is insured")
            return
        
        if self.location_type == "room":
            self.location_instance.remove_object(self)
        elif self.location_type == "mob":
            if self.location_instance is not None:
                self.location_instance.remove_inventory(self.uuid)
        else:
            log_error(f"Object imp: object {self.vnum} {self.name} is not in a room or on a mob: {self.location_type}")
            return
        
        object_db.delete_object(self.uuid)
        object_instance_manager.remove_object(self)      
        
    
    def update_location(self, location_type, location, location_instance):
        self.location = location
        self.location_type = location_type
        self.location_instance = location_instance
        
    def update_state(self, state):
        if 0 <= state < mud_consts.OBJ_STATE_MAX:
            self.state = state
        else:
            log_error(f"Invalid state {state} (object {self.vnum} {self.name})")
            
    def get_keywords(self):
        return self.template.keywords.split()
    
    def get_description(self):
        description = []
        description.append(self.description)
        return "\n".join(description)  
    
    def get_action_description(self):
        description = []
        description.append(self.action_description)
        return "\n".join(description)
    
    def pickup(self, player):
        if self not in player.current_room.object_list:
            log_error(f"Object pickup: object {self.vnum} {self.name} by {player.name} is not in room {player.current_room.vnum}")
            return False
  
        if self.state == mud_consts.OBJ_STATE_INVENTORY or self.state == mud_consts.OBJ_STATE_LOCKER or self.state == mud_consts.OBJ_STATE_EQUIPPED:
            log_error(f"Object pickup: object {self.vnum} {self.name} by {player.name} is in state {self.state}")   
            return False
        
        if self.state == mud_consts.OBJ_STATE_NORMAL:
            # normal items need to reset on repop
            reset_manager.add_to_obj_repop_queue(self.obj_reset)
        
        player.current_room.remove_object(self)
        player.add_inventory(self.uuid)
        self.update_state(mud_consts.OBJ_STATE_INVENTORY)
        self.update_location("player", player.name, player)
        self.save()
        return True
    
    def drop(self, player):
        # todo code to check for no drop flag
        
        if self.uuid not in player.inventory:
            log_error(f"Object drop: object {self.vnum}, {self.name} not in {player.name} inventory")
            return False
        
        if self.state == mud_consts.OBJ_STATE_LOCKER or self.state == mud_consts.OBJ_STATE_EQUIPPED:
            log_error(f"Object pickup: object {self.vnum} {self.name} by {player.name} is in state {self.state}")   
            return False

        self.update_state(mud_consts.OBJ_STATE_DROPPED)
        
        player.current_room.add_object(self)
        player.remove_inventory(self.uuid)
        self.update_location("room", player.current_room.vnum, player.current_room)
        self.save()
        return True
     
    def give(self, player, target):
        if self.uuid not in player.inventory:
            log_error(f"Object give: object {self.vnum}, {self.name} not in {player.name} inventory")
            return False
        
        if self.state == mud_consts.OBJ_STATE_LOCKER or self.state == mud_consts.OBJ_STATE_EQUIPPED:
            log_error(f"Object pickup: object {self.vnum} {self.name} by {player.name} is in state {self.state}")   
            return False
        
        target_is = "player"
        
        if target.character.NPC:
            if self.state != mud_consts.OBJ_STATE_SPECIAL and self.state != mud_consts.OBJ_STATE_QUEST:
                self.update_state(mud_consts.OBJ_STATE_DROPPED)
            target_is = "mob"

        self.update_location(target_is, target.name, target)    
        player.remove_inventory(self.uuid)
        target.add_inventory(self.uuid)
        
        self.save()
        return True
       
    
    # for debugging
    def __str__(self):
        msg = f"{self.vnum} {self.name} {self.state}"
        msg += f" Location: {self.location_type} {self.location} {self.location_instance}"
        return msg

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