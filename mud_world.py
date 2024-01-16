import time

from mud_objects import MobTemplate, Room, ResetMob, ResetObject, ObjectTemplate, MobInstance, ObjectInstance
from mud_objects import room_manager, mob_manager, object_manager, reset_manager, mob_instance_manager, object_instance_manager
from mud_shared import log_info, log_error

### Parsing functions


def equip_number_to_slot(number):
    slot_map = {
        0: "light",
        1: "ring_left",
        2: "ring_right",
        3: "neck_one",
        4: "neck_two",
        5: "body",
        6: "head",
        7: "legs",
        8: "feet",
        9: "hands",
        10: "arms",
        11: "off_hand",
        12: "about_body",
        13: "waist",
        14: "wrist_left",
        15: "wrist_right",
        16: "main_hand",
        17: "held",
    }
    return slot_map.get(number, f"Invalid slot number: {number}")



def parse_multi_line(lines):
    ret_string = ""
    offset = 0
    for line in lines:
        offset += 1
        if line.endswith('~'):
            ret_string += line[:-1]
            return ret_string, offset
        elif line.startswith('~'):
            return ret_string, offset
        else:
            ret_string += line + '\n'
            
def parse_flags(flag_string):
    if '|' in flag_string:
        numbers = map(int, flag_string.split('|'))
        return sum(numbers)
    else:
        return int(flag_string)
    
def parse_mob(lines):
    mob_vnum = int(lines[0][1:])
    offset = 1
    mob_keywords, offset_add = parse_multi_line(lines[offset:])
    mob_keywords = mob_keywords.lower()
    offset += offset_add
    mob_short_desc, offset_add = parse_multi_line(lines[offset:])
    offset += offset_add
    mob_long_desc, offset_add = parse_multi_line(lines[offset:])
    offset += offset_add
    mob_desc, offset_add = parse_multi_line(lines[offset:])
    offset += offset_add
    
    parts = lines[offset].split()
    act_flags = parse_flags(parts[0])
    aff_flags = parse_flags(parts[1])
    align = int(parts[2])
    offset += 1
    
    parts = lines[offset].split()
    level, hitroll, ac = int(parts[0]), int(parts[1]), int(parts[2])
    dice = parts[3].replace('D', 'd').split('d')
    hitdice_num = int(dice[0])
    dice = dice[1].split('+')
    hitdice_size, hitdice_bonus = int(dice[0]), int(dice[1])
    dice = parts[4].replace('D', 'd').split('d')
    damdice_num = int(dice[0])
    dice = dice[1].split('+')
    damdice_size, damdice_bonus = int(dice[0]), int(dice[1])
    offset += 1

    parts = lines[offset].split()
    gold, xp = int(parts[0]), int(parts[1])

    offset += 1
    parts = lines[offset].split()
    sex = int(parts[2])
    
    current_mob = MobTemplate(mob_vnum, mob_keywords, mob_short_desc, mob_long_desc, mob_desc, act_flags, aff_flags, align, level, hitroll, ac, hitdice_num, hitdice_size, hitdice_bonus, damdice_num, damdice_size, damdice_bonus, gold, xp, sex)
    mob_manager.add(mob_vnum, current_mob)         
    
def parse_object(lines):
    obj_vnum = int(lines[0][1:])
    current_object = ObjectTemplate(obj_vnum)
    offset = 1
    current_object.keywords, offset_add = parse_multi_line(lines[offset:])
    current_object.keywords = current_object.keywords.lower()
    offset += offset_add
    current_object.short_description, offset_add = parse_multi_line(lines[offset:])
    offset += offset_add
    current_object.long_description, offset_add = parse_multi_line(lines[offset:])
    offset += offset_add
    current_object.action_description, offset_add = parse_multi_line(lines[offset:]) 
    offset += offset_add
    
    current_object.item_type, current_object.extra_flags, current_object.wear_flags = lines[offset].split()
    current_object.item_type = int(current_object.item_type)
    current_object.extra_flags = parse_flags(current_object.extra_flags)
    wear_flags = current_object.wear_flags.split("|")
    if len(wear_flags) == 1:
        wear_flags = int(wear_flags[0])
        if wear_flags % 2 == 1:
            wear_flags = wear_flags - 1
        if wear_flags > 0:    
            current_object.wear_flags = wear_flags
    else:  
        current_object.wear_flags = int(wear_flags[1])
    offset+=1
    
    current_object.value_0, current_object.value_1, current_object.value_2, current_object.value_3 = lines[offset].split()
    current_object.value_0 = parse_flags(current_object.value_0)
    current_object.value_1 = parse_flags(current_object.value_1)
    current_object.value_2 = parse_flags(current_object.value_2)
    current_object.value_3 = parse_flags(current_object.value_3)
    offset+=1
    
    current_object.weight, current_object.cost, _ = lines[offset].split()
    current_object.weight = int(current_object.weight)
    current_object.cost = int(current_object.cost)
    offset+=1
    
    # E and A sections not currently processed
    
    object_manager.add(obj_vnum, current_object)
    # print("Object", lines)

def parse_room(lines):
    vnum = int(lines[0][1:])
    current_room = Room(vnum)
    current_room.name = lines[1][:-1]
    # print(current_room.name)
    current_room.description, offset = parse_multi_line(lines[2:])
    offset+=2
    
    parse_line = lines[offset].split()
    try:
        current_room.area_number = int(parse_line[0])
        current_room.room_flags = parse_flags(parse_line[1])
        current_room.sector_type = int(parse_line[2])
    except:
        log_error(f"Error parsing room {current_room.name} {vnum} line {offset}: {lines[offset]} - missing room flags or sector type")
    offset+=1
    
    while lines[offset].startswith('S') == False:
        if lines[offset].startswith('D'):
            door_dir = int(lines[offset][1:])
            offset += 1
            door_desc, offset_add = parse_multi_line(lines[offset:])
            offset += offset_add
            door_keywords, offset_add = parse_multi_line(lines[offset:])
            offset += offset_add
            try:
                door_locks, door_key, door_to_room = lines[offset].split()
            except:
                log_error(f"Error parsing room {current_room.name} {vnum} line {offset}: {lines[offset]} - missing door info")
            offset += 1
            current_room.add_door(door_dir, door_desc, door_keywords, int(door_locks), int(door_key), int(door_to_room)) 
        elif lines[offset].startswith('E'):
            offset += 1
            ex_desc_keywords, offset_add = parse_multi_line(lines[offset:])
            offset += offset_add
            ex_desc_desc, offset_add = parse_multi_line(lines[offset:])
            offset += offset_add
            current_room.add_extended_description(ex_desc_keywords, ex_desc_desc)
    
    room_manager.add(vnum, current_room)

    
def parse_reset(line):
    line_index = 0
    mob_reset = None
    obj_reset = None
    while line_index < len(line):
        if line[line_index].startswith('S'):
            # shouldn't be reached but just to be safe
            return
        elif line[line_index].startswith('M'):
            split_line = line[line_index].split()[2:]
            mob_vnum, mob_count, mob_room_vnum, *mob_comment = split_line
            mob_vnum = int(mob_vnum)
            mob_count = int(mob_count)
            mob_room_vnum = int(mob_room_vnum)
            mob_comment = ' '.join(mob_comment) if mob_comment else ""

            mob_reset = ResetMob(mob_vnum, mob_count, mob_room_vnum, mob_comment)
            reset_manager.add_mob_reset(mob_reset)

            
        elif line[line_index].startswith('O'):
            split_line = line[line_index].split()[2:]
            obj_vnum, _, obj_room_vnum, *_ = split_line
            obj_vnum = int(obj_vnum)
            obj_room_vnum = int(obj_room_vnum)
            
            obj_reset = ResetObject(obj_vnum, obj_room_vnum)
            reset_manager.add_object_reset(obj_reset)
            
            pass
        elif line[line_index].startswith('P'):
            # handle 'P' case here
            pass
        elif line[line_index].startswith('G'):
            # Case G: give object to mob, format: G 1 5020 5                 (platinum wand)
            # The second number of the obj_vnum which is what we need
            # The object is given to the last mob_reset that was loaded
            obj_vnum = int(line[line_index].split()[2])
            if mob_reset == None:
                print(f"Reset: error loading obj {obj_vnum} to mob: no mob reset")
            else:
                mob_reset.add_item(obj_vnum)

        elif line[line_index].startswith('E'):
            # Case E: equip object to mob, format: E 1 3021 25 16             (short sword)
            split_line = line[line_index].split()
            obj_vnum = int(split_line[2])
            equip_slot = equip_number_to_slot(int(split_line[4]))
            
            if mob_reset == None:
                print(f"Reset: error loading obj {obj_vnum} to mob: no mob reset")
            else:
                mob_reset.equipment.equip(equip_slot, obj_vnum)
            
        elif line[line_index].startswith('D'):
            # handle 'D' case here
            pass
        elif line[line_index].startswith('R'):
            # handle 'R' case here
            pass
        elif line[line_index].startswith('*'):
            # comment line, just pass
            pass
        else:
            print("Unknown reset: ", line[line_index])
        line_index += 1
 
    
def parse_shops(line):
    pass 
    # print("Shops: ", line)
    
def parse_specials(line):
    pass 
    # print("Specials: ", line)

def parse_are_file(filename):
    with open(filename) as f:
        lines = f.readlines()
        
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line]

    STATE = None
    line_index = 0

    while line_index < len(lines):
        if STATE == None:      
            if lines[line_index].startswith('#'):
                STATE = lines[line_index][1:].split()[0]
                line_index += 1
            else:
                print("Not expected: ", lines[line_index])
                line_index += 1
        elif STATE == "AREA":
            Area = lines[line_index-1].replace('#AREA', '').strip()[:-1]
            print("\tArea: ", Area)
            STATE = None
        elif STATE == "HELPS":
            while lines[line_index].startswith('0 $~') == False:
                line_index += 1
            line_index += 1
            STATE = None
        elif STATE in ["MOBILES", "OBJECTS", "ROOMS"]:
            if lines[line_index].startswith('#'):
                if lines[line_index].startswith('#0'):
                    STATE = None
                    line_index += 1 
                else:
                    offset = 1
                    while lines[line_index+offset].startswith('#') == False:
                        offset += 1
                    parse_func = parse_mob if STATE == "MOBILES" else parse_object if STATE == "OBJECTS" else parse_room
                    parse_func(lines[line_index:line_index+offset])
                    line_index += offset
        elif STATE == "RESETS":
            # Resets pass the all section as a block on input to parse_reset
            offset = 0
            while lines[line_index+offset].startswith('S') == False:
                offset += 1
            parse_reset(lines[line_index:line_index+offset])
            line_index += offset + 1
            STATE = None
        elif STATE in ["SHOPS", "SPECIALS"]:
            # Shops and specials passes line by line to parse function
            if lines[line_index].startswith('S') or lines[line_index] == 0:
                STATE = None
                line_index += 1
            else:
                parse_func = parse_shops if STATE == "SHOPS" else parse_specials
                parse_func(lines[line_index])
                line_index += 1  
        elif STATE == "$":
            return

def load_area_files_list(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    are_files = [line.strip() for line in lines if line.strip() != '$']
    return are_files

def build_world():
    start_time = time.time()
    print("Building world...")
    area_list_path = 'world/area.lst'  # Update this path to your area.lst file location
    are_files = load_area_files_list(area_list_path)

    for are_file in are_files:
        full_path = f'world/{are_file}'  # Update the path as necessary
        print(f"\tLoading {full_path}...")
        parse_are_file(full_path)
    
    print(f"World built ({time.time() - start_time:.2f}s)")

def reset_world():
    print("Reset world...")
    
    for mob_reset in reset_manager.mob_resets:
        mob_template = mob_manager.get(mob_reset.mob_vnum)
        if mob_template is not None:
            room = room_manager.get(mob_reset.room_vnum)
            if room is not None:
                # todo later: review max_count
                # for i in range(mob_reset.max_count):
                mob = MobInstance(mob_template, mob_reset, room)
                
                if mob_reset.equipment:
                    for slot, obj_vnum in mob_reset.equipment.slots.items():
                        if obj_vnum != 0:
                            obj_template = object_manager.get(obj_vnum)
                            if obj_template is not None:
                                obj = ObjectInstance(obj_template)
                                object_instance_manager.add(obj)
                                mob.equipment.equip(slot, obj)
                if mob_reset.inventory:
                    for obj_vnum in mob_reset.inventory:
                        obj_template = object_manager.get(obj_vnum)
                        if obj_template is not None:
                            obj = ObjectInstance(obj_template)
                            object_instance_manager.add(obj)
                            mob.add_item(obj)
   
            else:
                print(f"Room {mob_reset.room_vnum} not found")
        else:
            print(f"Mob {mob_reset.mob_vnum} not found")

    for obj_reset in reset_manager.object_resets:
        obj_template = object_manager.get(obj_reset.obj_vnum)
        if obj_template is not None:
            room = room_manager.get(obj_reset.room_vnum)
            if room is not None:
                # check if obj is already in room
                add_obj = True
                for obj in room.object_list:
                    if obj.vnum == obj_reset.obj_vnum:
                        add_obj = False
                if add_obj:
                    obj = ObjectInstance(obj_template, obj_reset, room)
            else:
                print(f"Room {obj_reset.room_vnum} not found")
        else:
            print(f"Object {obj_reset.obj_vnum} not found")

def build_objects():
    start_time = time.time()
    object_instance_manager.load_objects()
    print(f"Objects loaded from database ({time.time() - start_time:.2f}s)")


if __name__ == '__main__':
    build_world()
    reset_world()
    build_objects()
