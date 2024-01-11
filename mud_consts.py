# mud_consts.py


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
           
           
MOTD = """Message of the day!\n\n"""

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

# Tried DND style but too high of variance between races
# RACES = {
#   'Cragkin': [17, 12, 16, 10, 10, 9, 1000, ['merge']],
#   'Moonshades': [10, 17, 12, 13, 13, 14, 1000, ['nightvision', 'silent']],
#   'Etherials': [14, 17, 10, 13, 13, 10, 1000, ['ethereal', 'hide']],
#   'Starfolk': [8, 8, 12, 17, 16, 13, 1000, ['starlight', 'heal']],
#   'Frostlings': [12, 10, 12, 15, 16, 11, 1000, ['blizzard', 'ice wall']],
#   'Aurorans': [8, 8, 10, 16, 17, 12, 1000, ['holy light', 'holy shield']]
# }

# will try this instead: start with 10 in all stats, then add 3 to one, 2 to another, 1 to another
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

ACT_SENTINEL = 2		  # Stays in one room
ACT_SCAVENGER = 4		  # Picks up objects
ACT_UNUSED1 = 8		    # no longer used
ACT_UNUSED2 = 16		  # no longer used
ACT_AGGRESSIVE = 32		# Attacks PC's
ACT_WIMPY = 128		  # Flees when hurt

OBJ_STATE_NORMAL = 0  # For standard reset items, won't save
OBJ_STATE_DROPPED = 1 # For items dropped on the ground, save but will imp after time
OBJ_STATE_INVENTORY = 2  # For items in inventory, will save
OBJ_STATE_LOCKER = 3  # For items in lockers, will save
OBJ_STATE_EQUIPPED = 4  # For items equipped, will save
OBJ_STATE_SPECIAL = 5  # For items that are special, will save (even if on ground) and not imp
OBJ_STATE_QUEST = 6  # For items that are quest items, will save (even if on ground) and not imp

OBJ_STATE_MAX = 7 # For checking if valid state, not a state itself (add new states above and increment max)


DIR_NORTH = 0
DIR_EAST = 1
DIR_SOUTH = 2
DIR_WEST = 3
DIR_UP = 4
DIR_DOWN = 5

# Room sector flags
SECT_INSIDE = 0
SECT_CITY = 1
SECT_FIELD = 2
SECT_FOREST = 3
SECT_HILLS = 4
SECT_MOUNTAIN = 5
SECT_WATER_SWIM = 6
SECT_WATER_NOSWIM = 7
SECT_BEACH = 8
SECT_AIR = 9
SECT_DESERT = 10
