# mud_sever.py

import time
import signal
import socket

VERSION = "0.0.1"

from mud_comms import handle_new_client, handle_shutdown, player_manager, handle_disconnection, handle_client_login
from mud_handler import handle_player
from mud_world import build_world, reset_world
from mud_shared import log_info, log_error

def log_client_input(player, msg):
    print(f"{player.fd}: Received: {msg.rstrip()}")              

def start_server(port=4000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen()

    log_info(f"Server listening on port {port}")
    
    # Set up signal handler for SIGINT
    signal.signal(signal.SIGINT, shutdown_handler)

    game_loop(server_socket)
           
def game_loop(server_socket):
    server_socket.settimeout(0.1)
    while True:
        # Accept new connections
        try:
            client_sock, addr = server_socket.accept()
            client_sock.setblocking(False)  # Set to non-blocking mode
            log_info(f"Accepted connection from {addr}")
            handle_new_client(client_sock)
        except socket.timeout:
            pass

        # Handle incoming messages
        for player in player_manager.get_players():
            try:
                data = player.socket.recv(1024)
                if data:
                    msg = data.decode('utf-8')
                    log_client_input(player, msg)
                    if player.loggedin:
                        handle_player(player, msg)
                    else:
                        handle_client_login(player, msg)
            except ConnectionAbortedError:
                handle_disconnection(player, "Connection aborted")
            except ConnectionResetError:
                handle_disconnection(player, "Connection reset by peer")
            except BlockingIOError:
                pass # No data received
        

        # Update game state
        update_game_state()

        # Sleep for a bit to control the loop's rate
        time.sleep(0.1)
        
def update_game_state():
    pass


def shutdown_handler(signum, frame):
    handle_shutdown(signum, frame)


def main():
    log_info(f"Booting up PyMud v{VERSION}...")
    build_world()
    reset_world()
    start_server()

if __name__ == '__main__':
    main()


