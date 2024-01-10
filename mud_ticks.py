
import time
import random

from mud_comms import  player_manager
from mud_objects import mob_instance_manager


class TimeManager:
    def __init__(self):
        self.last_tick = time.time()
        self.tick_length = 30
    
    # tick length (in ms) is 30s +/- 2s (1 std dev)
    def update_tick_length(self):
        self.tick_length = random.normalvariate(30, 2) * 1000

    def next_tick(self):
        elapsed_time_ms = (time.time() - self.last_tick) * 1000
        if elapsed_time_ms > self.tick_length:
            self.last_tick = time.time()
            return True
        else:
            return False

time_manager = TimeManager()   

def tick_loop():
    if not time_manager.next_tick():
        return
    
    print("Tick!")
    for player in player_manager.get_players():
        player.character.tick()
    time_manager.update_tick_length()
    
    for mob in mob_instance_manager.get_mobs():
        mob.tick()