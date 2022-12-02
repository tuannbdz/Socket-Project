import socket
import sys
import os

MAXBUF = 2048
serverPort = 80

def clientConnect(serverName):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.settimeout(5)
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
                        chunk = clientSocket.recv(min(MAXBUF, remain - cntByteRecv))
                        cntByteRecv += len(chunk)
                        fragments.append(chunk)
                        print('Downloading ', round(cntByteRecv / remain * 100, 2) , '%')
                print("Finish receiving data...")
                break
        elif (temp.find(b'Transfer-Encoding: chunked')) >= 0:
            # print(firstChunk)
            temp = temp.split(b'\r\n\r\n')
            # header = temp[0]
            print(header.decode())
            chunkSize = temp[1].split(b'\r\n')[0]
            recvSize = len(firstChunk) - (len(header) + 4 + len(chunkSize) + 2)
            print(chunkSize, recvSize)
            # if recvSize >= chunkSize:
            
            # print(chunkSize)
            # while chunkSize != 0:
            sys.exit(0)
        else: break
    result = b''.join(fragments)
    return result

def writeData(receiveMessage, fileName):
    receiveMessage = receiveMessage.split(b'\r\n\r\n')
    headers = receiveMessage[0]
    data = b''
    for i in range(1, len(receiveMessage)):
        data += receiveMessage[i]
    # print(headers.decode())
    # print(data.decode())
    fileName = fileName.replace('%20', ' ')
    f = open(fileName, "wb")
    f.write(data)
    f.close()

def parseRequest(requestURL):
    if(requestURL[-1] != '/'):
        requestURL += '/'
    serverName = requestURL[requestURL.find('//') + 2 : requestURL.find('/', requestURL.find('//') + 2)]
    fileName = requestURL.split('/')[-2]
    if(fileName == serverName):
        fileName = 'index.html'
    isFolder = (fileName.find('.') == -1)
    requestURL = requestURL[:-1]
    return (serverName, fileName, isFolder)

def readSubFolder(clientSocket, recvMessage):
    queue = []
    data = recvMessage.split(b'\r\n\r\n')[1]
    for line in data.split(b'\n'):
        if(line.find(b'href=') >= 0):
            begPos = line.find(b'\"', line.find(b'href='))
            endPos = line.find(b'\"', begPos + 1)
            fileName = line[begPos + 1 : endPos]
            if(fileName.find(b'.') >= 0):
                queue.append(fileName)
    return queue


if __name__ == '__main__':
    requestURL = sys.argv[1]
    serverName, fileName, isFolder = parseRequest(requestURL)
    try:
        clientSocket = clientConnect(serverName)
        clientRequest(clientSocket, requestURL, serverName)
        receiveMessage = messageReceive(clientSocket)
        # print(receiveMessage.decode())
        # print('isFolder = ', isFolder   )
        if(isFolder == False):
            writeData(receiveMessage, serverName + '_' + fileName)
        else:
            folderName = serverName + '_' + fileName
            if(os.path.isdir(folderName) == False):
                os.mkdir(serverName + '_' + fileName)
            os.chdir(folderName)
            writeData(receiveMessage, 'index.html')
            URLqueue = readSubFolder(clientSocket, receiveMessage)
            for request in URLqueue:
                t = clientSocket.recv(1)
                clientRequest(clientSocket, requestURL + request.decode(), serverName)
                msg = messageReceive(clientSocket)
                writeData(msg, request.decode())

    except KeyboardInterrupt:
        clientSocket.close()
    # except:
    #     print('Connection error!')
    #     clientSocket.close()
    finally:
        clientSocket.close()