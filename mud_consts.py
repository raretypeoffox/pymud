# mud_consts.py

from enum import Enum

SERVER_LOG = "server_log.txt"
MOTD_FILE = "config/motd.txt"

Greeting = """
                        /\\
                        ||
                        ||
                        ||
                        ||                                               ~-----~
                        ||                                            /===--  ---~~~
                        ||                   ;'                 /==~- --   -    ---~~~
                        ||                (/ ('              /=----         ~~_  --(  '
                        ||             ' / ;'             /=----               \__~
     '                ~==_=~          '('             ~-~~      ~~~~        ~~~--\~'
     \\\\                (c_\_        .i.             /~--    ~~~--   -~     (     '
      `\               (}| /       / : \           / ~~------~     ~~\   (
      \ '               ||/ \      |===|          /~/             ~~~ \ \(
      ``~\              ~~\  )~.~_ >._.< _~-~     |`_          ~~-~     )\\
       '-~                 {  /  ) \___/ (   \   |` ` _       ~~         '
       \ -~\                -<__/  -   -  L~ -;   \\\\    \ _ _/
       `` ~~=\                  {    :    }\ ,\    ||   _ :(
        \  ~~=\__                \ _/ \_ /  )  } _//   ( `|'
        ``    , ~\--~=\           \     /  / _/ / '    (   '
         \`    } ~ ~~ -~=\   _~_  / \ / \ )^ ( // :_  / '
         |    ,          _~-'   '~~__-_  / - |/     \ (
          \  ,_--_     _/              \_'---', -~ .   \\
           )/      /\ / /\   ,~,         \__ _}     \_  "~_
           ,      { ( _ )'} ~ - \_    ~\  (-:-)       "\   ~ 
                  /'' ''  )~ \~_ ~\   )->  \ :|    _,       " 
                 (\  _/)''} | \~_ ~  /~(   | :)   /          }
                <``  >;,,/  )= \~__ {{{ '  \ =(  ,   ,       ;
               {o_o }_/     |v  '~__  _    )-v|  "  :       ,"
               {/"\_)       {_/'  \~__ ~\_ \\\\_} '  {        /~\\
               ,/!          '_/    '~__ _-~ \_' :  '      ,"  ~ 
              (''`                  /,'~___~    | /     ,"  \ ~' 
             '/, )                 (-)  '~____~";     ,"     , }
           /,')                    / \         /  ,~-"       '~'
       (  ''/                     / ( '       /  /          '~'
    ~ ~  ,, /) ,                 (/( \)      ( -)          /~'
  (  ~~ )`  ~}                   '  \)'     _/ /           ~'
 { |) /`,--.(  }'                    '     (  /          /~'
(` ~ ( c|~~| `}   )                        '/:\         ,'
 ~ )/``) )) '|),                          (/ | \)                 -sjm
  (` (-~(( `~`'  )                        ' (/ '
   `~'    )'`')                              '
     ` ``

                **** Welcome to Mystic Realms! ****
                **** Based on PyMUD by Vagonuth ****

"""
           
DIRECTIONS = ["north", "east", "south", "west", "up", "down"]
DIRECTIONS_REVERSE = ["south", "west", "north", "east", "down", "up"]


RACE_MSG = """
Please choose from one of the following races:

[Cragkin]     Stone-skinned humanoids from mountainous regions, known for their
              incredible strength and ability to merge with rock and earth.

[Moonshades]  Nocturnal beings with a strong affinity to moonlight. They have
              enhanced night vision, silent movement and a knack for archery.

[Etherials]   Ghost-like beings that exist partially in another dimension, making them
              intangible and difficult to harm. They excel at hiding in the shadows.
              
[Starfolk]    Mysterious beings that come from the night sky, 
              their bodies resembling the starry heavens, with abilities tied to the cosmos.

[Frostlings]  Icy beings from the coldest parts of the world,
              capable of withstanding extreme cold and manipulating ice and snow.

[Aurorans]    Beings of pure light, they are the embodiment of goodness and purity,
              and are capable of great feats of healing and protection.

"""

# Race specific stats: str, dex, con, int, wis, cha, tnl, racials

RACES = {
  'Cragkin': [13, 11, 12, 10, 10, 10, 1000, ['merge']],
  'Moonshade': [10, 13, 11, 12, 10, 10, 1000, ['nightvision', 'silent']],
  'Etherial': [12, 13, 10, 11, 10, 10, 1000, ['ethereal', 'hide']],
  'Starfolk': [10, 10, 12, 13, 10, 11, 1000, ['starlight', 'heal']],
  'Frostling': [11, 10, 12, 13, 10, 10, 1000, ['blizzard', 'ice wall']],
  'Auroran': [10, 10, 12, 11, 13, 10, 1000, ['holy light', 'holy shield']]
}

RACES_ABV = {
  'Cragkin': 'Crag',
  'Moonshade': 'Moon',
  'Etherial': 'Ether',
  'Starfolk': 'Star',
  'Frostling': 'Frost',
  'Auroran': 'Auro'
}


ORIGIN_MSG = """
Please choose from one of the following origins:

1. [Warrior of the Forgotten Legion]  
    A descendant of an ancient and legendary army, known for their unmatched 
    battle prowess and endurance.
              
2. [Elemental Envoy]
    Born under a rare celestial alignment, naturally attuned to elemental 
    forces, giving them a natural proclivty towards elemental magic.

3. [Spiritual Wanderer]
    Travelled through sacred lands, gaining unique insights into the 
    spiritual world, enhancing their healing and protective spells.

4. [Shadow Guild Operative]
    Trained by an elusive and feared guild, adept in the arts of stealth, 
    thievery, and assassination. Live in the shadows.
    
5. [Borderland Sentinel]
    Guarded the frontiers of their homeland, adept in using a 
    bow for long-range defense and keenly aware of their surroundings.

6. [Wandering Bard]
    Travelled far and wide, collecting tales and skills from various 
    cultures, versatile in a range of practical and social abilities.

Enter 1-6 to choose an origin:
"""

ORIGINS = [
  "Warrior of the Forgotten Legion",
  "Elemental Envoy",
  "Spiritual Wanderer",
  "Shadow Guild Operative",
  "Borderland Sentinel",
  "Wandering Bard"
]

#define ITEM_TAKE		      1
#define ITEM_WEAR_FINGER	      2
#define ITEM_WEAR_NECK		      4
#define ITEM_WEAR_BODY		      8
#define ITEM_WEAR_HEAD		     16
#define ITEM_WEAR_LEGS		     32
#define ITEM_WEAR_FEET		     64
#define ITEM_WEAR_HANDS		    128 
#define ITEM_WEAR_ARMS		    256
#define ITEM_WEAR_SHIELD	    512
#define ITEM_WEAR_ABOUT		   1024 
#define ITEM_WEAR_WAIST		   2048
#define ITEM_WEAR_WRIST		   4096
#define ITEM_WIELD		   8192
#define ITEM_HOLD		  16384

EQ_SLOTS = {
  1: "<held in inventory>",
  2: "<worn on finger>",
  4: "<worn on neck>",
  8: "<worn on body>",
  16: "<worn on head>",
  32: "<worn on legs>",
  64: "<worn on feet>",
  128: "<worn on hands>",
  256: "<worn on arms>",
  512: "<held in offhand>",
  1024: "<worn about body>",
  2048: "<worn about waist>",
  4096: "<worn on wrist>",
  8192: "<wielded>",
  16384: "<held>"
}





  

#define ITEM_LIGHT		      1
#define ITEM_SCROLL		      2
#define ITEM_WAND		      3
#define ITEM_STAFF		      4
#define ITEM_WEAPON		      5
#define ITEM_TREASURE		      8
#define ITEM_ARMOR		      9
#define ITEM_POTION		     10
#define ITEM_FURNITURE		     12
#define ITEM_TRASH		     13
#define ITEM_CONTAINER		     15
#define ITEM_DRINK_CON		     17
#define ITEM_KEY		     18
#define ITEM_FOOD		     19
#define ITEM_MONEY		     20
#define ITEM_BOAT		     22
#define ITEM_CORPSE_NPC		     23
#define ITEM_CORPSE_PC		     24
#define ITEM_FOUNTAIN		     25
#define ITEM_PILL		     26



class BaseEnum(Enum):
    @classmethod
    def get_name_by_value(cls, value):
        for member in cls:
            if member.value == value:
                return member.name.lower()
        return None
      
class Exits(BaseEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    UP = 4
    DOWN = 5

class ObjState(BaseEnum):
  NORMAL = 0  # For standard reset items, won't save
  DROPPED = 1 # For items dropped on the ground, save but will imp after time
  INVENTORY = 2  # For items in inventory, will save
  LOCKER = 3  # For items in lockers, will save
  EQUIPPED = 4  # For items equipped, will save
  SPECIAL = 5  # For items that are special, will save (even if on ground) and not imp
  QUEST = 6  # For items that are quest items, will save (even if on ground) and not imp
  MAX = 7 # For checking if valid state, not a state itself (add new states above and increment max)  

class MobActFlags(BaseEnum):
    SENTINEL = 2
    SCAVENGER = 4
    AGGRESSIVE = 32
    WIMPY = 128 

class RoomFlags(BaseEnum):
    DARK = 1
    HAVEN = 2
    NO_MOB = 4
    INDOORS = 8
    PRIVATE = 512
    SAFE = 1024
    SOLITARY = 2048
    PET_SHOP = 4096
    NO_RECALL = 8192
  
class RoomSectorType(BaseEnum):
    INSIDE = 0
    CITY = 1
    FIELD = 2
    FOREST = 3
    HILLS = 4
    MOUNTAIN = 5
    WATER_SWIM = 6
    WATER_NOSWIM = 7
    BEACH = 8
    AIR = 9
    DESERT = 10
    
    
    
# Just for Fun

GOODBYE_MSGS = [
  "As you dissolve into a shimmering mist, the realm whispers its farewells. Until the winds of adventure bring you back, traveler.",
  "The ancient runes surrounding you glow softly, transporting you back to your realm. The world of legend awaits your return.",
  "A mystical eagle appears, lifting you into the skies. Your journey pauses as the lands below bid you a silent goodbye.",
  "With a wave of a wizard's staff, you fade from the land of myths. May your tales be told until you tread these paths again."
]


LOOK_SLEEPING_MSGS = [
  "As you try to look around, the world remains a hazy blur, the ethereal shapes and shadows of your dreams obscuring reality. You're still gripped by sleep, unable to discern the world around you.",
  "In your slumber, you reach out to observe your surroundings, but your senses are dulled by the tendrils of sleep. Vague images and indistinct sounds from your dream world mingle with reality, leaving you uncertain of what is real and what is not.",
  "You attempt to look around, but your eyes refuse to open, heavy with the weight of sleep. The darkness behind your eyelids offers no view, only the distant echoes of dreams still playing in your mind.",
  "Though you try to lift the veil of sleep to peek at your surroundings, the world outside remains elusive, hidden behind a fog of drowsiness. Your efforts to look are in vain, as you drift between consciousness and the realm of dreams.",
  "In your half-asleep state, you struggle to focus on your environment, but the details slip away like shadows in the night. The gentle pull of sleep holds you captive, blurring the lines between the waking world and the landscapes of your dreams.",
  "As you try to look around in your sleepy state, your mind wanders off, counting sheep. At sheep number 42, you realize you're still deep in the clutches of sleep, unable to perceive the world around you as the sheep continue their endless march through your dreams.",
  "As you try to look around, your vision blurs, and you find yourself standing in a moonlit glade. Ethereal creatures dance around you, their laughter like the tinkling of bells. A sense of peace fills you, but as you reach out to touch the dream, it dissipates like mist."
  "In your dream, you are soaring high above the clouds, the wind rushing past you as you glide over majestic mountains and emerald forests. You feel a sense of freedom and exhilaration, but as you try to look closer at the landscape below, the dream fades and you are gently pulled back to reality.",
  "You dream of wandering through an ancient, enchanted library, its endless shelves filled with mystical tomes and artifacts. Each book you open reveals a different realm or secret knowledge. However, as you try to focus on a particular volume, the words blur and the pages flutter away, leaving you in a serene state of sleep.",
  "In your slumber, you find yourself in a grand hall, feasting with legendary heroes and heroines of old. The air is filled with music and laughter, and tales of epic adventures are shared. Just as you raise a goblet in toast, the dream gently fades, and you sense you're still resting safely.",
  "In your dream, you find yourself floating in a starlit sky, surrounded by swirling galaxies and distant nebulas. Each star twinkles like a tiny eye, watching over you as you drift through the cosmic dance.",
  "In your dreams, you wander through an ethereal forest, where the trees are made of starlight and the ground sparkles like diamonds. You try to look around, but the scenery shifts and swirls, forever just out of reach.",
  "You find yourself in a grand, opulent ballroom, filled with masked dancers twirling in an endless waltz. You try to focus on their faces, but they blur and merge into one another, creating a mesmerizing but elusive spectacle.",
  "You are floating on a gentle river, the water clear as crystal, reflecting a sky filled with two moons. As you try to look around, the river carries you through changing landscapes, from lush jungles to snow-capped mountains, all blending seamlessly into each other."
  "You stand at the edge of a vast desert, the sands shifting colors from deep reds to golden yellows under a setting sun. As you try to look around, mirages form on the horizon, showing visions of ancient cities and forgotten civilizations, disappearing as quickly as they appear.",
  "You're soaring high above the clouds, the wind rushing past as you glide on magnificent, ethereal wings. You attempt to look down at the world below, but it shifts between fantastical landscapes - floating islands, towering castles, and mysterious, deep forests."
]   

NO_FIGHT_IN_SAFE_ROOM = [
  "You fumble groggily with the scroll, but your drowsy mind cannot comprehend the mystical runes. The words blur before your eyes as you drift back into the comforting embrace of sleep, the knowledge of the scroll remaining just out of reach in your slumbering state.",
  "As you prepare to strike, an invisible barrier of tranquility surrounds you, halting your actions. The sacred ground of this safe room negates all hostility, enforcing a peaceful coexistence.",
  "Your muscles tense, ready for a fight, but the air in the safe room hums with a serene energy, dousing your combative spirit like water on a flame. Here, conflict finds no foothold.",
  "You attempt to engage in combat, but a gentle yet firm force suppresses your aggressive intentions. In this sanctuary, peace reigns supreme, and all thoughts of violence are swiftly quelled.",
  "Eyes narrowing, you move to attack, but the serene aura of the safe room envelopes you, soothing your rage. A whisper in your mind urges restraint, reminding you that this place is a refuge from strife.",
  "As your hand balls into a fist, a soft, melodic chime fills the air, its vibrations easing the tension in your body. This safe room, a bastion of peace, allows no room for the chaos of battle." 
]
