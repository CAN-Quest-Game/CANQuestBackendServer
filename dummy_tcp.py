from socket import *
IP = '127.0.0.1'
#IP = '141.215.216.168'
PORT = 8080

socketClient = socket(AF_INET, SOCK_STREAM)
socketClient.connect((IP,PORT))
 

while True:
    data = socketClient.recv(1024).decode()
    print('\n' + f"Received from server: {data}" + '\n') #display to client 
    
    if "0x00" in data:
        socketClient.send("test".encode())

    if "SHUTDOWN" in data:
        break

socketClient.close()