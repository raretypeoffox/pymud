import time

from mud_shared import log_info, log_error, dice_roll, random_percent, colourize, first_to_upper, report_mob_health

from mud_world import mob_instance_manager
from mud_comms import send_room_message_processing, send_message, send_room_message, send_prompt_to_room

from mud_objects import combat_manager



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

def process_mob_death(player, mob):
    mob.move_to_room(None)
    # todo add corpse
    
    mob_instance_manager.remove_mob_instance(mob)
    mob = None

def process_victory(player, mob_level):
    level_diff = player.character.level - mob_level
    
    if level_diff < 5:
        num_dice = 5 - level_diff
        
        # bonus num_dice for being under level 20
        if player.character.level < 20:
            low_level_bonus = (20 - player.character.level) // 2
        xp = dice_roll(num_dice, 10, ((num_dice + low_level_bonus) * 5))
    else:
        xp = 0
    
    send_message(player, colourize(f"You gain {xp} experience!\n","yellow"))
    gain_msg = player.character.gain_experience(xp)
    if gain_msg != "":
        # Level!
        send_message(player, colourize(gain_msg,"cyan"))
        
    send_message(player, player.get_prompt())

def deal_damage(attacker, defender, damage, msg, type=0):
    
    PC, NPC = return_PC_and_NPC(attacker, defender)
    
    # Apply damage to defender
    defender.character.apply_damage(damage)
    send_room_message_processing(attacker, defender, msg)
  
    
    if defender.character.is_dead():
        combat_manager.end_combat(attacker, defender)
        combat_manager.end_combat(defender, attacker)
        if defender == NPC:
            mob_level = NPC.character.level
            process_mob_death(PC, NPC)
            msg = colourize(f"{first_to_upper(defender.name)} is dead!!!\n", "yellow")
            send_room_message(PC.current_room, msg, prompt=False)
            send_prompt_to_room(PC.current_room, excluded_player=PC, newline=False)
            process_victory(PC, mob_level)
        elif attacker == NPC:

            # TODO PC Death
            send_room_message(PC.current_room, colourize(f"{PC.name} is dead!!!\n", "red"), excluded_player=PC, excluded_msg=colourize("You are dead!!!", "red"))
            send_message(PC, f"\n\n\nYou are magically healed!\n{PC.get_prompt()}")
            PC.character.current_hitpoints = PC.character.max_hitpoints
            return
        else:
            log_error("Unexpected result, neither PC nor NPC!")
            return
            
    
    
    

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
            msg = f"$A score$s a CRITICAL HIT on $D for {damage} damage!\n"
        else:
            msg = f"$A hit$s $D for {damage} damage!\n"
        
        if damage <= 0:
            damage = 1
   
    else:
        msg = f"$A miss$e$s $D!\n"

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

def combat_round(combatant_one, combatant_two, type=0):
        
    multi_hit(combatant_one, combatant_two, type)
     

def attempt_flee(combantant_one, combatant_two):
    # add random chance to flee
    if not combat_manager.in_combat(combantant_one):
        send_message(combantant_one, "You are not in combat!\n")
        return False
    
    flee_chance = 0.5
    if random_percent() < flee_chance:
        send_room_message(combantant_one, f"{combantant_one.name} flees in terror!\n")
        combat_manager.end_combat(combantant_one, combatant_two)
        combat_manager.end_combat(combatant_two, combantant_one)
        send_message(combantant_one, combantant_one.get_prompt())
        return True
    else:
        send_message(combantant_one, "You fail to flee!\n")
        return False
    

def test_kill_mob(player, mob):
    send_message(player, f"You attack {mob.name}!\n")
    combat_manager.start_combat(player, mob)
    combat_manager.start_combat(mob, player)
    combat_round(player, mob)
    send_message(player, report_mob_health(combat_manager.get_current_target(player)))

    send_prompt_to_room(player.current_room, excluded_player=player)


def combat_loop():
    
    if combat_manager.next_round() == False:
        return
    
    # First process all the combat hits
    for combatant in combat_manager.get_characters_in_combat():
        if combatant is None or combat_manager.get_current_target(combatant) is None:
            continue
        combat_round(combatant, combat_manager.get_current_target(combatant))
           
    # At the end of the round, send the mob's health and prompt to all players
    rooms_with_players = set()
    for combatant in combat_manager.get_characters_in_combat():
        if combatant is None or combat_manager.get_current_target(combatant) is None:
            continue
        if combatant.character.NPC is False:
            send_message(combatant, report_mob_health(combat_manager.get_current_target(combatant)))
            rooms_with_players.add(combatant.current_room)
    
    # Make sure even folks not in combat get a prompt after the combat round is over       
    for room in rooms_with_players:
        send_prompt_to_room(room)


