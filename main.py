''' 
Filename: main.py
Author: CANQuest Team
Version: 1.0prod
Description: Main file for the CANQuest Backend Server. Sets up the TCP and socketCAN server, handles client connections, and manages CAN communication.
'''
import socket
import threading
import ipaddress
import argparse
import config
from can_handler import * 

def can_message_handler(can_handler, stop_can):
    '''
    Function to handle CAN messages. It runs in a separate thread and continuously receives messages from the CAN bus.
    Arguments: 
    - can_handler: instance of the CAN_Handler class.
    - stop_can: threading.Event object to signal when to stop the thread.
    '''
    while not stop_can.is_set():
        can_handler.recv_msg()

def client_handler(client_sock, can_handler, stop_can, verbose=config.verbose):
    ''' 
    Function to handle client connections. It runs in a separate thread and continuously receives messages from the client.
    Arguments:
    - client_sock: socket object for the client connection.
    - can_handler: instance of the CAN_Handler class.
    - stop_can: threading.Event object to signal when to stop the thread.
    - verbose: boolean flag to enable verbose output, taken from config.py
    '''
    try:
        while not stop_can.is_set():
            data = client_sock.recv(1024).decode()
            if not data:
                print ("\nClient Disconnected. Please re-connect.")
                config.server_socket.shutdown(0)
                config.server_down = True
                break

            if verbose: print('\n' + f"Received from client: {data}" + '\n')

    except Exception as e:
        print(f"Client Error: {e}")
        config.stop_can.set()

def main(verbose):
    '''Main function to start the server and handle client connections. It sets up the CAN bus and starts threads for handling CAN messages and client connections.'''
    try:
        can_handler = None
        print("Waiting for client connection...")
        while not config.stop_can.is_set(): #ensure the server lock is not set to send CAN messages
            config.client_sock, addr = config.server_socket.accept()
            print(f"Accepted connection from {addr}")   

            #setup the CAN bus
            can_handler = CAN_Handler(verbose=config.verbose)
            can_handler.setup()

            #start the CAN message handler thread
            can_thread = threading.Thread(target=can_message_handler, args=(can_handler, config.stop_can), daemon=True)
            can_thread.start()

            #start the wiper data broadcast thread
            wiper_thread = threading.Thread(target=can_handler.broadcast_wiper_data, daemon=True)
            wiper_thread.start() 

            #start the client handler thread
            client_thread = threading.Thread(target=client_handler, args=(config.client_sock, can_handler, config.stop_can), daemon=True)
            client_thread.start()

    except KeyboardInterrupt:
        print("\nServer shutdown")
    except Exception as e:
        if config.server_down == False:
            print(f"Server Error: {e}")
        else:
            print("Initiating server shutdown due to client shutdown.")
    finally:
        config.stop_can.set() #stop the CAN message handler thread first
        if can_handler:
            can_handler.shutdown()
        if config.client_sock:
            config.client_sock.close()
        if config.server_socket:
            config.server_socket.close()
        print("Server shutdown complete. Bye!")
        
if __name__ == '__main__':

    try: 
        # check for verbose setting
        parser = argparse.ArgumentParser(description='CANQuest Backend Server')
        parser.add_argument('-v', '--verbose', action='store_true')
        
        args = parser.parse_args()
        
        if args.verbose:
            print("Verbose mode enabled")
            config.verbose = True

        #print startup message
        print( "\n"
        " ██████╗ █████╗ ███╗   ██╗ ██████╗ ██╗   ██╗███████╗███████╗████████╗ \n"
        "██╔════╝██╔══██╗████╗  ██║██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝\n"
        "██║     ███████║██╔██╗ ██║██║   ██║██║   ██║█████╗  ███████╗   ██║   \n"
        "██║     ██╔══██║██║╚██╗██║██║▄▄ ██║██║   ██║██╔══╝  ╚════██║   ██║   \n"
        "╚██████╗██║  ██║██║ ╚████║╚██████╔╝╚██████╔╝███████╗███████║   ██║   \n"
        " ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝  \n"
        "--------------------------------------------------------------------\n"
        "Welcome to the CANQuest Backend Server v1.0!\n"
        "Have fun with your quests, but remember to be a ETHICAL hacker...\n"
        "To start, enter the IP address of your VM/device running this server.\n"
        "Then, enter that same IP address in the game interface.\n"
        "To exit the server, press Ctrl+C or Cmd+C at any time.\n"
        "--------------------------------------------------------------------\n")

        #connect to user-entered IP address
        user_ip = input("Enter your IP address: ").strip()           
        try:
            ipaddress.ip_address(user_ip)
        except ValueError:
            print("Error: Invalid IP address format. Please try again.")
            exit()

        IP = user_ip
        PORT = 8080

        #setup server socket connection
        try:
            config.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            config.server_socket.bind((IP, PORT))
            config.server_socket.listen(1)
            print(f"Server listening on {IP}:{PORT}")
        except Exception as e:
            print(f"Error: {e}, please restart the server.")
            exit()

        #execute main function
        main(config.verbose)

    except KeyboardInterrupt:
        print("\nQuest complete? We hope so...")