
#for while we're testing
from mud_world import build_world, reset_world
from mud_shared import log_info, log_error, dice_roll, random_percent


from mud_world import room_manager
from mud_objects import Player
import mud_consts



def one_hit(attacker, defender, type=0):
    
    # Make sure the attacker is alive, and the defender is alive
    # Make sure defender is in room
    
    # Figure out the type of damage message to send
    
    # Calculate to-hit roll
    
    hitroll = attacker.get_hitroll()
    armor_class = defender.get_AC()
    
    target_roll = armor_class - hitroll
        
    roll = dice_roll(1, 20, 0)
    
    if target_roll < 1:
        target_roll = 1 # dice roll of 1 will always miss
        
    # print(f"Target roll: {target_roll}, dice roll: {roll}")
    
    if roll > target_roll:
        damroll_dice, dam_roll_size, dam_roll_bonus = attacker.get_damroll()
        damage = dice_roll(damroll_dice, dam_roll_size, dam_roll_bonus)
        # print(f"Damage: {damage} / Damroll: {damroll_dice}d{dam_roll_size}+{dam_roll_bonus}")
        if roll == 20:
            damage += dice_roll(damroll_dice, dam_roll_size, dam_roll_bonus)
            msg = f"{attacker.name} scores a CRITICAL HIT on {defender.name} for {damage} damage!"
        else:
            msg = f"{attacker.name} hits {defender.name} for {damage} damage!"
        
        
        # Apply damage to defender
        # defender.apply_damage(damage)
        
    else:
        msg = f"{attacker.name} misses {defender.name}!"

    print(msg[0].upper() + msg[1:])
    
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
    
    # Inititive roll
    # later, change 2 to be a function of dexterity
    combatant_one_init = dice_roll(1, 20, 2)
    combatant_two_init = dice_roll(1, 20, 2)
    
    if combatant_one_init > combatant_two_init:
        # combatant_one goes first
        multi_hit(combatant_one, combatant_two)
        # if alive, combatant_two goes second
        multi_hit(combatant_two, combatant_one)
    else:
        # combatant_two goes first
        multi_hit(combatant_two, combatant_one)
        # if alive, combatant_one goes second
        multi_hit(combatant_one, combatant_two)


if __name__ == '__main__':
    build_world()
    reset_world()
    
    player = Player(0)
    player.name = "Xamur"
    player.character.race = "Cragkin"
    player.character.origin = mud_consts.ORIGINS[0]
    player.character.set_racial_stats(*mud_consts.RACES["Cragkin"])
    
    print(player.name)
    print(player.character)
    
    mob_list = room_manager.get_room_by_vnum(3710).get_mob_instances()
    mob = next(iter(mob_list))
    
    print(mob.name)
    
    print("=====================================\n")
    combat_round(player, mob)
