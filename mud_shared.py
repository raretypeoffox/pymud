# mud_shared.py

import random
import re
from datetime import datetime
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
    
  
def dice_roll(num, size, bonus):
    total = 0
    for i in range(num):
        total += random.randint(1, size)
    return total + bonus

def random_percent():
    return round(random.uniform(0,1), 4)

# Compile the regular expression once, faster performance per copilot
ansi_color_code_re = re.compile(r'\033\[\d+m')

def first_to_upper(s):
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
    ''' Checks if a flag is set in a bitfield.'''
    if not isinstance(flags, int) or not isinstance(flag, int):
        raise ValueError("Both flags and flag must be integers.")
    if flag != 0 and ((flag & (flag - 1)) != 0):
        raise ValueError("Flag must be a power of 2.")
    return bool(flags & flag)

def is_NPC(player):
    if player.character is None:
        return False
    elif player.character.NPC is True:
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
    
