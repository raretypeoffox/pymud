# mud_abilities.py

import random
from enum import Enum

from mud_shared import log_error, colourize

SkillSpellLevels = [
    ("Novice", "The initial learning stage of the skill."),
    ("Initiate", "Basic understanding and control over the skill's effects."),
    ("Adept", "Enhanced efficiency and effectiveness in skill use."),
    ("Scholar", "Deep theoretical knowledge and practical skill in the skill."),
    ("Savant", "Advanced mastery over the nuances and minor details of the skill."),
    ("Expert", "Exceptional proficiency, able to modify and adapt the skill creatively."),
    ("Master", "Complete and total command over every aspect of the skill."),
    ("Archon", "The skill is used with legendary precision and power."),
    ("Ethereal", "The skill use transcends normal limits, reaching near-mythical levels."),
    ("Transcendent", "The highest level of mastery, where the skill is used with absolute perfection and extraordinary effects.")
]

SkillLevels = [
    ("Rookie", "Basic familiarity with the skill; still prone to mistakes."),
    ("Apprentice", "Gaining a better grasp, with improved execution."),
    ("Practitioner", "Competent and reliable use of the skill in typical situations."),
    ("Tactician", "Strategic application and greater control in skill deployment."),
    ("Artisan", "Skilled and artistic execution, showing flair and creativity."),
    ("Expert", "High proficiency, able to use the skill effectively under pressure."),
    ("Master", "Peak mastery, demonstrating near-flawless execution."),
    ("Veteran", "Seasoned and experienced, using the skill with intuitive ease."),
    ("Elite", "Elite level of skill, capable of extraordinary feats and tactics."),
    ("Legendary", "The pinnacle of skill mastery, renowned and respected far and wide.")
]

# could move to object instance via an extra flag from .are file
ScrollsAndSpellbooks = {
    3001: 'magic missile',
}

SpellTingleMessages = [
"A tingling sensation courses through your fingertips, a sign of your growing proficiency in the spell.",
"As you practice the spell, you notice the incantations coming more naturally to you, a clear sign of improvement.",
"You feel a subtle shift in your magical energy, indicating that your understanding of the spell is deepening.",
"The arcane symbols and gestures of the spell begin to resonate with you more clearly, a testament to your progress.",
"You sense a newfound clarity in your spellcasting, a small yet significant step towards mastering this spell."
]

SpellLevelMessages = [
"As you chant the final incantation, a surge of power courses through you. You have reached a new level of mastery in the spell!",
"The arcane words flow from you with newfound ease and potency. Your mastery of the spell has ascended to a higher level!",
"A burst of magical energy envelops you, signaling your advancement. You've achieved a deeper understanding and greater control of the spell.",
"With a triumphant flourish, you complete the spell, feeling the fabric of magic respond more keenly to your command. Your proficiency in the spell has greatly increased!",
"The spell's energies align perfectly with your will, a clear sign of your growing expertise. You have successfully advanced to the next level of mastery!"
]

SpellLevelMessagesByMastery =[
    ["",
     "",
     ""      
    ],
    
    [
    "You gain a clearer understanding of the spell, stepping confidently into the role of an Initiate.",
    "The spell's basics are now second nature to you, marking your advancement to an Initiate.",
    "Your control over the spell strengthens, solidifying your position as an Initiate."
    ],
    [
    "Your spellcasting grows more efficient, signaling your rise to the level of an Adept.",
    "You weave the spell with increased expertise, proudly stepping into the Adept stage.",
    "The spell flows from you with greater ease, a clear sign of your newfound Adept status."
    ],
    [
    "Your deep understanding of the spell's theory and practice elevates you to a Scholar.",
    "You meld theory with practice, ascending to the scholarly ranks in spellcasting.",
    "Insights into the spell's deeper mechanics come naturally to you, marking you as a true Scholar."
    ],
    [
    "You master the nuances of the spell, ascending to the level of a Savant.",
    "The spell's intricate details are now at your fingertips, defining you as a Savant.",
    "Your expertise extends to even the minor aspects of the spell, elevating you to a Savant."
    ],
    [
    "Your exceptional skill allows for creative adaptations of the spell, marking you as an Expert.",
    "You can now modify and adapt the spell in innovative ways, a true mark of an Expert.",
    "The spell bends to your will in unique forms, showcasing your expertise."
    ],
    [
    "You achieve total command over the spell, marking your ascension to a Master.",
    "Every aspect of the spell is under your control, a testament to your status as a Master.",
    "The spell is an extension of your will, a clear indication of your mastery."
    ],
    [
    "Your spellcasting reaches legendary precision and power, elevating you to an Archon.",
    "As an Archon, your spells are cast with an almost mythical prowess.",
    "Your mastery is the stuff of legends, firmly establishing you as an Archon."
    ],
    [
    "You transcend normal limits, your spellcasting now at the Ethereal level.",
    "The spell's effects are near-mythical, a clear mark of your Ethereal mastery.",
    "Your command of the spell defies belief, elevating you to an Ethereal level of mastery."
    ],
    [
    "You reach the pinnacle of spellcasting, achieving Transcendent mastery.",
    "Your spell use is absolute perfection, marking your status as Transcendent.",
    "The extraordinary effects of your spellcasting herald your new level: Transcendent."
    ]  
]



StudyMessages = [
    "As you study the intricate symbols and ancient script on the scroll, the words seem to lift off the page and imprint themselves in your mind.",
    "You unfurl the scroll, and its mysterious contents unravel before you. With each line you read, the spell's essence becomes clearer.",
    "The scroll's arcane language twists and turns before your eyes, but as you concentrate, its meaning becomes evident, weaving its magic into your memory.",
    "You pore over the scroll, deciphering its cryptic runes. Slowly, the spell's structure reveals itself, embedding its knowledge deep within your consciousness.",
    "The scroll's mystical glyphs glow faintly as you read, their ancient power seeping into your being, instilling you with a new magical understanding.",
    "As you absorb the scroll's contents, the words dance and shimmer on the parchment, forming a vivid mental image of the spell's invocation.",
    "The scroll whispers secrets of old as you study it, the magic within leaping forth to intertwine with your own arcane prowess.",
    "With each word you read from the scroll, the air around you crackles with energy, signaling the successful acquisition of a new spell.",
    "The ancient knowledge on the scroll unfolds in your mind like a blooming flower, its petals revealing the secrets of the spell.",
    "As you commit the scroll's contents to memory, a sense of empowerment washes over you. The spell's formula now seems as familiar as an old friend."
]

class AbilityType(Enum):
    SKILL = 0
    SPELL = 1
    # RACIAL = 3


class LearnedAbility:
    def __init__(self, name, ability_type, level=1, experience=0):
        self.name = name
        self.type = ability_type  # 'skill' or 'spell'
        self.level = level
        self.experience = experience
        self.is_locked = False  # Additional feature, for locking abilities under certain conditions

    def gain_experience(self, amount):
        if not self.is_locked:
            self.experience += amount
            level_up_message = self.check_level_up()

            # Calculate 20% of the experience required for the next level
            required_exp = self.calculate_required_exp()
            if self.experience >= required_exp * 0.2:
                return colourize(SpellTingleMessages[random.randint(0, len(SpellTingleMessages) - 1)] + "\n", "bright magenta")
            else:
                return level_up_message

    def check_level_up(self):
        # Define logic for leveling up
        # For example, experience required for each level could increase exponentially
        required_exp = self.calculate_required_exp()
        if self.experience >= required_exp:
            self.level += 1
            self.experience -= required_exp
            # Implement additional effects of leveling up (e.g., increase in power, new effects, etc.)
            
            level_up_message = SpellLevelMessages[random.randint(0, len(SpellLevelMessages) - 1)] + "\n"
            level_up_mastery_message = SpellLevelMessagesByMastery[self.level - 1][random.randint(0, len(SpellLevelMessagesByMastery[self.level - 1]) - 1)] + "\n"
            
            level_up_message = colourize(level_up_message, "bright cyan")
            level_up_mastery_message = colourize(level_up_mastery_message, "bright magenta")
            
            return level_up_message + level_up_mastery_message
        return ""

    def calculate_required_exp(self):
        return 100 * (self.level ** 2)

    def lock_ability(self):
        self.is_locked = True

    def unlock_ability(self):
        self.is_locked = False
        
    def get_ability_experience_level(self):
        if self.type == AbilityType.SKILL:
            exp_level = SkillLevels[self.level - 1][0]
        elif self.type == AbilityType.SPELL:
            exp_level = SkillSpellLevels[self.level - 1][0]
        else:
            log_error(f"Unknown ability type {self.type} for ability {self.name}!")
        
        exp_pct = self.experience / self.calculate_required_exp()
        
        # Calculate the number of asterisks to add
        num_asterisks = int(exp_pct * 5) + 1
        
        # Create a string with num_asterisks asterisks
        asterisks = '*' * num_asterisks
        
        # Append the asterisks to exp_level
        exp_level += ' [' + asterisks.ljust(5) + ']'
        
        # Align self.name to the left with a width of 20 characters
        name_str = self.name.ljust(20)
        
        ret_str = f"{name_str}{exp_level} {self.experience}"        
        return ret_str
    
    def get_level(self):
        # Calculate the required experience for the next level
        required_exp = self.calculate_required_exp()

        # Calculate the sublevel
        sublevel = self.experience // (required_exp * 0.2)

        # Add 1 to sublevel because sublevel starts from 1
        sublevel += 1

        # Ensure sublevel is not greater than 5
        sublevel = min(5, sublevel)

        return self.level, int(sublevel)
        
class Abilities:
    def __init__(self):
        self.abilities = {}

    def learn_ability(self, ability_name, ability_type):
        if ability_name not in self.abilities:
            self.abilities[ability_name] = LearnedAbility(ability_name, ability_type)
            return StudyMessages[random.randint(0, len(StudyMessages) - 1)]

    def has_ability(self, ability_name):
        return ability_name in self.abilities

    def used_ability(self, ability_name):
        if ability_name in self.abilities:

            # chance to gain 1 extra experience
            if random.random() <= 0.25:
                return self.abilities[ability_name].gain_experience(10)
            return ""
                
    def list_spells(self):
        spell_list = []
        for ability in self.abilities.values():
            if ability.type == AbilityType.SPELL:
                spell_list.append(ability.get_ability_experience_level())
        if spell_list == []:
            ret_str = "You have not learned any spells yet.\n"
        else:
            ret_str = "You have learned the following spells:\n"
            ret_str += '\n'.join(spell_list)
            ret_str += '\n'

        return ret_str
    
    def get_level(self, ability_name):
        if ability_name in self.abilities:
            return self.abilities[ability_name].get_level()
        else:
            return 0, 0




