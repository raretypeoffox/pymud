import time
from collections import deque

# Define command cooldowns (in seconds)
COMMAND_COOLDOWNS = {
    'north': 0.2, 'east': 0.2, 'south': 0.2, 'west': 0.2, 
    'up': 0.2, 'down': 0.2, 'cast': 5.0,
    # other commands...
    'chat': 0.0,  # Instant command
    'score': 0.0,  # Instant command
    # Add cooldowns for other commands...
}

def handle_player(player, msg):
    msg = msg.rstrip()
    parts = msg.split(' ', 1)
    command = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else ''

    if msg == '':
        return

    current_time = time.time()
    if command in COMMAND_COOLDOWNS:
        if hasattr(player, 'last_command_time') and (current_time - player.last_command_time) < COMMAND_COOLDOWNS[command]:
            # Player is still on cooldown, queue the command
            if not hasattr(player, 'command_queue'):
                player.command_queue = deque()
        # Check if the queue has reached its limit
        if len(player.command_queue) < 5:  # Adjust the limit as needed
            player.command_queue.append((command, argument))
        else:
            send_message(player, "Your command queue is full!\n")
        return

    # Check and process the next command in the queue if cooldown has expired
    if hasattr(player, 'command_queue') and player.command_queue:
        queued_command, queued_argument = player.command_queue.popleft()
        # Execute the queued command
        execute_command(player, queued_command, queued_argument)
        player.last_command_time = current_time
        return

    # Rest of your command handling logic...
    # ...

    # After successfully executing a command, update last command execution time
    if command in COMMAND_COOLDOWNS:
        player.last_command_time = current_time
