# mud_world.py

from mud_shared import dice_roll

all_rooms = {}
all_mobs = {}
all_mob_resets = []


class Room:
    def __init__(self, room_id, name, description):
        self.room_id = room_id
        self.name = name
        self.description = description
        self.area = None
        self.room_flags = None
        self.sector_type = None
        self.doors = {}  # Door information
        self.extended_descriptions = []  # Extended descriptions
        
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
        mob_names_str = '\n'.join('\t' + name for name in mob_names)
        return mob_names_str

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


class MobInstance:
    def __init__(self, template):
        self.template = template
        self.current_room = None
        
        self.max_hitpoints = dice_roll(template.hitdice_num, template.hitdice_size, template.hitdice_bonus)
        self.current_hitpoints = self.max_hitpoints
        self.max_mana = 100
        self.current_mana = self.max_mana
        
        self.aggro_list = []

    def set_room(self, room):
        self.current_room = room

    def move_to_room(self, new_room):
        if self.current_room is not None:
            self.current_room.remove_mob(self)
        new_room.add_mob(self)
        self.current_room = new_room

class MobReset:
    def __init__(self, mob_vnum, max_count, room_vnum):
        self.mob_vnum = mob_vnum
        self.max_count = max_count
        self.room_vnum = room_vnum
        
def parse_flags(flag_string):
    if '|' in flag_string:
        numbers = map(int, flag_string.split('|'))
        return sum(numbers)
    else:
        return int(flag_string)
    
def load_mobs_from_are_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    mobs = {}
    current_mob = None
    parse_flag = False  # Flag to start parsing mobs
    line_index = 0

    while line_index < len(lines):
        line = lines[line_index].strip()

        if line == "#MOBILES":
            parse_flag = True
        elif line == "#0":
            parse_flag = False
        elif parse_flag:
            if line.startswith("#"):
                vnum = int(line[1:])
                line_index += 1
                line = lines[line_index].strip()
                keywords = line[:-1]
                line_index += 1
                line = lines[line_index].strip()
                short_desc = ""
                while line != "~":
                    short_desc = short_desc + line
                    if len(line) > 1 and line[-1] == "~":
                        short_desc = short_desc[:-1]
                        break
                    line_index += 1
                    line = lines[line_index].strip()
                
                line_index += 1
                line = lines[line_index].strip()
                
                long_desc = ""
                while line != "~":
                    long_desc = long_desc + line
                    if len(line) > 1 and line[-1] == "~":
                        long_desc = long_desc[:-1]
                        break
                    line_index += 1
                    line = lines[line_index].strip()
                
                line_index += 1
                line = lines[line_index].strip()
                
                desc = ""
                while line != "~":
                    desc = desc + line
                    if len(line) > 1 and line[-1] == "~":
                        desc = desc[:-1]
                        break
                    line_index += 1
                    line = lines[line_index].strip()
                
                line_index += 1
                line = lines[line_index].strip()
                
                parts = line.split()
                act_flags = parse_flags(parts[0])
                aff_flags = parse_flags(parts[1])
                align = int(parts[2])
                
                line_index += 1
                line = lines[line_index].strip()
                parts = line.split()
                level = int(parts[0])
                hitroll = int(parts[1])
                ac = int(parts[2])
                dice = parts[3].replace('D', 'd').split('d')
                hitdice_num = int(dice[0])
                dice = dice[1].split('+')
                hitdice_size = int(dice[0])
                hitdice_bonus = int(dice[1])
                dice = parts[4].replace('D', 'd').split('d')
                print(file_path, vnum, dice, parts, dice[0])
                damdice_num = int(dice[0])
                dice = dice[1].split('+')
                damdice_size = int(dice[0])
                damdice_bonus = int(dice[1])
                
                line_index += 1
                line = lines[line_index].strip()
                
                parts = line.split()
                gold = int(parts[0])
                xp = int(parts[1])
                
                line_index += 1
                line = lines[line_index].strip()
                
                parts = line.split()
                sex = int(parts[2])
                
                current_mob = MobTemplate(vnum, keywords, short_desc, long_desc, desc, act_flags, aff_flags, align, level, hitroll, ac, hitdice_num, hitdice_size, hitdice_bonus, damdice_num, damdice_size, damdice_bonus, gold, xp, sex)
                mobs[vnum] = current_mob

        line_index += 1

    return mobs

def load_rooms_from_are_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    rooms = {}
    current_room = None
    parse_flag = False  # Flag to start parsing rooms
    line_index = 0

    while line_index < len(lines):
        line = lines[line_index].strip()
        
        if line == "#ROOMS":
            parse_flag = True  # Start parsing after encountering #ROOMS
            line_index += 1
            continue
        
        if parse_flag and line.startswith("#"):
            if line == "#0":
                break
            else:             
                room_id = int(line[1:])
                current_room = Room(room_id, "", "")
                current_room.description = ""
                line_index += 1
                line = lines[line_index].strip()
                current_room.name = line[:-1]
                line_index += 1
                line = lines[line_index].strip()
                
                while line != "~":
                    current_room.description = current_room.description + line + "\n"
                    if len(line) > 1 and line[-1] == "~":
                        current_room.description = current_room.description[:-1]
                        break
                    line_index += 1
                    line = lines[line_index].strip()
                    
                line_index += 1
                line = lines[line_index].strip() 
                
                extra_flags = lines[line_index].split()

                current_room.area, current_room.room_flags, current_room.sector_type = int(extra_flags[0]), parse_flags(extra_flags[1]), int(extra_flags[2])
                line_index += 1
                line = lines[line_index].strip() 

        if parse_flag and current_room:
            if line.startswith("D"):
                door_number, door_desc, door_keywords, locks, key, to_room, line_index = parse_door_data(lines, line_index)
                current_room.add_door(door_number, door_desc, door_keywords, locks, key, to_room)
            elif line.startswith("E"):
                keywords, description, line_index = parse_extended_description(lines, line_index)
                current_room.add_extended_description(keywords, description)
            elif line == "S":
                rooms[current_room.room_id] = current_room
                current_room = None
                line_index += 1
            else:
                line_index += 1
        else:
            line_index += 1

    return rooms


def parse_door_data(lines, current_line):
    
    door_number = int(lines[current_line][1:])
    current_line += 1
    line = lines[current_line].strip()
    
    door_description = ""
    while line != "~":
        door_description = door_description + lines[current_line] + "\n"
        if len(line) > 1 and line[-1] == "~":
            door_description = door_description[:-1]
            break
        current_line += 1
        line = lines[current_line].strip()
    current_line += 1
    
    door_keywords = ""
    while line != "~":
        door_keywords = door_keywords + lines[current_line] + "\n"
        if len(line) > 1 and line[-1] == "~":
            door_keywords = door_keywords[:-1]
            break
        current_line += 1  
        line = lines[current_line].strip()  
    current_line += 1

    lock_info = lines[current_line].split()
    door_locks, door_key, to_room = int(lock_info[0]), int(lock_info[1]), int(lock_info[2])
    current_line += 1

    return door_number, door_description.strip(), door_keywords.strip(), door_locks, door_key, to_room, current_line

def parse_extended_description(lines, current_line):
    extended_keywords = lines[current_line + 1]
    extended_description = []
    current_line += 2

    while not lines[current_line].startswith("~"):
        extended_description.append(lines[current_line])
        current_line += 1

    return extended_keywords, " ".join(extended_description), current_line + 1

def load_mob_resets(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    mob_resets = []
    parse_flag = False  # Flag to start parsing rooms
    line_index = 0

    while line_index < len(lines):
        line = lines[line_index].strip()
        
        if line == "#RESETS":
            parse_flag = True  # Start parsing after encountering #ROOMS
            line_index += 1
            continue
        
        if parse_flag and line.startswith("S"):
            parse_flag = False
            break
        
        if parse_flag and line.startswith("M"):
            parts = line.split()
            if len(parts) >= 5:
                # Extract the mob vnum, max count, and room vnum
                mob_vnum = int(parts[2])
                max_count = int(parts[3])
                room_vnum = int(parts[4])
                mob_resets.append(MobReset(mob_vnum, max_count, room_vnum))
                
        line_index += 1   
    return mob_resets


def load_area_files_list(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    are_files = [line.strip() for line in lines if line.strip() != '$']
    return are_files

def get_room_by_id(room_id):
    # room_id = int(room_id)
    print(f"Getting room {room_id}")
    print(f"Room {room_id} is {all_rooms.get(room_id, None)}")
    return all_rooms.get(room_id, None)

def reset_world():
    for mob_reset in all_mob_resets:
        mob_template = all_mobs.get(mob_reset.mob_vnum, None)
        if mob_template is not None:
            room = get_room_by_id(mob_reset.room_vnum)
            if room is not None:
                for i in range(mob_reset.max_count):
                    mob = MobInstance(mob_template)
                    mob.set_room(room)
                    room.add_mob(mob)
                    print(f"Added mob {mob.template.vnum} to room {room.room_id}")
            else:
                print(f"Room {mob_reset.room_vnum} not found")
        else:
            print(f"Mob {mob_reset.mob_vnum} not found")

def build_world():
    print("Building world...")
    area_list_path = 'world/area.lst'  # Update this path to your area.lst file location
    are_files = load_area_files_list(area_list_path)

    for are_file in are_files:
        full_path = f'world/{are_file}'  # Update the path as necessary
        print(f"Loading rooms from {full_path}")
        rooms = load_rooms_from_are_file(full_path)
        all_rooms.update(rooms)

    print(f"{len(all_rooms)} rooms from {len(are_files)} area files loaded successfully.")
    
    for are_file in are_files:
        full_path = f'world/{are_file}'  # Update the path as necessary
        print(f"Loading mobs from {full_path}")
        mobs = load_mobs_from_are_file(full_path)
        all_mobs.update(mobs)
        
    for are_file in are_files:
        full_path = f'world/{are_file}'
        print(f"Loading mob resets from {full_path}")
        global all_mob_resets
        mob_resets = load_mob_resets(full_path)
        all_mob_resets = all_mob_resets + mob_resets

    for mobs in all_mobs.values():
        print(f"Loaded mob {mobs.vnum}: {mobs.short_desc}")
        
    reset_world()
            
if __name__ == '__main__':
    build_world()
     
    

