from can_handler import *
import socket
import threading

def main():
    can_handler = CAN_Handler()
    can_handler.setup()
    while True:
        threading.Thread(target=can_handler.broadcast_wiper_data, daemon=True).start()
        can_handler.recv_msg()


       # can_handler.listener()
        
if __name__ == '__main__':
    IP = '127.0.0.1'
    PORT = 8080
    wiper_status = 0x00
    status_lock = threading.Lock()


    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen(1)
    print(f"Server listening on {IP}:{PORT}")
    while True:
        try:
            client_sock, addr = server_socket.accept()
            print(f"Accepted connection from {addr}")
            main()
            break
        except Exception as e:
            print(f"Error: {e}")
            print("retrying...")