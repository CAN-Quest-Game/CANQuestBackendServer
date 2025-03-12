import threading

# Global variables
wiper_status = 0x00
status_lock = threading.Lock()
verbose = False
client_sock = None
server_socket = None
stop_can = threading.Event()
server_down = False