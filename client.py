from socket import *
serverName = 'web.stanford.edu'
serverPort = 80
MAXBUF = 1024

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
requestMessage = "GET http://web.stanford.edu/class/cs224w/slides/01-intro.pdf HTTP/1.1\r\n"
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
    firstChunk = clientSocket.recv(MAXBUF)
    fragments.append(firstChunk)
    print(len(firstChunk))
    temp = firstChunk
    
    # print(chunk)
    if(temp.find(b'Content-Length') >= 0):
        posHeader = temp.find(b'Content-Length') + 15
        fileLen = int(temp[posHeader : temp.find(b'\r\n', posHeader)])
        print('fileLen: ', fileLen)
        offset = 0
        if temp.find(b'\r\n\r\n'):
            BodyBegin = temp.find(b'\r\n\r\n') + 4
            offset = len(firstChunk) - BodyBegin + 1
            if offset != fileLen:
                remain = (fileLen - offset)
                cntByteRecv = 0
                while cntByteRecv < remain:
                    chunk = clientSocket.recv(remain - cntByteRecv)
                    cntByteRecv += len(chunk)
                    fragments.append(chunk)
                    print('Downloading ', cntByteRecv / remain * 100, '%')
            print("Finish receiving data...")
            break
    elif (temp.find('transfer-encoding: chunked')):
        break

receiveMessage = b''.join(fragments)
# print("Data: ", receiveMessage)
receiveMessage = receiveMessage.split(b'\r\n\r\n')
headers = receiveMessage[0]
data = b''
for i in range(1, len(receiveMessage)):
    data += receiveMessage[i]
# f = open("example.html", "w")
# print(headers)
# print(data)
f = open("example.pdf", 'wb')
f.write(data)
# f.write(receiveMessage[receiveMessage.find('<') : ])
f.close()
clientSocket.close()