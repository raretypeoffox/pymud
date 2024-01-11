
import time
import random

from mud_comms import  player_manager, send_room_message
from mud_objects import mob_instance_manager, room_manager, object_instance_manager
from mud_shared import colourize, first_to_upper, log_error
from mud_handler import player_movement
import mud_consts

class TimeManager:
    def __init__(self):
        self.startup_time = time.time()
        
        self.last_tick = time.time()
        self.tick_length = 30
        self.ticks_elapsed = 0
        
        self.last_mini_tick = time.time()
        self.mini_tick_length = 5
        
        self.last_long_tick = time.time()
        self.long_tick_length = (60 * 15) # fixed 15 minutes
        self.long_ticks_elapsed = 0
        
        self.imp_list = set() # list of objects to imp

    # tick length (in ms) is 30s +/- 2s (1 std dev)
    def update_tick_length(self):
        self.tick_length = random.normalvariate(30, 2) * 1000
        
    def update_mini_tick_length(self):
        self.mini_tick_length = random.normalvariate(5, 0.5) * 1000

    def next_tick(self):
        elapsed_time_ms = (time.time() - self.last_tick) * 1000
        if elapsed_time_ms > self.tick_length:
            self.last_tick = time.time()
            self.update_tick_length()
            self.ticks_elapsed += 1
            return self.ticks_elapsed
        else:
            return 0
        
    def next_mini_tick(self):
        elapsed_time_ms = (time.time() - self.last_mini_tick) * 1000
        if elapsed_time_ms > self.mini_tick_length:
            self.last_mini_tick = time.time()
            self.update_mini_tick_length()
            return True
        else:
            return False
        
    def next_long_tick(self):
        elapsed_time_ms = (time.time() - self.last_long_tick) * 1000
        if elapsed_time_ms > self.long_tick_length:
            self.last_long_tick = time.time()
            self.long_ticks_elapsed += 1
            return self.long_ticks_elapsed
        else:
            return 0

time_manager = TimeManager()   

def tick_loop():
    if not time_manager.next_tick():
        return
    
    for player in player_manager.get_players():
        player.character.tick()
    
    for mob in mob_instance_manager.get_all_instances():
        mob.character.tick()
        
    player_manager.save_all_players() # maybe move to long tick loop?
    do_specials()
        
def mini_tick_loop():
    if not time_manager.next_mini_tick():
        return
    
    # for non-sentinel mobs, small chance for them to move
    for mob in mob_instance_manager.get_all_instances():
        if mob.template.check_if_move():
            door = mob.current_room.choose_random_door()
            player_movement(mob, door)
  
def long_tick_loop():
    if not time_manager.next_long_tick():
        return
    
    object_instance_manager.save_objects()          
    do_imp()
    
def do_imp():
    # first imp all the items that were added in the previous long_tick
    if len(time_manager.imp_list) > 0:
        for obj in time_manager.imp_list:
            if obj is not None and obj.state == mud_consts.OBJ_STATE_DROPPED and obj.insured == None:
                print(obj)
                if obj.location_instance is None:
                    log_error(f"Object {obj.name} has no location room instance but is ready to be imped")
                    continue
                send_room_message(obj.location_instance, f"{first_to_upper(obj.name)} disappears in a puff of smoke!\n")
                obj.imp()
                del obj
        time_manager.imp_list.clear()
    
    # then add all the items that will be imp'd in the next long_tick
    for obj in object_instance_manager.get_all_instances():
        if obj.state == mud_consts.OBJ_STATE_DROPPED and obj.insured == None:
            time_manager.imp_list.add(obj)
    
    
def do_specials():
    if time_manager.ticks_elapsed % 5 > 0:
        return
    
    send_room_message(room_manager.get_room_by_vnum(3001), colourize("You hear the waves crashing against the shore.", "blue"))
     
    
        
        
        