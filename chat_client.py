import socket
import threading
import json
import sys
from chatui import *

# Global Variables
host = sys.argv[1]
port = int(sys.argv[2])
nickname = sys.argv[3]
exit_flag = [False]  # Shared exit flag as a list


def listen_for_messages(sock, exit_flag):
    # Listen for messages from the server
    while not exit_flag[0]:
        message = sock.recv(1024).decode("utf-8")
        if message == "":
            # The server has closed the socket, exit the program
            exit_flag[0] = True
        print_message(message)


def send_messages(sock, exit_flag):
    # Send messages to the server
    while not exit_flag[0]:
        message = read_command(f'{nickname}> ')
        if message.startswith('/'):
            # Handle special commands
            if message == '/q':
                print_message("Exiting the chat. Goodbye!")
                exit_flag[0] = True
                # Turn into a json packet and send to server
                message_packet = {"type": "command", "command": "q"}
                message_packet = json.dumps(message_packet)
                sock.sendall(message_packet.encode("utf-8"))

            elif message.startswith('/online'):
                # Turn into a json packet and send to server
                message_packet = {"type": "command", "command": "online"}
                message_packet = json.dumps(message_packet)
                sock.sendall(message_packet.encode("utf-8"))

            else:
                print_message("Unknown command. Type '/q' to quit or '/online' to see who is online.")
        else:
            # Turn into a json packet
            message_packet = {"type": "chat", "text": message}
            message_packet = json.dumps(message_packet)
            sock.sendall(message_packet.encode("utf-8"))


# main
def main():
    # Create the socket
    sock = socket.socket()
    sock.connect((host, port))

    # create hello packet
    hello_packet = {"type": "hello", "nickname": nickname}

    # turn hello packet into json
    hello_packet = json.dumps(hello_packet)

    # send hello packet
    sock.sendall(hello_packet.encode("utf-8"))

    init_windows()

    # create a thread to listen for messages from the server
    listen_thread = threading.Thread(target=listen_for_messages, args=(sock, exit_flag), daemon=True)
    listen_thread.start()

    # create a thread to send messages to the server
    send_thread = threading.Thread(target=send_messages, args=(sock, exit_flag), daemon=True)
    send_thread.start()

    # Wait for the user to type '/q'
    while not exit_flag[0]:
        pass

    # Close the socket
    sock.close()

    end_windows()
    sys.exit(0)


if __name__ == "__main__":
    main()