from socket import *
import sys

MAXBUF = 1024
serverPort = 80

def clientConnect(serverName):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    print("Connect successfully")
    return clientSocket

def clientRequest(clientSocket, requestURL, serverName):
    requestMessage = "GET " + requestURL + " HTTP/1.1\r\n"
    connectionType = "Connection: keep-alive\r\n"
    hostName = "Host: " + serverName + "\r\n"
    requestMessage += hostName
    requestMessage += connectionType
    requestMessage += "\r\n"
    clientSocket.settimeout(2)
    iResult = clientSocket.send(requestMessage.encode())
    print("Request message: ", requestMessage)
    print("Byte send: ", iResult)


def messageReceive(clientSocket):
    fragments = []
    while True:
        firstChunk = clientSocket.recv(MAXBUF)
        fragments.append(firstChunk)
        temp = firstChunk
        if(len(temp) == 0):
            break
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
        elif (temp.find(b'Transfer-Encoding: Chunked')) >= 0:
            break
    result = b''.join(fragments)
    return result

def writeData(receiveMessage, serverName, fileName):
    receiveMessage = receiveMessage.split(b'\r\n\r\n')
    headers = receiveMessage[0]
    data = b''
    for i in range(1, len(receiveMessage)):
        data += receiveMessage[i]
    print(headers)
    # print(data)
    f = open(serverName + '_' + fileName, "wb")
    f.write(data)
    f.close()

if __name__ == '__main__':
    requestURL = sys.argv[1]
    if(requestURL[-1] != '/'):
        requestURL += '/'
    serverName = requestURL[requestURL.find('//') + 2 : requestURL.find('/', requestURL.find('//') + 2)]
    fileName = requestURL.split('/')[-2]
    if(fileName == serverName):
        fileName = 'index.html'
    requestURL = requestURL[:-1]
    clientSocket = clientConnect(serverName)
    clientRequest(clientSocket, requestURL, serverName)
    receiveMessage = messageReceive(clientSocket)
    writeData(receiveMessage, serverName, fileName)
    clientSocket.close()