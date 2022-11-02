"""
File implementing the zone transfer protocol for both SS and SP

A zone transfer occurs between an SS and an SP via a TCP socket. A zone transfer always
refers to a single domain.

When the zone transfer begins, the SS will ask the SP for the version number of the database for
that domain. If the version is greater than the one the SS has in memory, it will begin the transfer
by asking how many entries the database has. The SP answers, the SS acknowledges the number of entries.
Then, the SP will send one segment per entry. When all segments are received by the SS, it will confirm 
having received everything. The SP will acknowledge this, terminating the zone transfer.

Last Modification: Documentation
Date of Modification: 02/11/2022 09:39
"""


import time
import socket
import sys
from common.dnsEntry import DNSEntry

#TODO: Handle errors (wrong status etc)
#TODO: Proper timeout
#TODO: Domain verification on acknowledgement
from server.zoneTransferPacket import SequenceNumber, ZoneTransferPacket, ZoneStatus

"""
Max zone transfer packet size in bytes
"""
maxSize = 1024

#TODO: Validate request
def processPacket(packet):
    """
    Given a packet an SP received from an SS, computes the packet(s) to send back
    in response. Auxiliary function for zoneTransferSP

    Arguments:

    packet : ZoneTransferPacket -> the packet received
    """
    if packet.sequenceNumber == SequenceNumber(0):
        return ZoneTransferPacket(SequenceNumber(1), ZoneStatus(0), 1)

    if packet.sequenceNumber == SequenceNumber(2):
        return ZoneTransferPacket(SequenceNumber(3), ZoneStatus(0), 1)


    if packet.sequenceNumber == SequenceNumber(4):
        return ZoneTransferPacket(SequenceNumber(5), ZoneStatus(0), (0,DNSEntry("ns1 CNAME batata 100 100", fromFile = True)))

    
    if packet.sequenceNumber == SequenceNumber(6):
        return ZoneTransferPacket(SequenceNumber(7), ZoneStatus(0), None)

def zoneTransferSP(localIP, port):
    """
    Function implementing the zone transfer protocol from the point of view of an
    SP.

    Arguments:
    
    localIP : String -> The IP where the TCP socket will be binded
    port    : int    -> The port to listen on
    """
    #Setup socket
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSocket.bind((localIP, port))
    tcpSocket.listen()

    try:
        #Run forever
        while True:
            (clientConnected, clientAddress) = tcpSocket.accept()
            print("Client address")

            for i in range(4):
                data = clientConnected.recv(maxSize)
                print(data.decode())
                packet = ZoneTransferPacket.from_str(data.decode())
                print(str(packet))
                response_packet = processPacket(packet)
                print(str(response_packet))
                clientConnected.send(str(response_packet).encode())

    finally:
        tcpSocket.close()


def getServerVersionNumber(tcpSocket, domain):
    """
    Queries the SP about the version number of the database of the given domain.
    Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket       -> the socket used to communicate with the SP
    domain : String -> the name of the domain to query about

    Returns:

    int : The version number of the database
    """
    sentPacket = ZoneTransferPacket(SequenceNumber(0), ZoneStatus(0), domain)
    tcpSocket.send(str(sentPacket).encode())
    data = tcpSocket.recv(maxSize)
    receivedPacket = ZoneTransferPacket.from_str(data.decode())
    return receivedPacket.data


def getDomainNumberEntries(tcpSocket, domain):
    """
    Queries the SP about the number of entries to expect for the given domain. Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket       -> the socket used to communicate with the SP
    domain : String -> the name of the domain to query about

    Returns:

    int : the number of entries to expect for the domain
    """
    sentPacket = ZoneTransferPacket(SequenceNumber(2), ZoneStatus(0), domain)
    tcpSocket.send(str(sentPacket).encode())
    data = tcpSocket.recv(maxSize)
    receivedPacket = ZoneTransferPacket.from_str(data.decode())
    return receivedPacket.data


def acknowledgeNumberEntries(tcpSocket, domain, entries):
    """
    Acknowledges the expected number of entries for a domain to the SP. Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket        -> the socket used to communicate with the SP
    domain : String  -> the name of the domain the number of entries refer to
    entries : int    -> the number of entries to expect
    """
    sentPacket = ZoneTransferPacket(SequenceNumber(4), ZoneStatus(0), (entries, domain))
    tcpSocket.sendall(str(sentPacket).encode())

def getAllEntries(tcpSocket, domain, entries):
    """
    Receives all entries for the given domain from the SP. Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket        -> the socket used to communicate with the SP
    domain  : String -> the name of the domain to get entries for
    entries : int    -> the number of entries to get
    """
    newEntries = {}
    for i in range(entries):
        data = tcpSocket.recv(maxSize)
        print(data.decode())
        receivedPacket = ZoneTransferPacket.from_str(data.decode())
        #TODO: Remove debug print
        

        order = int(receivedPacket.data[0])
        entry = receivedPacket.data[1]
        
        if (domain, entry.type) not in newEntries.keys():
            newEntries[(domain, entry.type)] = []
        
        newEntries[(domain, entry.type)].append(entry)
        
        #TODO: Replace entries


def confirmEntries(tcpSocket):
    """
    Confirms to the SP that it has received the expected number of entries. 
    Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket -> the socket used to communicate with the SP
    """
    sentPacket = ZoneTransferPacket(SequenceNumber(6), ZoneStatus(0), None)
    tcpSocket.sendall(str(sentPacket).encode())


def receiveEndOfTransfer(tcpSocket):
    """
    Receives the end of transfer packet from the SP. Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket -> the socket used to communicate with the SP
    """
    tcpSocket.recv(maxSize)

def zoneTransferSS(serverConfig):
    """
    Function implementing the zone transfer protocol from the point of view of an
    SS.

    Arguments:
    
    serverConfig : ServerConfig -> The configuration of the server
    """
    while True:
        for domain in serverConfig.primaryDomains:
            server_address = serverConfig.primaryDomains[domain]
            # Create a TCP/IP socket
            tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpSocket.connect(server_address)

            #try:
            versionNumber = getServerVersionNumber(tcpSocket, domain)

            #TODO: Check version Number
            if versionNumber < 0:
                continue
            
            numberEntries = getDomainNumberEntries(tcpSocket, domain)
            acknowledgeNumberEntries(tcpSocket, domain, numberEntries)
            
            getAllEntries(tcpSocket, domain, numberEntries)
            
            confirmEntries(tcpSocket)
            
            receiveEndOfTransfer(tcpSocket)
            #finally:
            #    print("Upsie")
            #    tcpSocket.close()

        time.sleep(10)