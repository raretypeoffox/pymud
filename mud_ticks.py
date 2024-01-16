# mud_ticks.py

import time
import random

from mud_comms import send_room_message
from mud_objects import player_manager, mob_instance_manager, room_manager, object_instance_manager, reset_manager
from mud_shared import colourize, first_to_upper, log_error, log_info
from mud_handler import player_movement
import mud_consts
from mud_consts import ObjState

class TimeManager:
    def __init__(self):
        self.startup_time = time.time()
        
        self.last_tick = time.time()
        self.tick_length = 30 * 1000
        self.ticks_elapsed = 0
        
        self.last_mini_tick = time.time()
        self.mini_tick_length = 5 * 1000
        
        self.last_checks = {}

    # tick length (in ms) is 30s +/- 2s (1 std dev)
    def update_tick_length(self):
        self.tick_length = random.normalvariate(30, 2) * 1000
        
    def update_mini_tick_length(self):
        self.mini_tick_length = random.normalvariate(5, 0.5) * 1000

    def next_tick(self, current_time):
        elapsed_time_ms = (current_time - self.last_tick) * 1000
        if elapsed_time_ms > self.tick_length:
            self.last_tick = current_time
            self.update_tick_length()
            self.ticks_elapsed += 1
            return self.ticks_elapsed
        else:
            return 0
        
    def next_mini_tick(self, current_time):
        elapsed_time_ms = (current_time - self.last_mini_tick) * 1000
        if elapsed_time_ms > self.mini_tick_length:
            self.last_mini_tick = current_time
            self.update_mini_tick_length()
            return True
        else:
            return False
        
    def check_length_has_passed(self, key, time_interval, current_time):
        """
        Check if the specified time interval has passed since the last check.
        'key' is a unique identifier for each interval check.
        'time_interval' is the length of time to check in seconds.
        """
        last_check_time = self.last_checks.get(key, self.startup_time)

        if current_time - last_check_time >= time_interval:
            self.last_checks[key] = current_time
            return True
        return False

class ImpManager: 
    def __init__(self):
        self.imp_list = set() # list of objects to imp

time_manager = TimeManager()   
imp_manager = ImpManager()

def tick_loop():
    for player in player_manager.get_players(LoggedIn=True):
        player.tick()
    
    for mob in mob_instance_manager.get_all():
        mob.tick()
        
    player_manager.save_all_players()
    do_specials()
     
def mini_tick_loop():           

    # for non-sentinel mobs, small chance for them to move
    for mob in mob_instance_manager.get_all():
        if mob.template.check_if_move():
            door = mob.current_room.choose_random_door()
            player_movement(mob, door)
   
def do_imp():
    # first imp all the items that were added in the previous long_tick
    if len(imp_manager.imp_list) > 0:
        for obj in imp_manager.imp_list:
            if obj is not None and obj.state == ObjState.DROPPED and obj.insured == None:
                if obj.location_type == 'room' and obj.location_instance is None:
                    if obj.location_instance is None:
                        log_error(f"Object {obj.name} has no location room instance but is ready to be imped (looking for room vnum {obj.location})")
                        continue
                    send_room_message(obj.location_instance, f"{first_to_upper(obj.name)} disappears in a puff of smoke!\n")
                if obj.location_type == 'player':
                    log_error(f"Object {obj.name} is attempting to be imp'd but is still on a player")
                    continue
                if obj.location_type == 'mob':
                    log_info(f"Object {obj.name} is on a mob and being imped")
                obj.imp()
                del obj
        imp_manager.imp_list.clear()
    
    # then add all the items that will be imp'd in the next long_tick
    for obj in object_instance_manager.get_all():
        if obj.state == ObjState.DROPPED and obj.insured == None:
            imp_manager.imp_list.add(obj)
    
    
def do_specials():
    # TODO turn this into a loaded file
    TICKS_SPECIAL = 5
    if time_manager.ticks_elapsed % TICKS_SPECIAL > 0:
        return
    
    send_room_message(room_manager.get(3001), colourize("You hear the waves crashing against the shore.\n", "blue"))
    send_room_message(room_manager.get(3008), colourize("A faint, echoing whisper seems to drift through the cave, as if the very walls are murmuring a secret to those who dare to listen closely.\n", "blue"))
    send_room_message(room_manager.get(3105), colourize("Soft, melodic sounds of water gently babbling over smooth stones fill the air, creating a soothing, tranquil ambiance.\n", "blue"))
    send_room_message(room_manager.get(3112), colourize("A low, rumbling grunt echoes through the gully, sending a shiver down your spine as it hints at the presence of a large creature nearby.\n", "red"))
    
    if time_manager.ticks_elapsed % (TICKS_SPECIAL * 3) == 0:
        send_room_message(room_manager.get(3103), colourize("A soft melody seems to drift through the leaves of the ancient oak, fading in and out like a whispered secret.\n", "blue"))
    elif time_manager.ticks_elapsed % (TICKS_SPECIAL * 2) == 0:
        send_room_message(room_manager.get(3103), colourize("For a moment, the wind through the ancient oak's branches carries a melody, harmonious and old as time itself.\n", "blue"))
    else:
        send_room_message(room_manager.get(3103), colourize("The rustling of the ancient oak's leaves briefly harmonizes into a melodic tune, as if nature itself is singing a forgotten song.\n", "blue"))
    

    
def timed_events():
    
    current_time = time.time()
    
    # we'll always return after a timed event, so we don't need to worry about
    # the game slowing down if we have a lot of events to process
    
    if time_manager.next_mini_tick(current_time):
        mini_tick_loop()
    
    if time_manager.next_tick(current_time):
        tick_loop()
    
    # simple 3 minutes reset on mobs and objects
    # later, will make it so it takes longer to reset if players in area
    if time_manager.check_length_has_passed('mob_reset', 60 * 3, current_time):
        reset_manager.process_repop_queue() # option to break out mobs and object reset timers
    
    if time_manager.check_length_has_passed('imp', 60 * 5, current_time):
        do_imp()
        
    if time_manager.check_length_has_passed('obj_save', 60 * 15, current_time):
        object_instance_manager.save_objects()

        
        
        