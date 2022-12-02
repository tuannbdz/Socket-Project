import socket
import sys
import os

MAXBUF = 8192
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
    dataChunks = []
    while True:
        firstChunk = clientSocket.recv(MAXBUF)
        rollingBuffer = firstChunk
        if(len(rollingBuffer) == 0):
            break
        if(rollingBuffer.find(b'Content-Length') >= 0):
            dataChunks.append(firstChunk)
            posHeader = rollingBuffer.find(b'Content-Length') + 15
            fileLen = int(rollingBuffer[posHeader : rollingBuffer.find(b'\r\n', posHeader)])
            print('fileLen: ', fileLen)
            offset = 0
            if rollingBuffer.find(b'\r\n\r\n'):
                BodyBegin = rollingBuffer.find(b'\r\n\r\n') + 4
                offset = len(firstChunk) - BodyBegin + 1
                if offset != fileLen:
                    remain = (fileLen - offset)
                    cntByteRecv = 0
                    while cntByteRecv < remain:
                        chunk = clientSocket.recv(min(2048, remain - cntByteRecv))
                        cntByteRecv += len(chunk)
                        dataChunks.append(chunk)
                        print('Downloading ', round(cntByteRecv / remain * 100, 2) , '%')
                print("Finish receiving data...")
                break
        elif (rollingBuffer.find(b'Transfer-Encoding: chunked')) >= 0:
            #append header
            dataChunks.append(rollingBuffer[:rollingBuffer.find(b'\r\n\r\n')] + b'\r\n\r\n')

            headerEndingPosition = rollingBuffer.find(b'\r\n\r\n') + len(b'\r\n\r\n')
            rollingBuffer = rollingBuffer[headerEndingPosition:]
            #get the position (actually the position just after the final bit of the size number) of the first chunk size number within the file
            chunkSizePosition = rollingBuffer.find(b'\r\n')
            #get the first chunk's size
            chunkSize = int(rollingBuffer[:chunkSizePosition].decode(), 16)
            #remove the size (also remove the following \r\n
            rollingBuffer = rollingBuffer[(chunkSizePosition + len(b'\r\n')):]
            print(chunkSize, rollingBuffer)
            while True:
                # the end message is encountered
                if chunkSize == 0:
                    break
                chunk = clientSocket.recv(2048)
                #append the chunk to the buffer
                rollingBuffer += chunk
                #if the buffer has now have the full chunk in question
                if len(rollingBuffer) >= chunkSize + 2:
                    while len(rollingBuffer) >= chunkSize + 2:
                        #append the whole chunk onto the data chunks
                        dataChunks.append(rollingBuffer[:chunkSize])
                        #remove the chunk from the buffer (along with the trailing \r\n)
                        rollingBuffer = rollingBuffer[(chunkSize + len(b'\r\n')):]
                        #if the chunk does not contain the next chunk size yet
                        while rollingBuffer.find(b'\r\n') == -1:
                            chunk = clientSocket.recv(1)
                            rollingBuffer += chunk
                        #get the position after the last bit of the next chunk size number
                        chunkSizePosition = rollingBuffer.find(b'\r\n')
                        #get the next chunk's size
                        chunkSize = int(rollingBuffer[:chunkSizePosition].decode(), 16)
                        if chunkSize == 0:
                            break
                        #remove the chunk size number (along with the \r\n) from the buffer
                        rollingBuffer = rollingBuffer[(chunkSizePosition + len(b'\r\n')):]
            break
        else: break
    result = b''.join(dataChunks)
    print(result)
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
