import queue
import json

from mud_shared import log_error, log_info
from mud_comms import handle_disconnection
from mud_consts import Exits, RoomSectorType

# Telnet constants - see https://tools.ietf.org/html/rfc854
TELNET_IAC = b'\xff'
TELNET_WILL = b'\xfb'
TELNET_WONT = b'\xfc'
TELNET_DO = b'\xfd'
TELNET_DONT = b'\xfe'
TELNET_SB = b'\xfa'
TELNET_SE = b'\xf0'
TELNET_GMCP = b'\xc9'

# Telnet commands, simplified to improvide code readability
TELNET_WILL_SUPPORT = TELNET_IAC + TELNET_WILL
TELNET_WONT_SUPPORT = TELNET_IAC + TELNET_WONT
TELNET_GMCP_ASK_SUPPORTED = TELNET_IAC + TELNET_DO + TELNET_GMCP
TELNET_GMCP_MSG_START = TELNET_IAC + TELNET_SB + TELNET_GMCP
TELNET_GMCP_MSG_END = TELNET_IAC + TELNET_SE

class PlayerGMCP:
    def __init__(self, player):
        self.player = player
        self.output_queue = queue.Queue()
        self.gmcp = True
        
    def queue_message(self, package, message, data):
        try:
            data_str = json.dumps(data)
            gmcp_msg = f"{package}.{message} {data_str}"
            gmcp_msg_bytes = gmcp_msg.encode('utf-8')
            telnet_cmd = TELNET_GMCP_MSG_START + gmcp_msg_bytes + TELNET_GMCP_MSG_END
            self.output_queue.put(telnet_cmd)
        except UnicodeEncodeError:
            log_error(f"Failed to encode message for player {self.fd}")
        except Exception as e:  # This will catch any other types of exceptions
            log_error(f"Unexpected error while adding GMCP message to output queue: {e}")
        
    def update_status(self):
        if self.player.loggedin is False:
            return
        status = {
            'ac': self.player.get_AC(),
            'alignment': self.player.character.alignment,
            'character_name': self.player.name,
            'class': "",
            'con': self.player.character.con,
            'dex': self.player.character.dex,
            'experience_tnl': self.player.character.tnl - self.player.character.xp,
            'experience_tnl_max': self.player.character.tnl,
            'gold': self.player.character.gold,
            'health': self.player.character.current_hitpoints,
            'health_max': self.player.character.max_hitpoints,
            'hitroll': self.player.get_hitroll(),
            'int': self.player.character.int,
            'level': self.player.character.level,
            'mana': self.player.character.current_mana,
            'mana_max': self.player.character.max_mana,
            # 'opponent_name'
            'race': self.player.character.race,
            # 'room_exits': self.current_room.get_exit_names(),
            'room_name': self.player.current_room.name,
            'str': self.player.character.str,
            'wis': self.player.character.wis
        }
        self.queue_message("Char", "Status", status)
    
        vitals = {
            'hp': self.player.character.current_hitpoints,
            'maxhp': self.player.character.max_hitpoints,
            'mp': self.player.character.current_mana,
            'maxmp': self.player.character.max_mana,
            'stamina': self.player.character.current_stamina,
            'maxstamina': self.player.character.max_stamina,
            'tnl': self.player.character.tnl - self.player.character.xp,
            'tnlmax': self.player.character.tnl
        }
        self.queue_message("Char", "Vitals", vitals)
           
    def get_room_info(self):
        room = self.player.current_room
        if room is None:
            log_error(f"PlayerGMCP: Player {self.player.name} has no current room!")
            return {}
                
        door_status = {}
        for door in room.door_list:
            door_status[Exits.get_name_by_value(door.door_number)] = "O" if door.locks == 0 else "C"
        
        room = {
            'details': {},
            'environment': RoomSectorType.get_name_by_value(room.sector_type),
            'exits': door_status,
            'name': room.name,
            'zone': room.area_number
        }
        return room
    
    def update_room(self):
        if self.player.loggedin is False:
            return

        self.queue_message("Room", "Info", self.get_room_info())
        
      
def handle_gmcp_negotiation(data, player):
    # print("handle_telnet", str(data[:3]), TELNET_IAC + TELNET_WILL)
    if data[:3] == TELNET_WILL_SUPPORT + TELNET_GMCP:  
        player.gmcp = PlayerGMCP(player)
        log_info(f"Player {player.fd} supports GMCP")
    elif data[:3] == TELNET_WONT_SUPPORT + TELNET_GMCP:  
        player.gmcp = None
        log_info(f"Player {player.fd} does not support GMCP")
        
    # optional - check for out telnet options here
        
def handle_gmcp_message(data, player):
    # Remove the IAC SB GMCP IAC SE bytes from the start and end of the message
    gmcp_msg = data[3:-2]

    # Decode the message from bytes to a string
    gmcp_msg_str = gmcp_msg.decode('utf-8')

    # Split the GMCP message into parts
    parts = gmcp_msg_str.split(' ', 2)

    # If the message contains data, parse it
    if len(parts) == 3:
        package, message, data_str = parts
        data = json.loads(data_str)
    elif len(parts) == 2:
        package, message = parts
        data = None
    else:
        package = parts[0]
        message = None
        data = None

    # Perform the appropriate action based on the package and message
    # ... not yet implemented ... TODO
    
    log_info(f"Received GMCP message from player {player.fd}: {package} {message} {data}")
    
def send_gmcp_messages(players):
    for player in players:
        if player.gmcp:
            while not player.gmcp.output_queue.empty():
                try:
                    # Get the next message from the queue
                    msg = player.gmcp.output_queue.get()

                    # Send the message
                    player.socket.send(msg)
                except (BrokenPipeError, OSError):
                    handle_disconnection(player)
                except Exception as e:  # This will catch any other types of exceptions
                    log_error(f"Unexpected error while sending GMCP message: {e}")
