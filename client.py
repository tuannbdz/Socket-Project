from socket import *
serverName = 'example.com'
serverPort = 80
MAXBUF = 1024
print('ok con de')
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
requestMessage = "GET /index.html HTTP/1.1\r\n"
connectionType = "Connection: keep-alive\r\n"
hostName = "Host: www." + serverName + "\r\n"
persistentConnectionType = "Transfer-Encoding: chunked\r\n"
# requestMessage += persistentConnectionType
requestMessage += hostName
requestMessage += connectionType
requestMessage += "\r\n"
clientSocket.settimeout(2)
print(requestMessage)
print("Connect successfully")
iResult = clientSocket.send(requestMessage.encode())
print("Byte send: ", iResult)
fragments = []
i = 10
while True:
    chunk = clientSocket.recv(MAXBUF)
    fragments.append(chunk)
    print(len(chunk))
    if len(chunk) == 0:
        break

    temp = chunk.decode().lower()
    if(temp.find('content-length') >= 0):
        posHeader = temp.find('content-length') + 15
        fileLen = int(temp[posHeader : temp.find('\r\n', posHeader)])
        print('fileLen: ', fileLen)
        offset = 0
        if temp.find('\r\n\r\n'):
            BodyBegin = temp.find('\r\n\r\n') + 4
            offset = len(chunk) - BodyBegin + 1
            if offset == fileLen:
                print("Finish receiving data...")
            else:
                remain = clientSocket.recv(fileLen - offset)
                fragments.append(remain)
            break
    elif (temp.find('transfer-encoding: chunked')):
        break

receiveMessage = b''.join(fragments)
# print("Data: ", receiveMessage)

f = open("example.html", "w")
f.write(receiveMessage.decode('latin-1'))
# f.write(receiveMessage[receiveMessage.find('<') : ])
f.close()
clientSocket.close()