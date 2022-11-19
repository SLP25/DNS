"""
File implementing the zone transfer protocol for both SS and SP

A zone transfer occurs between an SS and an SP via a TCP socket. A zone transfer always
refers to a single domain.

When the zone transfer begins, the SS will ask the SP for the version number of the database for
that domain. If the version is greater than the one the SS has in memory, it will begin the transfer
by asking how many entries the database has. The SP answers, the SS acknowledges the number of entries.
Then, the SP will send one segment per entry. When all segments are received by the SS, it will confirm 
having received everything. The SP will acknowledge this, terminating the zone transfer.

Last Modification: Multiprocessing
Date of Modification: 19/11/2022 18:10
"""


import time
import socket
from common.tcpClient import TCPClient
from common.utils import decompose_address

#TODO: Handle errors (wrong status etc)
#TODO: Proper timeout
#TODO: Domain verification on acknowledgement
from server.zoneTransferPacket import SequenceNumber, ZoneTransferPacket, ZoneStatus

"""
Max zone transfer packet size in bytes
"""
maxSize = 1024

#TODO: Validate request
def processPacket(serverData, packet):
    """
    Given a packet an SP received from an SS, computes the packet(s) to send back
    in response. Auxiliary function for zoneTransferSP

    Arguments:

    serverData : ServerData -> the configuration of the server
    packet : ZoneTransferPacket -> the packet received
    """
    print(packet.data)
    domain = serverData.get_domain(packet.get_domain(), True) if packet.get_domain() else None
    entries = domain.database.entries if domain else None

    if packet.sequenceNumber == SequenceNumber(0):
        return [ZoneTransferPacket(SequenceNumber(1), ZoneStatus(0), 1)]

    if packet.sequenceNumber == SequenceNumber(2):
        return [ZoneTransferPacket(SequenceNumber(3), ZoneStatus(0), len(entries))]


    if packet.sequenceNumber == SequenceNumber(4):
        res = []
        for index, entry in enumerate(entries):
            res.append(ZoneTransferPacket(SequenceNumber(5), ZoneStatus(0), (index, entry)))
        return res

    
    if packet.sequenceNumber == SequenceNumber(6):
        return [ZoneTransferPacket(SequenceNumber(7), ZoneStatus(0), None)]

def zoneTransferSP(serverData, localIP, port):
    """
    Function implementing the zone transfer protocol from the point of view of an
    SP.

    Arguments:
    
    serverData : ServerData -> the configuration of the server
    localIP      : String       -> The IP where the TCP socket will be binded
    port         : int          -> The port to listen on
    """
    #Setup socket
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSocket.bind((localIP, port))
    tcpSocket.listen()

    try:
        #Run forever
        while True:
            clientConnected = TCPClient(tcpSocket.accept(), ZoneTransferPacket.split_messages, maxSize)

            #TODO: check if client is authorized (client_ip in serverData.get_domain(domain_name, True).authorizedSS)

            for i in range(4):
                data = clientConnected.read()
                packet = ZoneTransferPacket.from_str(data.decode())
                print(str(packet))
                response_packets = processPacket(serverData, packet)
                for response_packet in response_packets:
                    print(str(response_packet))
                    clientConnected.write(str(response_packet).encode())
                    time.sleep(1)

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
    tcpSocket.sendall(str(sentPacket).encode())
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
    tcpSocket.sendall(str(sentPacket).encode())
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
        receivedPacket = ZoneTransferPacket.from_str(data.decode())
        #TODO: Remove debug print
        

        order = int(receivedPacket.data[0])
        entry = receivedPacket.data[1]
        
        if (domain, entry.type) not in newEntries.keys():
            newEntries[(domain, entry.type)] = []
        
        newEntries[(domain, entry.type)].append(entry)
        
    #TODO: Replace entries
    print("====================================")
    for entry in newEntries:
        print(entry)
    print("====================================")


def confirmEntries(tcpSocket):
    """
    Confirms to the SP that it has received the expected number of entries. 
    Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket -> the socket used to communicate with the SP
    """
    sentPacket = ZoneTransferPacket(SequenceNumber(6), ZoneStatus(0), "")
    tcpSocket.sendall(str(sentPacket).encode())


def receiveEndOfTransfer(tcpSocket):
    """
    Receives the end of transfer packet from the SP. Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket -> the socket used to communicate with the SP
    """
    tcpSocket.recv(maxSize)

def zoneTransferSS(serverData):
    """
    Function implementing the zone transfer protocol from the point of view of an
    SS.

    Arguments:
    
    serverData : ServerData -> The configuration of the server
    """
    while True:
        #logger.log
        #TODO: One thread per domain
        for domain in serverData.get_secondary_domains():
            # Create a TCP/IP socket
            tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpSocket.connect(decompose_address(domain.primaryServer))

            print("INICIO")

            #try:
            versionNumber = getServerVersionNumber(tcpSocket, domain.name)
            print("VERSION NUMBER")
            #TODO: Check version Number
            if versionNumber < 0:
                continue
            numberEntries = getDomainNumberEntries(tcpSocket, domain.name)
            acknowledgeNumberEntries(tcpSocket, domain.name, numberEntries)
            print("Entries")
            getAllEntries(tcpSocket, domain.name, numberEntries)

            confirmEntries(tcpSocket)

            receiveEndOfTransfer(tcpSocket)
            print("End of zone transfer")
            #finally:
            #    print("Upsie")
            #    tcpSocket.close()

        time.sleep(10)