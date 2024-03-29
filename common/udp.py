"""
File implementing a wrapper class for a UDP socket

Last Modification: Added automatic port assignment
Date of Modification: 16/11/2022 13:56
"""

import socket
from typing import Optional
from . import utils

class UDP:
    """
    Wrapper class for a UDP socket

    Arguments:

    localIP : String -> The IP to run the socket on
    localPort : int  -> The port to listen on. If not indicated, the OS picks a random available port
    bufferSize : int -> The size of the buffer for messages
    binding : bool   -> Whether or not to bind to the port
    """
    def __init__(self, localIP:str = utils.get_local_ip(), localPort:int = 0, timeout:Optional[float] = None, bufferSize:int = 1024, binding:bool = False):
        self.localIP = localIP
        self.localPort = localPort
        self.bufferSize = bufferSize
        self.serverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if timeout != None:
            self.serverSocket.settimeout(timeout)

        if binding:
            self.serverSocket.bind((self.localIP, self.localPort))


    def receive(self) -> tuple[bytes,str,int]:
        """
        Receive data
        If timeout is set, raises socket.timeout

        Returns:

        message : bytes                     -> The message received
        ip      : String                    -> The ip address of the sender
        port    : int                       -> The port the massage was sent in
        """
        bytesAddressPair = self.serverSocket.recvfrom(self.bufferSize)

        message = bytesAddressPair[0]
        ip, port = bytesAddressPair[1]

        return message, ip, port

    def send(self, message:str, ip:str, port:int) -> None:
        """
        Send data

        Arguments:

        message : bytes                    -> The message to send through the socket
        ip      : String                    -> The ip address to send the message to
        port    : int                       -> The port the massage is to be sent through
        """
        self.serverSocket.sendto(message, (ip, port))