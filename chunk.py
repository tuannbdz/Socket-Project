from socket import *

serverName = 'google.com'
serverPort = 80
serverAddress = (serverName, serverPort)
maxBuffer = 1024

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(serverAddress)

requestLine = 'GET http://www.httpwatch.com/httpgallery/chunked/chunkedimage.aspx HTTP/1.1\r\n'
hostNameLine = 'Host: www.httpwatch.com' + serverName + '\r\n'
connectionTypeLine = 'Connection: keep-alive\r\n'

requestMessage = requestLine + hostNameLine + connectionTypeLine + '\r\n'
clientSocket.send(requestMessage.encode())

#là fragments
dataChunks = []
rollingBuffer = bytearray

#get the first chunk (just to get the data types initialization for rollingBuffer to use the .find() function)
chunk = clientSocket.recv(maxBuffer)
rollingBuffer = chunk

#get all of the header
while rollingBuffer.find(b'\r\n\r\n') == -1:
    chunk = clientSocket.recv(maxBuffer)
    rollingBuffer += chunk

#remove header
headerEndingPosition = rollingBuffer.find(b'\r\n\r\n') + len(b'\r\n\r\n')
rollingBuffer = rollingBuffer[headerEndingPosition:]

#get the position (actually the position just after the final bit of the size number) of the first chunk size number within the file
chunkSizePosition = rollingBuffer.find(b'\r\n')

#get the first chunk's size
chunkSize = int(rollingBuffer[:chunkSizePosition].decode(), 16)
#remove the size (also remove the following \r\n
rollingBuffer = rollingBuffer[(chunkSizePosition + len(b'\r\n')):]

while True:
    # the end message is encountered
    if chunkSize == 0:
        break
    chunk = clientSocket.recv(maxBuffer)
    #append the chunk to the buffer
    rollingBuffer += chunk
    #if the buffer has now have the full chunk in question
    if len(rollingBuffer) >= chunkSize + 2:
        #append the whole chunk onto the data chunks
        dataChunks.append(rollingBuffer[:chunkSize])
        #remove the chunk from the buffer (along with the trailing \r\n)
        rollingBuffer = rollingBuffer[(chunkSize + len(b'\r\n')):]
        #get the position after the last bit of the next chunk size number
        chunkSizePosition = rollingBuffer.find(b'\r\n')
        #get the next chunk's size
        chunkSize = int(rollingBuffer[:chunkSizePosition].decode(), 16)
        #remove the chunk size number (along with the \r\n) from the buffer
        rollingBuffer = rollingBuffer[(chunkSizePosition + len(b'\r\n')):]

receivedData = b''.join(dataChunks)

file = open('example.html', 'w')
file.write(receivedData.decode('ISO-8859-1'))
file.close()

clientSocket.close()