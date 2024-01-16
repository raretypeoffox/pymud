# mud_objects.py

import sqlite3
import threading
import pickle
from datetime import datetime
import time
import random
import uuid
import json
from enum import Enum

from mud_shared import dice_roll, colourize, log_info, log_error, check_flag, first_to_upper, process_keyword, process_search_output
import mud_consts
from mud_consts import Exits, ObjState, MobActFlags, RoomFlags, RoomSectorType
from mud_abilities import Abilities

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
            
            if player.name is None or player.name == "":
                log_error("Player_DB: Error saving player, player name is None or empty")
                return
            
            player_name = player.name.lower()
            character_data = pickle.dumps(player.character)
            inventory = [str(i) for i in player.inventory]
            self.cursor.execute('''
                INSERT OR REPLACE INTO players (name, room_id, current_recall, created, lastlogin, title, inventory, character)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (player_name, player.room_id, player.current_recall, player.created, player.lastlogin, player.title, json.dumps(inventory), character_data))
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

    def query_player(self, player_name, fields):
        '''
        Queries the player database for specific fields of a player.

        Parameters:
        player_name (str): The name of the player to query.
        fields (list): A list of strings representing the fields to query.

        Returns:
        list: A list containing the values of the requested fields for the player, in the same order as the fields parameter.
            Returns None if the player does not exist or if any of the requested fields do not exist.
        '''
        with self.lock:
            try:
                # Construct the SQL query
                sql = 'SELECT {} FROM players WHERE LOWER(name) = LOWER(?)'.format(', '.join(fields))
                self.cursor.execute(sql, (player_name.lower(),))

                result = self.cursor.fetchone()
                if result is None:
                    return None
                else:
                    return list(result)
            except sqlite3.OperationalError:
                # This exception is raised if any of the requested fields do not exist
                return None
        
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
                action_desc TEXT,
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
            obj.action_desc,
            obj.state.value,
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

        data = [(str(obj.uuid), obj.vnum, obj.name, obj.description, obj.action_desc, obj.state.value, obj.insured, obj.location, obj.location_type, obj.max_hitpoints, obj.current_hitpoints, json.dumps(obj.enchantments)) for obj in objects]

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
            obj = ObjectInstance(object_manager.get(row[1]), instance_uuid=obj_uuid)
            if obj is None:
                log_error(f"Object DB Error: no object template found with vnum {row[0]}")
                continue
            obj.vnum = row[1]
            if row[2] is not None:
                obj.name = row[2]
            if row[3] is not None:
                obj.description = row[3]
            if row[4] is not None:
                obj.action_desc = row[4]
            obj.state = ObjState(row[5])
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

class KeyedEntityManager:
    def __init__(self):
        self.items = {}
        
    def add(self, id, item):
        self.items[id] = item
    
    def get(self, id):
        return self.items.get(id)
    
    def remove(self, id):
        if id in self.items:
            del self.items[id]
            
    def get_all(self):
        return self.items.values()

class InstanceManager:
    def __init__(self):
        self.instances = {}  # vnum: [instance1, instance2, ...]

    def add(self, instance):
        if instance.vnum not in self.instances:
            self.instances[instance.vnum] = []
        self.instances[instance.vnum].append(instance)

    def remove(self, instance):
        if instance.vnum in self.instances:
            self.instances[instance.vnum].remove(instance)
            if not self.instances[instance.vnum]:
                del self.instances[instance.vnum]

    def get_all_by_vnum(self, vnum):
        return self.instances.get(vnum, [])

    def get(self, vnum, index):
        return self.instances.get(vnum, [None])[index]

    def get_all(self):
        return [instance for instance_list in self.instances.values() for instance in instance_list]

class MobInstanceManager(InstanceManager):
    pass

class ObjectInstanceManager(InstanceManager):
    def __init__(self):
        super().__init__()
        self.uuids = {}  # uuid: object_instance

    # ObjectInstanceManager specific methods go here
    
    # extend add to also add uuids
    def add(self, object_instance):
        super().add(object_instance)
        self.uuids[object_instance.uuid] = object_instance
        
    def get_object_by_uuid(self, uuid):
        return self.uuids.get(uuid)
    
    def load_objects(self):
        object_instances = object_db.load_objects()
        for object_instance in object_instances:
            # self.add_object(object_instance)
            object_instance.load()
            
    def save_objects(self):
        objects = []
        start_time = time.time()
        for vnum in self.instances:
            for obj in self.instances[vnum]:
                if obj.state == ObjState.NORMAL: 
                    # don't save objects that are in NORMAL
                    continue
                
                # if an object's descriptions are the same as the template, set them to None
                if obj.name == obj.template.short_desc:
                    obj.name = None
                if obj.desc == obj.template.long_desc:
                    obj.desc = None
                if obj.action_desc== obj.template.action_desc:
                    obj.action_desc = None
                
                objects.append(obj)
                
                if obj.name is None:
                    obj.name = obj.template.short_desc
                if obj.desc is None:
                    obj.desc = obj.template.long_desc
                if obj.action_desc is None:
                    obj.action_desc = obj.template.action_desc
 
        object_db.save_objects(objects)
        log_info(f"Saved {len(objects)} objects in {time.time() - start_time:.2f} seconds")

class PlayerManager(KeyedEntityManager):
   
    def get_players(self, LoggedIn=False):
        if not LoggedIn:
            return list(self.items.values())
        else:
            return [player for player in self.items.values() if player.loggedin]

    def get_player_by_name(self, name):
        for player in self.items.values():
            if player.name is None:
                continue
            if player.name.lower() == name.lower():
                return player
        return None
    
    def save_all_players(self):
        start_time = time.time()
        for player in self.items.values():
            if player.loggedin:
                player_db.save_player(player)
        log_info(f"Player Manager: saved all players in {time.time() - start_time:.2f} seconds")
    
    def disconnect_player(self, player, msg=""):
        if msg:
            try:
                player.socket.send(msg.encode('utf-8'))
            except OSError:
                pass # The socket is already closed
        player.save()
            
        return self.remove(player.socket)

class Player:
    def __init__(self, fd, socket):
        self.fd = fd
        self.socket = socket
        self.output_buffer = ""
        self.loggedin = False
        self.reconnect_prompt = False
        self.awaiting_reconnect_confirmation = False
        self.awaiting_race = False
        self.awaiting_origin = False
        self.gmcp = None     
        
        self.name = None
        self.room_id = 3001
        self.current_room = None
        self.current_recall = 0
        self.character = Character()
        
        self.group = None
        self.follow = None
        
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
        self.set_room(room_manager.get(self.room_id))
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
        if self.gmcp is not None:
            self.gmcp.update_status()
            self.gmcp.update_room()
            
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
        return self.character.get_AC()
    
    def add_inventory(self, obj_uuid):
        self.inventory.add(obj_uuid)
        obj = object_instance_manager.get_object_by_uuid(obj_uuid)
        if obj is not None:
            self.inventory_list[obj_uuid] = obj
        
    def remove_inventory(self, obj_uuid):
        self.inventory.remove(obj_uuid)
        del self.inventory_list[obj_uuid]
    
    def get_objects(self):
        return set(self.inventory_list.values())

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
        if self.gmcp is not None:
            self.gmcp.update_status()

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
        
        self.alignment = 0
        
        self.racials = []
        self.abilities = Abilities()
   
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
        
        if room.flag(RoomFlags.HAVEN):
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
                msg += colourize(f"{mud_consts.EQ_SLOTS[int(item.template.wear_flags)]: <20}{item.template.short_desc}\n", "yellow")
            return msg
        else:
            return None


class Group:
    def __init__(self, leader):
        self.leader = leader
        self.members = [leader]

    def add_member(self, player):
        self.members.append(player)

    def remove_member(self, player):
        self.members.remove(player)
  
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
        if check_flag(self.act_flags, MobActFlags.SENTINEL):
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
        self.short_desc = ""
        self.long_desc = ""
        self.action_desc = ""
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
        
        self.doors = {}
        self.extended_descriptions = []
    
        self.mob_list = set()
        self.object_list = set()
        self.player_list = set()
        self.door_list = set()
        self.extended_descriptions_list = set()

    def add_door(self, door_number, door_description, keywords, locks, key, to_room):
        self.doors[door_number] = {
            "description": door_description,
            "keywords": keywords,
            "locks": locks,
            "key": key,
            "to_room": to_room
        }
        self.door_list.add(Door(door_number, door_description, keywords, locks, key, to_room))

    def add_extended_description(self, keywords, description):
        self.extended_descriptions.append({
            "keywords": keywords,
            "description": description
        })
        self.extended_descriptions_list.add(ExtendedDescription(keywords, description))
        
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
        available_exits = []
        
        for i in range(len(Exits)):
            if i in self.doors:
                if self.doors[i]["locks"] == 0:
                    available_exits.append(Exits.get_name_by_value(i))
                else:
                    available_exits.append(Exits.get_name_by_value(i) + " (locked)")
        
        available_exits_str = ' '.join(available_exits)
        return available_exits_str
    
    def choose_random_door(self, exclude_other_area=True):
        available_doors = []
        for door in self.doors:
            if exclude_other_area and room_manager.get(self.doors[door]["to_room"]).area_number != self.area_number:
                continue
            if self.doors[door]["locks"] == 0:
                available_doors.append(door)
        if available_doors:
            return random.choice(available_doors)
        else:
            return None
        
    def scan(self, player=None):
        msg = ""
        count_per_exit = {}
        for exit in self.doors:
            if self.doors[exit]["locks"] == 0:
                count_per_exit[exit] = 0
                msg += f"{first_to_upper(Exits.get_name_by_value(exit)): <10}"
                if self.doors[exit]["description"] != "":
                    msg += f"({self.doors[exit]["description"]})"
                msg += "\n"
                for player in room_manager.get(self.doors[exit]["to_room"]).player_list:
                    position_str = "."
                    if player.character.position == "Sleep":
                        position_str = " is sleeping here."
                    elif player.character.position == "Rest":
                        position_str = " is resting here."
                    msg += colourize(f"    {player.name} {player.get_title()}{position_str}\n", "cyan")
                    count_per_exit[exit] += 1
                for mob in room_manager.get(self.doors[exit]["to_room"]).mob_list:
                    msg += colourize(f"    {first_to_upper(mob.template.long_desc)}", "cyan")
                    count_per_exit[exit] += 1
                if count_per_exit[exit] == 0:
                    msg += "    You see no one here.\n"
            else:
                msg += f"{first_to_upper(Exits.get_name_by_value(exit)): <10} Locked\n"
        return msg
    
    def get_players(self):
        return self.player_list
    
    def get_mobs(self):
        return self.mob_list
    
    def get_objects(self):
        return self.object_list
    
    def get_doors(self):
        return self.door_list
    
    def get_extended_descriptions(self):
        return self.extended_descriptions_list    
    
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

    def flag(self, flag):
        return check_flag(self.room_flags, flag)

class Door:
    def __init__(self, door_number, door_description, keywords, locks, key, to_room):
        self.door_number = door_number
        self.description = door_description
        self.keywords = keywords
        self.locks = locks
        self.key = key
        self.to_room = to_room
        
    def get_keywords(self):
        return self.keywords.split()
    
    def get_description(self):
        return self.description

class ExtendedDescription:
    def __init__(self, keywords, description):
        self.keywords = keywords
        self.description = description
        
    def get_keywords(self):
        return self.keywords.split()
    
    def get_description(self):
        return self.description 



      
class MobInstance:
    def __init__(self, template, mob_reset, room):
        self.template = template
        self.mob_reset = mob_reset
        self.name = self.template.short_desc
        self.vnum = template.vnum
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
        mob_instance_manager.add(self)
        
        # todo
        self.equipment = Equipment()
        self.inventory = set() # set of object UUIDs (saved)
        self.inventory_list = {} # key: UUID, value: ObjectInstance (not saved)
        
        self.group = None
        self.follow = None
        
        self.aggro_list = set()
        
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
        return self.character.get_AC()
    
    def get_damroll(self):
        return self.template.damdice_num, self.template.damdice_size, self.template.damdice_bonus
        
    def tick(self):
        self.character.tick(self.current_room)
        
        if random.uniform(0, 1) < 0.2 and self.aggro_list:
            self.aggro_list.pop()

class ObjectInstance:
    def __init__(self, template, obj_reset=None, room=None, instance_uuid=None):
        self.template = template
        self.vnum = template.vnum
        self.uuid = instance_uuid if instance_uuid is not None else uuid.uuid1()
        self.name = self.template.short_desc
        self.desc = self.template.long_desc
        self.action_desc = self.template.action_desc
        
        self.state = ObjState.NORMAL
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
        
        object_instance_manager.add(self)
                 
                    
    def save(self):
        object_db.save_object(self)
       
    def load(self):
        if self.location_type == "room":
            self.location = int(self.location)
            room = room_manager.get(self.location)
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
        elif self.location_type == "player":
            if self.location_instance is not None:
                self.location_instance.remove_inventory(self.uuid)
        else:
            log_error(f"Object imp: object {self.vnum} {self.name} is not in a known location: {self.location_type}")
            return
        
        object_db.delete_object(self.uuid)
        object_instance_manager.remove(self)      
        
    
    def update_location(self, location_type, location, location_instance):
        self.location = location
        self.location_type = location_type
        self.location_instance = location_instance
        
    def update_state(self, state):
        if isinstance(state, Enum) and 0 <= state.value < ObjState.MAX.value:
            self.state = state
        else:
            log_error(f"Invalid state {state} (object {self.vnum} {self.name})")
            
    def get_keywords(self):
        return self.template.keywords.split()
    
    def get_description(self):
        description = []
        description.append(self.description)
        return "\n".join(description)  
    
    def get_action_desc(self):
        description = []
        description.append(self.action_desc)
        return "\n".join(description)
    
    def pickup(self, player):
        if self not in player.current_room.object_list:
            log_error(f"Object pickup: object {self.vnum} {self.name} by {player.name} is not in room {player.current_room.vnum}")
            return False
  
        if self.state == ObjState.INVENTORY or self.state == ObjState.LOCKER or self.state == ObjState.EQUIPPED:
            log_error(f"Object pickup: object {self.vnum} {self.name} by {player.name} is in state {self.state}")   
            return False
        
        if self.state == ObjState.NORMAL:
            # normal items need to reset on repop
            reset_manager.add_to_obj_repop_queue(self.obj_reset)
        
        player.current_room.remove_object(self)
        player.add_inventory(self.uuid)
        self.update_state(ObjState.INVENTORY)
        self.update_location("player", player.name, player)
        self.save()
        return True
    
    def drop(self, player):
        # todo code to check for no drop flag
        
        if self.uuid not in player.inventory:
            log_error(f"Object drop: object {self.vnum}, {self.name} not in {player.name} inventory")
            return False
        
        if self.state == ObjState.LOCKER or self.state == ObjState.EQUIPPED:
            log_error(f"Object drop: object {self.vnum} {self.name} by {player.name} is in state {self.state}")   
            return False

        self.update_state(ObjState.DROPPED)
        
        player.current_room.add_object(self)
        player.remove_inventory(self.uuid)
        self.update_location("room", player.current_room.vnum, player.current_room)
        self.save()
        return True
     
    def give(self, player, target):
        if self.uuid not in player.inventory:
            log_error(f"Object give: object {self.vnum}, {self.name} not in {player.name} inventory")
            return False
        
        if self.state == ObjState.LOCKER or self.state == ObjState.EQUIPPED:
            log_error(f"Object pickup: object {self.vnum} {self.name} by {player.name} is in state {self.state}")   
            return False
        
        target_is = "player"
        
        if target.character.NPC:
            if self.state != ObjState.SPECIAL and self.state != ObjState.QUEST:
                self.update_state(ObjState.DROPPED)
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
            mob_template = mob_manager.get(mob_reset.mob_vnum)
            room = room_manager.get(mob_reset.room_vnum)
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
            room = room_manager.get(obj_reset.room_vnum)
            ObjectInstance(object_manager.get(obj_reset.obj_vnum), obj_reset=obj_reset, room=room)
            # todo
            # code for objects within containers
        return True
    
    def process_repop_queue(self):
        self.process_mob_repop_queue()
        self.process_obj_repop_queue()

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
    
    def get_current_target(self, character):
        return self.current_target.get(character)
    
    def get_next_target(self, character):
        targets = self.get_combat_targets(character)
        if targets:
            return next(iter(targets))
        else:
            return None
    
    def set_next_target(self, character):
        next_target = self.get_next_target(character)
        if next_target is not None:
            self.current_target[character] = next_target
            return next_target
        else:
            return None

    def in_combat(self, character):
        return character in self.combat_dict and len(self.combat_dict[character]) > 0

    def all_targeting_character(self, character):
        return [char for char, target in self.current_target.items() if target == character]

    def end_combat_with_all(self, player):
        for character in self.all_targeting_character(player):
            self.end_combat(player, character)
            self.end_combat(character, player)

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

# Init Global databases
player_db = PlayerDatabase('player_database.db')
object_db = ObjectDatabase('object_database.db')

# Init Player Manager
player_manager = PlayerManager()

# Init Global template managers
room_manager = KeyedEntityManager()
mob_manager = KeyedEntityManager()
object_manager = KeyedEntityManager()

# Init Global reset manager
reset_manager = Resets()

# Init Global instance managers
mob_instance_manager = MobInstanceManager()
object_instance_manager = ObjectInstanceManager()

# Init Global combat manager
combat_manager = CombatManager()

