from socket import *
serverName = "localhost"
serverPort = 80
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((serverName, serverPort))
serverSocket.listen(1)
print("Server connection OK")
try:
    while(1):
        connectionSocket, addr = serverSocket.accept()
        print("Client: ", addr)
        connectionSocket.close()
except KeyboardInterrupt:
    connectionSocket.close()
finally:
    connectionSocket.close()
 