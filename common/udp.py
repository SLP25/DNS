"""
File implementing a wrapper class for a UDP socket

Last Modification: Documentation
Date of Modification: 02/11/2022 09:40
"""

import socket

class UDP:
    """
    Wrapper class for a UDP socket

    Arguments:

    localIP : String -> The IP to run the socket on
    localPort : int  -> The port to listen on
    bufferSize : int -> The size of the buffer for messages
    binding : bool   -> Whether or not to bind to the port
    """
    def __init__(self, localIP = "127.0.0.1", localPort = 4200, bufferSize = 1024, binding = False):
        self.localIP = localIP
        self.localPort = localPort
        self.bufferSize = bufferSize
        self.serverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        if binding:
            self.serverSocket.bind((self.localIP, self.localPort))


    def receive(self):
        """
        Receive data

        Returns:

        message : bytes                     -> The message received
        address : (IP : String, port : int) -> The address of the sender
        """
        bytesAddressPair = self.serverSocket.recvfrom(self.bufferSize)
        message = bytesAddressPair[0]

        address = bytesAddressPair[1]

        clientMsg = "Message from Client:{}".format(message)
        clientIP  = "Client IP Address:{}".format(address)
        
        print(clientMsg)
        print(clientIP)

        return message, address

    def send(self, message, address):
        """
        Send data

        Arguments:

        message : bytes                    -> The message to send through the socket
        address : (IP : String, port: int) -> The address to send the message to
        """
        self.serverSocket.sendto(message, address)