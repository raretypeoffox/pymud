import time

from mud_shared import log_info, log_error, dice_roll, random_percent, colourize


from mud_world import room_manager
from mud_comms import player_manager
import mud_consts

from mud_objects import CombatManager
combat_manager = CombatManager()

from mud_comms import send_message
# used for testing remove for full program
# def send_message(player, msg):
#     print(msg.rstrip())

def return_PC_and_NPC(character_one, character_two):
    if character_one.character.NPC is True:
        NPC = character_one
        PC = character_two
    elif character_two.character.NPC is True:
        NPC = character_two
        PC = character_one
    else:
        log_error("Unexpected result, two players compared!")
        return None
    return PC, NPC

def deal_damage(attacker, defender, damage, msg, type=0):
    
    PC, NPC = return_PC_and_NPC(attacker, defender)
    
    # Apply damage to defender
    defender.character.apply_damage(damage)
    
    if defender.character.is_dead():
        combat_manager.end_combat(attacker, defender)
        combat_manager.end_combat(defender, attacker)
        if defender == NPC:
            msg += f"{defender.name} is dead!\n"
            msg += PC.get_prompt()
        elif attacker == NPC:
            msg += f"You are dead!\n"
            
            # TODO PC Death
            msg += "\n\n\nYou are magically healed!"
            PC.character.current_hitpoints = PC.character.max_hitpoints
            msg += PC.get_prompt()
            
        else:
            log_error("Unexpected result, neither PC nor NPC!")
            return
            
    # do XP and advancement stuff here
    
    send_message(PC, msg)
    

def one_hit(attacker, defender, type=0):
    
    if attacker.character.is_dead() or defender.character.is_dead():
        return   
    
    # Make sure defender is in room
    
    # Figure out the type of damage message to send
    
    # Calculate to-hit roll
    
    hitroll = attacker.character.get_hitroll()
    armor_class = defender.character.get_AC()
    damage = 0
    target_roll = armor_class - hitroll
        
    roll = dice_roll(1, 20, 0)
    
    if target_roll < 1:
        target_roll = 1 # dice roll of 1 will always miss
        
    # print(f"Target roll: {target_roll}, dice roll: {roll}")
    
    if roll > target_roll:
        damroll_dice, dam_roll_size, dam_roll_bonus = attacker.character.get_damroll()
        damage = dice_roll(damroll_dice, dam_roll_size, dam_roll_bonus)
        # print(f"Damage: {damage} / Damroll: {damroll_dice}d{dam_roll_size}+{dam_roll_bonus}")
        if roll == 20:
            damage += dice_roll(damroll_dice, dam_roll_size, dam_roll_bonus)
            msg = f"{attacker.name} scores a CRITICAL HIT on {defender.name} for {damage} damage!\n"
        else:
            msg = f"{attacker.name} hits {defender.name} for {damage} damage!\n"
        
        if damage <= 0:
            damage = 1
   
    else:
        msg = f"{attacker.name} misses {defender.name}!\n"

    deal_damage(attacker, defender, damage, msg, type)
    
def multi_hit(attacker, defender, type=0):
    
    second_attack_chance = .50
    third_attack_chance = .25
    fourth_attack_chance = .125
    
    one_hit(attacker, defender, type)
        
    if random_percent() < second_attack_chance:
        one_hit(attacker, defender, type)

    if random_percent() < third_attack_chance:
        one_hit(attacker, defender, type)
        
    if random_percent() < fourth_attack_chance:
        one_hit(attacker, defender, type)

def combat_round(combatant_one, combatant_two):
        
    multi_hit(combatant_one, combatant_two)
       
    PC, NPC = return_PC_and_NPC(combatant_one, combatant_two)
    
    if PC.character.is_dead() or NPC.character.is_dead():
        return
    

def report_mob_health(PC, NPC):
    hp_pct = NPC.character.get_hp_pct()
    if hp_pct == 1:
        msg =  f"{NPC.name} is in full health!\n"
    elif hp_pct > .80:
        msg = f"{NPC.name} has some small wounds and bruises.\n"
    elif hp_pct > .50:
        msg = f"{NPC.name} has some big and nasty wounds.\n"
    elif hp_pct > .20:
        msg = f"{NPC.name} is bleeding profusely.\n"
    elif hp_pct > 0:
        msg = f"{NPC.name} is on the verge of death.\n"
    else:
        log_error("Combat round called with dead NPC!")
        
    send_message(PC, colourize(msg, "yellow"))


def test_kill_mob(player, mob):
    send_message(player, f"You attack {mob.name}!\n")
    combat_manager.start_combat(player, mob)
    combat_manager.start_combat(mob, player)




def combat_loop():
    
    if combat_manager.next_round() == False:
        return
    
    # First process all the combat hits
    for combatant in combat_manager.get_characters_in_combat():
        if combatant is None or combat_manager.get_current_target(combatant) is None:
            continue
        print(combatant.name, combat_manager.get_current_target(combatant).name)
        combat_round(combatant, combat_manager.get_current_target(combatant))
           
    # At the end of the round, send the mob's health and prompt to all players
    for combatant in combat_manager.get_characters_in_combat():
        if combatant is None or combat_manager.get_current_target(combatant) is None:
            continue
        if combatant.character.NPC is False:
            report_mob_health(combatant, combat_manager.get_current_target(combatant))
            send_message(combatant, combatant.get_prompt() + "\n")
            




