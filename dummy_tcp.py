from socket import *
IP = '127.0.0.1'
PORT = 8081

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