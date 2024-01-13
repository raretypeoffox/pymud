
# mud_spells.py

from mud_comms import send_message, send_room_message, send_room_message_processing
from mud_shared import first_to_upper, colourize, dice_roll
from mud_combat import deal_damage
from mud_objects import combat_manager




def spell_magic_missile(caster, target):
    
    caster.character.current_mana -= 30
    
    num_dice = 4 + (caster.character.int - 10)
    
    damage = dice_roll(num_dice, 4, caster.character.level)
    
    
    spell_msg = colourize(f"$A utter$s the words 'magic missile'!\n", "yellow")
    spell_msg += colourize(f"$A point$s at $D and a small missile of energy shoots out, dealing {damage} damage!\n", "magenta")

    deal_damage(caster, target, damage, spell_msg)
    
  






def do_cast(caster, target=None):
    
    
    if caster.character.current_mana < 30:
        send_message(caster, "You don't have enough mana to cast a spell!\n")
        return
    
    if combat_manager.in_combat(caster) is True:
        target = combat_manager.get_current_target(caster)
        
    if target is None:
        send_message(caster, "Cast at who?\n")
        return
    
    spell_magic_missile(caster, target)