import socket
import select
import json
import sys

# Global Variables
clients = set()
client_dict = {}
client_buffers = {}
port = int(sys.argv[1])


'''
Handle new connection function 
- Accepts a socket, a set of clients, a dictionary of clients, and a dictionary of client buffers
- Receives a hello message from the client
- Adds the client to the clients set
- Adds the client to the client dictionary
- Adds the client to the client buffers dictionary
- Sends a welcome message to all clients 
'''
def handle_new_connection(sock, clients, client_dict, client_buffers):
    # A listening socket has detected a new connection - accept it
    client_socket, address = sock.accept()
    clients.add(client_socket)
    client_buffers[client_socket] = b""  # Initialize an empty buffer for the client

    data = client_socket.recv(1024)
    client_buffers[client_socket] += data

    # Process complete messages in the buffer
    while b"}" in client_buffers[client_socket]:
        # find the index of the closing bracket
        idx = client_buffers[client_socket].index(b"}")
        # extract the complete message
        complete_message = client_buffers[client_socket][:idx + 1]
        # remove the complete message from the buffer
        client_buffers[client_socket] = client_buffers[client_socket][idx + 2:]

    hello = json.loads(complete_message.decode("utf-8"))
    # map message to client in clients dictionary
    client_dict[client_socket] = hello

    # send welcome message to all clients
    for client in clients:
        try:
            client.sendall(f"*** {hello['nickname']} has joined the chat.".encode("utf-8"))
        except BrokenPipeError:
            # Handle the broken pipe error here
            pass


'''
Handle chat function
- Accepts a socket, data, a set of clients, a dictionary of clients, and a dictionary of client buffers
- Appends the received data to the client's buffer
- Processes complete messages in the buffer
- Extracts the complete message
- Processes the complete message
- Sends the message to all clients
- Calls handle_commands() if the message is a command
'''
def handle_chat(s, data, clients, client_dict, client_buffers):
    # Append the received data to the client's buffer
    client_buffers[s] += data

    # Process complete messages in the buffer
    while b"}" in client_buffers[s]:
        # find the index of the closing bracket
        idx = client_buffers[s].index(b"}")
        # extract the complete message
        complete_message = client_buffers[s][:idx + 1]
        # remove the complete message from the buffer
        client_buffers[s] = client_buffers[s][idx + 2:]
        # Process the complete_message
        message = json.loads(complete_message.decode("utf-8"))

        if message["type"] == "chat":
            # send message to all clients
            message_text = message['text']
            for client in clients:
                try:
                    client.sendall(f"{client_dict[s]['nickname']}: {message_text}".encode("utf-8"))
                except BrokenPipeError:
                    # Handle the broken pipe error here
                    pass
        elif message["type"] == "command":
            handle_commands(message["command"], s, clients, client_dict)
            break


'''
Handle disconnect function
- Accepts a socket, a set of clients, a dictionary of clients, and a dictionary of client buffers
- Closes the socket
- Removes the client from the clients set
- Sends a message to all clients that the client has disconnected
- Removes the client from the client dictionary and client buffers dictionary
'''
def handle_disconnect(s, clients, client_dict, client_buffers):
    # remove client from clients set
    s.close()
    clients.remove(s)
    # send message to all clients that client has disconnected
    for client in clients:
        try:
            client.sendall(f"*** {client_dict[s]['nickname']} has left the chat.".encode("utf-8"))
        except BrokenPipeError:
            # Handle the broken pipe error here
            pass
    # remove client from client_dict and client_buffers
    del client_dict[s]
    del client_buffers[s]


'''
Handle commands function
- Accepts a message, a socket, a set of clients, and a dictionary of clients
- If the message is 'online', sends a list of all clients to the client
- If the message is 'q', sends a message to all clients that the client has disconnected
- Closes the socket and removes the client from the client dictionary and client buffers dictionary
'''
def handle_commands(message, s, clients, client_dict):
    # Handle special commands
    if message.startswith('online'):
        s.sendall("*** Users online: ".encode("utf-8"))
        for client in client_dict:
            try:
                s.sendall(f"\n*** {client_dict[client]['nickname']}".encode("utf-8"))
            except BrokenPipeError:
                # Handle the broken pipe error here
                pass
    elif message.startswith('q'):
        # send message to all clients that client has disconnected
        for client in clients:
            try:
                client.sendall(f"*** {client_dict[s]['nickname']} has left the chat.".encode("utf-8"))
            except BrokenPipeError:
                # Handle the broken pipe error here
                pass
        # remove 
        # client from client_dict, client_buffers, and clients
        s.close()
        del client_dict[s]
        del client_buffers[s]
        clients.remove(s)
        

# main
def main():
    # Create the socket
    sock = socket.socket()
    sock.bind(("localhost", port))
    sock.listen()

    clients = {sock}

    # wait for connections
    while True:
        # wait for a socket to become readable
        readable, _, _ = select.select(clients, [], [])

        # loop through the readable sockets
        for s in readable:
            if s is sock:
                # A listening socket has detected a new connection - accept it
                handle_new_connection(sock, clients, client_dict, client_buffers)

            else:
                # See if a client socket has data for us
                data = s.recv(1024)
                if data:
                    # Handle the chat
                    handle_chat(s, data, clients, client_dict, client_buffers)
                else:
                    # No data - client has disconnected
                    handle_disconnect(s, clients, client_dict, client_buffers)


if __name__ == "__main__":
    main()