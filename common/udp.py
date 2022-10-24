import socket

class UDP:
    def __init__(self, localIP = "127.0.0.1", localPort = 4200, bufferSize = 1024, binding = False):
        self.localIP = localIP
        self.localPort = localPort
        self.bufferSize = bufferSize
        self.serverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        if binding:
            self.serverSocket.bind((self.localIP, self.localPort))


    def receive(self):
        bytesAddressPair = self.serverSocket.recvfrom(self.bufferSize)
        message = bytesAddressPair[0]

        address = bytesAddressPair[1]

        clientMsg = "Message from Client:{}".format(message)
        clientIP  = "Client IP Address:{}".format(address)
        
        print(clientMsg)
        print(clientIP)

        return message, address

    def send(self, message, address):
        self.serverSocket.sendto(message, address)