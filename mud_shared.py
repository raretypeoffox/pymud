# mud_shared.py

import random
from datetime import datetime

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

LOG = "log.txt"

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
    with open(LOG, "a") as f:
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
    
def match_keyword(keywords, user_input):
    ''' Attempts to match user input against a list of keywords.
    Returns the first match if found, otherwise returns None.
    '''
    if isinstance(keywords, list) == False:
        keywords = [keywords]
    
    user_input = user_input.lower()
    for keyword in keywords:
        print(keyword)
        if keyword.lower().startswith(user_input):
            return keyword
    return None

   