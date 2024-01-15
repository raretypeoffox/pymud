
# mud_spells.py

from dataclasses import dataclass
from enum import Enum

from mud_comms import send_message
from mud_shared import colourize, dice_roll, parse_argument, search_items, is_NPC, is_PC, log_error
from mud_combat import deal_damage
from mud_objects import combat_manager

  
def spell_magic_missile(caster, target, spell):
    
    level, sublevel = caster.character.abilities.get_level(spell.spell_name)
    
    num_dice = 4 + (caster.character.int - 10)
    dam_dice = 3 + sublevel
    damage = dice_roll(num_dice, dam_dice, caster.character.level + level)
    
    spell_msg = colourize(f"$A utter$s the words 'magic missile'!\n", "yellow")
    spell_msg += colourize(f"$A point$s at $D and a small missile of energy shoots out, dealing {damage} damage!\n", "magenta")

    deal_damage(caster, target, damage, spell_msg)
    
def spell_burning_hands(caster, target, spell):
    
    level, sublevel = caster.character.abilities.get_level(spell.spell_name)
    
    num_dice = 2 + (caster.character.int - 10) // 2
    dam_dice = 2 + sublevel
    
    damage = dice_roll(num_dice, dam_dice, caster.character.level + level)
    
    spell_msg = colourize(f"$A utter$s the words 'burning hands'!\n", "yellow")
    
    for mob in set(caster.current_room.get_mobs()):
        spell_msg += colourize(f"$A point$s at $D and a small flame shoots out, dealing {damage} damage!\n", "red")
        deal_damage(caster, mob, damage, spell_msg)
        spell_msg = ""

class TargetType(Enum):
    IGNORE = 1 # Spell chooses its own targets.
    CHAR_OFFENSIVE = 2 # Spell is offensive (starts combat).
    CHAR_DEFENSIVE = 3 # Spell is defensive (any char is legal).
    CHAR_SELF = 4 # Spell is personal-effect only.
    OBJ_INV = 5 # Spell is used on an object.
 
@dataclass
class Spell:
    spell_name: str
    spell_func: callable
    min_cast_level: int
    target_type: int
    can_cast_in_combat: bool = False
    can_cast_on_player: bool = False
    mana_cost: int = 25
    lag: int = 5
    msg_noun_dmg: str = ""
    msg_spell_off: str = ""

SPELLS = {
    "magic missile": Spell("magic missile", spell_magic_missile, 1, TargetType.CHAR_OFFENSIVE, True, False, 30, 5, "magic missile", ""),
    "burning hands": Spell("burning hands", spell_burning_hands, 1, TargetType.IGNORE, True, False, 30, 5, "burning hands", ""),
}    

# TODO: will be used to say the spell name and target
def say_spell(caster, spell_name, target):
    pass

# returns the target of the spell based on the spell target type
def do_cast_select_target(caster, spell_name, target_type, target_name, combat_target):
    
    if target_type == TargetType.CHAR_SELF:
        return caster
    elif target_type == TargetType.CHAR_OFFENSIVE:
        # In combat, no target: target = combat_target
        # otherwise, target = target_name
        # no target, return none

        target = search_items((caster.current_room.get_players() | caster.current_room.get_mobs()), target_name)

        # In combat, no target: target = combat_target
        if combat_manager.in_combat(caster) and target is None and combat_target is not None:
            return combat_target

        return target
    elif target_type == TargetType.CHAR_DEFENSIVE:
        # if no target_name is provided, cast on ourselves
        if target_name is None:
            return caster
        
        return search_items((caster.current_room.get_players() | caster.current_room.get_mobs()), target_name)

    elif target_type == TargetType.OBJ_INV:
        return search_items(caster.get_objects(), target_name)
    elif target_type == TargetType.IGNORE:
        return None
    else:
        log_error(f"Unknown target type {target_type} for spell {spell_name}!")
        return None

# our main casting function, what gets called when a player types 'cast'
def do_cast(caster, argument):
    
    # first we need to parse argument to get the spell name and target
    spell_name, target_name = parse_argument(argument)
    if target_name is None:
        target_name = ""

    # if the spell name is None or too short, then the user didn't provide a valid spell name
    if spell_name is None or len(spell_name) < 3:
        send_message(caster, "Cast what? Please provide at least 3 characters of the spell name.\n")
        return
    
    # position check to see if the caster is in the right position to cast the spell
    if caster.character.get_position() != 'Stand':
        send_message(caster, "You must be standing to cast a spell!\n")
        return

    # search the SPELLS dictionary for the user's spell name
    spell = None
    for spell_key in SPELLS:
        if spell_key.startswith(spell_name):
            spell = SPELLS[spell_key]
            break

    # check to see if spell_name is actually a spell
    if spell is None:
        send_message(caster, f"You've never heard of a {spell_name} spell!!\n")
        return
    
    if caster.character.abilities.has_ability(spell.spell_name) is False:
        send_message(caster, f"You don't know how to cast {spell.spell_name}!\n")
        return
    
    # returns None is not in combat
    combat_target = combat_manager.get_current_target(caster)
    
    if combat_target is not None and spell.can_cast_in_combat is False:
        send_message(caster, "You can't concentrate enough.\n")
        return
    
    # check to see if the caster has enough mana to cast the spell
    # TODO implement race mana cost modifiers
    if caster.character.current_mana < spell.mana_cost:
        send_message(caster, f"You don't have enough mana to cast {spell.spell_name}!\n")
        return
        
    # find our target
    target = do_cast_select_target(caster, spell.spell_name, spell.target_type, target_name, combat_target)
    if target is None and spell.target_type != TargetType.IGNORE:
        send_message(caster, "Cast at who?\n")
        return None
    
    # no pvp
    if is_PC(caster) and target is not None and is_PC(target) and spell.can_cast_on_player is False:
        send_message(caster, f"You can't cast {spell.spell_name} on a player!\n")
        return
    
    # if we're already in combat, disallow targetting others not in combat
    # if spell.target_type == TargetType.CHAR_OFFENSIVE and combat_manager.in_combat(caster) is True and combat_manager.is_in_combat_with(caster, target) == False:
    #     send_message(caster, "Finish this fight first!\n")
    #     return
    
    if not callable(spell.spell_func):
        log_error(f"Spell function for {spell.spell_name} is not callable!")
        return

    caster.character.current_mana -= spell.mana_cost
    spell.spell_func(caster, target, spell)
    send_message(caster, caster.character.abilities.used_ability(spell.spell_name))
    
    
# for reference: how diku / merc works

# "name", {min cast level by class}
# spell_func, target_type, position
# gsn address, slot, min_mana, beats (0.25 seconds)
# noun_damage, msg_off

# {
# "magic missile",	{  1, 37, 37, 37 },
# spell_magic_missile,	TargetType.CHAR_OFFENSIVE,	POS_FIGHTING,
# NULL,			SLOT(32),	15,	12,
# "magic missile",	"!Magic Missile!"
# },

# {
# "cure light",		{ 37,  1, 37, 37 },
# spell_cure_light,	TargetType.CHAR_DEFENSIVE,	POS_FIGHTING,
# NULL,			SLOT(16),	10,	12,
# "",			"!Cure Light!"
# },
