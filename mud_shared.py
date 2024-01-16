# mud_shared.py

import shlex
import random
import re
from datetime import datetime
from enum import Enum
import mud_consts

# Define some ANSI escape codes for colors
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BRIGHT_RED = "\033[1;31m"
BRIGHT_GREEN = "\033[1;32m"
BRIGHT_BLUE = "\033[1;34m"
BRIGHT_YELLOW = "\033[1;33m"
BRIGHT_MAGENTA = "\033[1;35m"
BRIGHT_CYAN = "\033[1;36m"
BRIGHT_WHITE = "\033[1;37m"
RESET = "\033[0m"



# in the future, log this to a file
def log_error(msg):
    print(f"{RED}ERROR: {WHITE}{msg}{RESET}")
    log_msg(msg)
    
def log_info(msg):
    print(f"{GREEN}INFO: {WHITE}{msg}{RESET}")
    log_msg(msg)
    
def log_msg(msg):
    msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + msg
    # open the log file in append mode
    with open(mud_consts.SERVER_LOG, "a") as f:
        f.write(msg + "\n")

    
    
def colourize(text, flag):
    # Todo: add a check to see if player has ANSI colour enabled
    if flag == "red":
        return f"{RED}{text}{RESET}"
    elif flag == "green":
        return f"{GREEN}{text}{RESET}"
    elif flag == "blue":
        return f"{BLUE}{text}{RESET}"
    elif flag == "yellow":
        return f"{YELLOW}{text}{RESET}"
    elif flag == "magenta":
        return f"{MAGENTA}{text}{RESET}"
    elif flag == "cyan":
        return f"{CYAN}{text}{RESET}"
    elif flag == "white":
        return f"{WHITE}{text}{RESET}"
    elif flag == "bright red":
        return f"{BRIGHT_RED}{text}{RESET}"
    elif flag == "bright green":
        return f"{BRIGHT_GREEN}{text}{RESET}"
    elif flag == "bright blue":
        return f"{BRIGHT_BLUE}{text}{RESET}"
    elif flag == "bright yellow":
        return f"{BRIGHT_YELLOW}{text}{RESET}"
    elif flag == "bright magenta":
        return f"{BRIGHT_MAGENTA}{text}{RESET}"
    elif flag == "bright cyan":
        return f"{BRIGHT_CYAN}{text}{RESET}"
    elif flag == "bright white":
        return f"{BRIGHT_WHITE}{text}{RESET}"
    else:
        return text
 
def read_motd() -> str:
    try:
        with open(mud_consts.MOTD_FILE, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "Welcome to the MUD!\n"   
  
def dice_roll(num: int, size: int, bonus: int) -> int:
    total = 0
    for i in range(num):
        total += random.randint(1, size)
    return total + bonus

def random_percent() -> int:
    return round(random.uniform(0,1), 4)

# Compile the regular expression once, faster performance per copilot
ansi_color_code_re = re.compile(r'\033\[\d+m')

def first_to_upper(s : str) -> str:
    # Split the string by the newline character
    lines = s.split('\n')

    # Process each line individually
    for i in range(len(lines)):
        # Find all ANSI color codes at the beginning of the line
        ansi_color_codes = ansi_color_code_re.findall(lines[i])
        
        # Get the color codes and the rest of the string
        color_codes = ''.join(ansi_color_codes)
        rest_of_string = lines[i][len(color_codes):]

        # Capitalize the first character of the rest of the string
        if rest_of_string:
            rest_of_string = rest_of_string[0].upper() + rest_of_string[1:]

        # Combine the color codes and the rest of the string
        lines[i] = color_codes + rest_of_string

    # Join the lines back together
    s = '\n'.join(lines)
    return s



def check_flag(flags, flag):
    '''
    Checks if a specific flag is set in a bitfield.

    This function performs a bitwise AND operation between the flags and the flag to check.
    It raises a ValueError if either flags or flag is not an integer, or if flag is not a power of 2.

    Parameters:
    flags (int): The bitfield of flags.
    flag (int or Enum): The specific flag to check. Must be a power of 2.

    Returns:
    bool: True if the flag is set in the bitfield, False otherwise.
    '''
    if not isinstance(flags, int):
        raise ValueError("Flags must be an integer.")
    
    if isinstance(flag, Enum):
        flag = flag.value
    elif not isinstance(flag, int):
        raise ValueError("Flag must be an integer or an Enum member.")
    
    if flag != 0 and ((flag & (flag - 1)) != 0):
        raise ValueError("Flag value must be a power of 2.")
    
    return bool(flags & flag)

def is_NPC(player):
    if player.character is None:
        return False
    elif player.character.NPC is True:
        return True
    else:
        return False
    
def is_PC(player):
    if player.character is None:
        return False
    elif player.character.NPC is False:
        return True
    else:
        return False
   
def report_mob_health(NPC):
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
        log_error("report_mob_health() called with dead NPC!")
    msg = colourize(first_to_upper(msg), "yellow")
    return msg

def process_keyword(keyword):
    keyword = keyword.lower()
    # Split the keyword into number and actual keyword if applicable
    number, keyword = (keyword.split('.', 1) + [None])[:2] if '.' in keyword else (None, keyword)
    number = int(number) - 1 if number is not None and number.isdigit() else None
    return keyword, number

def process_search_output(number, matches):
    if number is None and matches:
        return matches[0]
    elif number is not None and number < len(matches):
        return matches[number]
    else:
        return None
    
def search_items(items: set, keyword: str) -> object:
    '''
    Searches for items that match the given keyword.

    This function processes the keyword to separate a number and the actual keyword if applicable.
    It then creates a list of items that match the keyword, and returns the item corresponding to the number
    if provided, or the first match if no number is provided.

    Parameters:
    items (set): A set of items, each of with have a method for get_keywords() that returns a list of keywords.
    keyword (str): The keyword to search for. Can include a number followed by a dot at the start to specify a particular match.

    Returns:
    object: The item that matches the keyword and corresponds to the number if provided, or the first matchif no number is provided.
            Returns None if no matches are found or if the number is greater than the number of matches.
            
    Common usage:
    For search for players and mobs in the room:
        target = search_items((player.current_room.get_players() | player.current_room.get_mobs()), argument)
    
    For searching for keywords (eg for look):
        all_items = (room.get_players() | player.inventory.get_all() | room.get_mobs() | room.get_objects() | room.get_doors() | room.get_extended_descriptions())
        item = search_items(all_items, argument)
    '''
    if keyword == "":
        return None
    
    # Process the keyword
    processed_keyword, number = process_keyword(keyword.lower())

    # Create a list of matches
    matches = [item for item in items if any(kw.startswith(processed_keyword) for kw in item.get_keywords())]

    # Process the search output
    return process_search_output(number, matches)
    
def parse_argument(argument):
    '''
    Splits the input argument into two parts: the first argument and the remainder.

    This function understands quotes and apostrophes, preserving the content inside them as a single token.
    If the input argument is None or an empty string, both the first argument and the remainder are set to None.
    The remainder is set to None if there are no additional arguments.

    Parameters:
    argument (str): The input string to be split. Can be None or an empty string.

    Returns:
    tuple: A tuple containing two elements. The first element is the first argument from the input string,
           or None if the input is None or an empty string. The second element is the remainder of the input string,
           or None if there are no additional arguments or if the input is None or an empty string.
    '''
    
    if argument is None or argument == '':
        return None, None
    
    # Split the argument into tokens
    tokens = shlex.split(argument)

    # The first token is the first argument
    first = tokens[0] if tokens else None

    # If there are more tokens, the rest of them form the remainder
    remainder = ' '.join(tokens[1:]) if len(tokens) > 1 else None

    first = first.lower()
    remainder = remainder.lower() if remainder is not None else None

    return first, remainder
