"""
File implementing a simple wrapper for TCP sockets.

This wrapper will have a buffer, and will make sure that when
reading from the socket, only a single message will be returned, and
not partial messages. For example, in the buffer with "<Message 1><Message 2>",
a call to the API of the wrapper class would return "<Message 1>" instead of
"<Message1><Mess" or "Mess<"
"""
import socket
from typing import Callable


class TCPWrapper:
    """
    Wrapper class for TCP connections
    
    
    This wrapper will have a buffer, and will make sure that when
    reading from the socket, only a single message will be returned, and
    not partial messages. For example, in the buffer with "<Message 1><Message 2>",
    a call to the API of the wrapper class would return "<Message 1>" instead of
    "<Message1><Mess" or "Mess<"
    """
    def __init__(self, conn:socket, splitFunction:Callable, bufferSize:int, address:tuple[str,int] = None):
        """Default constructor

        Args:
            conn (socket): a TCP conn socket
            splitFunction (function): function used to split the messages.
            Must receive one argument - bytes - and return a tuple of bytes
            bufferSize (int): the number of bytes to read from the socket at once
        """
        self.conn = conn
        self.address = address
        self.splitFunction = splitFunction
        self.bufferSize = bufferSize
        self.buffer = "".encode()
        
    def read(self) -> bytes:
        """Returns the oldest message in the socket.
        
        There is no guarantee on the number of reads this method
        will perform on the socket. Can be none (if the message is
        in the buffer), or multiple (if the message is too big to
        big read all at once)

        Returns:
            bytes: the oldest message in the socket
        """
        result = self.splitFunction(self.buffer)
        message = result[0]
        buffer = result[1]
        
        if message is None:
            addedBuffer = self.conn.recv(self.bufferSize)
            
            # There is nothing more to read
            if addedBuffer == b'':
                return b''
            
            self.buffer = self.buffer + addedBuffer
            return self.read()
        
        self.buffer = buffer.encode()
        return message.encode()
    
    def write(self, message:bytes) -> None:
        """
        Writes the given message to the socket
        Args:
            message (bytes): the message to send
        """
        self.conn.sendall(message)
        
    def shutdown(self, mode:int) -> None:
        """shutdown the tcp socket

        Args:
            mode : the end of file to send to shutdown the socket
        """
        self.conn.shutdown(mode)
        
    def close(self) -> None:
        """
            closes the tcp socket
        """
        self.conn.close()