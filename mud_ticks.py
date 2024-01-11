
import time
import random

from mud_comms import  player_manager
from mud_objects import mob_instance_manager
from mud_handler import player_movement

class TimeManager:
    def __init__(self):
        self.last_tick = time.time()
        self.tick_length = 30
        
        self.last_mini_tick = time.time()
        self.mini_tick_length = 5
    
    # tick length (in ms) is 30s +/- 2s (1 std dev)
    def update_tick_length(self):
        self.tick_length = random.normalvariate(30, 2) * 1000
        
    def update_mini_tick_length(self):
        self.mini_tick_length = random.normalvariate(5, 0.5) * 1000

    def next_tick(self):
        elapsed_time_ms = (time.time() - self.last_tick) * 1000
        if elapsed_time_ms > self.tick_length:
            self.last_tick = time.time()
            return True
        else:
            return False
        
    def next_mini_tick(self):
        elapsed_time_ms = (time.time() - self.last_mini_tick) * 1000
        if elapsed_time_ms > self.mini_tick_length:
            self.last_mini_tick = time.time()
            return True
        else:
            return False

time_manager = TimeManager()   

def tick_loop():
    if not time_manager.next_tick():
        return
    
    time_manager.update_tick_length()
    
    for player in player_manager.get_players():
        player.character.tick()
    
    for mob in mob_instance_manager.get_all_instances():
        mob.character.tick()
        
    player_manager.save_all_players()
        
def mini_tick_loop():
    if not time_manager.next_mini_tick():
        return

    time_manager.update_mini_tick_length()
    
    # for non-sentinel mobs, small chance for them to move
    for mob in mob_instance_manager.get_all_instances():
        if mob.template.check_if_move():
            door = mob.current_room.choose_random_door()
            player_movement(mob, door)
            
    
    
    
        
        
        