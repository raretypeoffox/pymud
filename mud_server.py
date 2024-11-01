# mud_sever.py

import time
import signal
import socket
import select

VERSION = "0.0.1"

from mud_comms import handle_new_client, handle_shutdown, handle_disconnection, handle_client_login, process_output
from mud_handler import handle_player
from mud_world import build_world, reset_world, build_objects
from mud_shared import log_info, log_error
from mud_combat import combat_loop
from mud_ticks import timed_events
from mud_gmcp import handle_gmcp_negotiation, handle_gmcp_message, send_gmcp_messages
from mud_gmcp import TELNET_WILL_SUPPORT, TELNET_WONT_SUPPORT, TELNET_GMCP_ASK_SUPPORTED, TELNET_GMCP_MSG_START
from mud_objects import player_manager
from mud_consts import BANLIST

from mud_shared import log_msg
def log_client_input(player, msg):
    print(f"{player.fd}: Received: {msg.rstrip()}")
    # remove the below later on
    if player.name:
        log_msg(f"[PLAYER]: {player.name}): {msg.rstrip()}")
    else:
        log_msg(f"[PLAYER]: {player.fd}): {msg.rstrip()}")   
        
import ipaddress

def load_ban_list():
    ban_list = []
    try:
        with open(BANLIST, 'r') as file:
            for line in file:
                ip = line.strip()  # Remove any leading/trailing whitespace
                try:
                    ipaddress.ip_address(ip)  # Check if it's a valid IP
                    ban_list.append(ip)
                except ValueError:
                    print(f"Ignoring invalid IP: {ip}")
    except FileNotFoundError:
        print("banlist.txt not found.")
    except Exception as e:
        print(f"Unexpected error while reading banlist.txt: {e}")
    return ban_list          

def start_server(port=4000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen()

    log_info(f"Server listening on port {port}")
    
    # Set up signal handler for SIGINT
    signal.signal(signal.SIGINT, shutdown_handler)

    game_loop(server_socket)
    
def game_loop(server_socket):
    ban_list = load_ban_list()
    
    while True:
        # Rebuild the list of sockets to monitor at the start of each loop iteration
        sockets = [server_socket] + [player.socket for player in player_manager.get_players()]

        # Use select to wait for data to be available on any socket
        ready_to_read, _, _ = select.select(sockets, [], [], 0)

        # First, read all data
        player_data = {}
        for sock in ready_to_read:
            if sock is server_socket:
                # If the server socket is ready to read, a new connection is available
                try:
                    client_sock, addr = server_socket.accept()
                    if addr[0] in ban_list:
                        log_info(f"Rejected connection from banned IP {addr}")
                        client_sock.close()
                        continue
                    client_sock.setblocking(False)  # Set to non-blocking mode
                    log_info(f"Accepted connection from {addr}")
                    handle_new_client(client_sock)
                    sockets.append(client_sock)  # Add the new socket to the list
                    client_sock.send(TELNET_GMCP_ASK_SUPPORTED) # Ask the client if they support GMCP
                except OSError as e:
                    log_error(f"OS error while accepting new connection: {e}")
                except socket.error as e:
                    log_error(f"Socket error while accepting new connection: {e}")
                except Exception as e:  # This will catch any other types of exceptions
                    log_error(f"Unexpected error while accepting new connection: {e}")
            else:
                # If a client socket is ready to read, data is available from the client
                player = player_manager.get(sock)
                if player:
                    try:
                        data = sock.recv(1024)
                        # print(str(data))
                        if data:
                            if data[:2] in [TELNET_WILL_SUPPORT, TELNET_WONT_SUPPORT]: #Client is letting us know if they support GMCP
                                handle_gmcp_negotiation(data, player)
                            elif data[:3] == TELNET_GMCP_MSG_START: #Client is sending us a GMCP message
                                handle_gmcp_message(data, player)
                            else:
                                msg = data.decode('utf-8')
                                player_data[player] = msg.split('\n')  # Split the message into commands
                    except ConnectionAbortedError:
                        handle_disconnection(player, "Connection aborted")
                        sockets.remove(sock)  # Remove the socket from the list
                    except ConnectionResetError:
                        handle_disconnection(player, "Connection reset by peer")
                        sockets.remove(sock)  # Remove the socket from the list
                    except BlockingIOError:
                        pass # No data received
                    except UnicodeDecodeError:
                        log_error(f"Received invalid data from player {player.fd}")
                    except socket.timeout:
                        log_error(f"Socket operation timed out for player {player.fd}")
                    except BrokenPipeError:
                        handle_disconnection(player, "Broken pipe")
                        sockets.remove(sock)  # Remove the socket from the list
                    except OSError as e:
                        log_error(f"OS error for player {player.fd}: {e}")
                        sockets.remove(sock)  # Remove the socket from the list
                    except socket.error as e:
                        log_error(f"Socket error while accepting new connection: {e}")
                    except Exception as e:  # This will catch any other types of exceptions
                        log_error(f"Unexpected error while reading player input: {e}\n{data}")

        # Then, process all data
        for player, commands in player_data.items():
            for command in commands:
                command = command.strip()  # Remove leading/trailing whitespace
                if command:  # Ignore empty commands
                    log_client_input(player, command)
                    if player.loggedin:
                        handle_player(player, command)
                    else:
                        handle_client_login(player, command)

        process_output()

        # Update game state
        update_game_state()
        
        # Send all GMCP messages
        send_gmcp_messages(player_manager.get_players(LoggedIn=True))

        # Sleep for a bit to control the loop's rate
        time.sleep(0.1)
        
def update_game_state():
    
    combat_loop()
    process_output()
    
    timed_events()
    process_output()


def shutdown_handler(signum, frame):
    handle_shutdown(signum, frame) 

def main():
    log_info(f"Booting up PyMud v{VERSION}...")
    build_world()
    reset_world()
    build_objects()
    start_server()

if __name__ == '__main__':
    main()


