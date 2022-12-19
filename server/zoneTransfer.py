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


from queue import Queue
import threading
import time
import socket
from common.tcpWrapper import TCPWrapper
import common.utils as utils
from common.logger import LogMessage, LoggingEntryType
from server.domain import Domain
from server.serverData import ServerData

#TODO: Handle errors (wrong status etc)
#TODO: Proper timeout
#TODO: Domain verification on acknowledgement
from server.zoneTransferPacket import SequenceNumber, ZoneTransferPacket, ZoneStatus

"""
Max zone transfer packet size in bytes
"""
maxSize = 1024

#TODO: Validate request
def processPacket(serverData:ServerData, packet:ZoneTransferPacket, ip:str, domain:Domain = None) -> tuple[Domain, ZoneTransferPacket]:
    """
    Given a packet an SP received from an SS, computes the packet(s) to send back
    in response. Auxiliary function for zoneTransferSP

    Arguments:

    serverData : ServerData -> the configuration of the server
    packet : ZoneTransferPacket -> the packet received
    """

    if domain is None and packet.sequenceNumber == SequenceNumber(0):
        domain = serverData.get_domain(packet.get_domain(), True) if packet.get_domain() else None
    entries = domain.database.entries if domain else None
    
    
    #TODO: Only use domain in first request
    status = ZoneStatus.SUCCESS
    result = ""
    utils.get_local_ip()(ip)
    if domain != None and not domain.is_authorized(ip):
        status = ZoneStatus.UNAUTHORIZED
    elif domain == None and packet.sequenceNumber.value in [0,2,4]:
        status = ZoneStatus.NO_SUCH_DOMAIN

    if packet.sequenceNumber == SequenceNumber(0):
        if status == ZoneStatus.SUCCESS:
            result = domain.database.serial
        return (domain, [ZoneTransferPacket(SequenceNumber(1), status, domain, result)])

    if packet.sequenceNumber == SequenceNumber(2):
        if status == ZoneStatus.SUCCESS:
            result = len(entries)
        return (domain, [ZoneTransferPacket(SequenceNumber(3), status, domain, result)])


    if packet.sequenceNumber == SequenceNumber(4):
        if domain == None:
            return (domain, [ZoneTransferPacket(SequenceNumber(5), \
                                                ZoneStatus.NO_SUCH_DOMAIN, None, "")])
        if status == ZoneStatus.UNAUTHORIZED:
            return (domain, [ZoneTransferPacket(SequenceNumber(5), status, domain, "")])
        res = []
        for index, entry in enumerate(entries):
            res.append(ZoneTransferPacket(SequenceNumber(5), ZoneStatus(0), domain, \
                                          (index, entry)))
        return (domain, res)

    return (domain, \
            [ZoneTransferPacket(SequenceNumber(0), ZoneStatus.BAD_REQUEST, domain, "")])

def zoneTransferSPClient(serverData:ServerData, logger:Queue, conn:socket, address:tuple[str,int]) -> None:
    """
    Handles the zone transfer process from the point of view of the SP,
    for a single SS client. Is called as a new thread by zoneTransferSP
    """
    domain = None
    try:
        clientConnected = TCPWrapper(conn, ZoneTransferPacket.split_messages, \
                                        maxSize, address)
        lock = threading.Lock()
        data = clientConnected.read()

        while data != b'':
            packet = ZoneTransferPacket.from_str(data.decode())

            with lock:
                (d, response_packets) = processPacket(serverData, packet, address[0], domain)
                if domain == None:
                    domain = d
            for response_packet in response_packets:
                clientConnected.write(str(response_packet).encode())

            data = clientConnected.read()
        logger.put(LogMessage(LoggingEntryType.ZT, f"{address[0]}:{address[1]}", \
            ["SP"], domain.name))
    except:
        logger.put(LogMessage(LoggingEntryType.EZ, f"{address[0]}:{address[1]}", \
            ["SP"], domain))
    finally:
        clientConnected.shutdown(socket.SHUT_WR)
        clientConnected.close()

def zoneTransferSP(serverData:ServerData, logger:Queue, localIP:str, port:int) -> None:
    """
    Function implementing the zone transfer protocol from the point of view of an
    SP.

    Arguments:

    serverData : ServerData -> the configuration of the server
    localIP      : String       -> The IP where the TCP socket will be bound
    port         : int          -> The port to listen on
    """
    #Setup socket
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSocket.bind((localIP, port))
    tcpSocket.listen()

    try:
        #Run forever
        while True:
            (conn, address) = tcpSocket.accept()
            t = threading.Thread(target=zoneTransferSPClient, \
                                 args=(serverData, logger, conn, address))
            t.start()
    finally:
        tcpSocket.close()


def getServerVersionNumber(tcpSocket:TCPWrapper, domain:str) -> int:
    """
    Queries the SP about the version number of the database of the given domain.
    Auxiliary function to zoneTransferSS

    Arguments:

    tcpSocket       -> the socket used to communicate with the SP
    domain : String -> the name of the domain to query about

    Returns:

    int : The version number of the database
    """
    sentPacket = ZoneTransferPacket(SequenceNumber(0), ZoneStatus(0), domain, domain)
    tcpSocket.write(str(sentPacket).encode())
    data = tcpSocket.read()
    receivedPacket = ZoneTransferPacket.from_str(data.decode())
    return receivedPacket.data


def getDomainNumberEntries(tcpSocket:socket, domain:str) -> int:
    """
    Queries the SP about the number of entries to expect for the given domain. Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket       -> the socket used to communicate with the SP
    domain : String -> the name of the domain to query about

    Returns:

    int : the number of entries to expect for the domain
    """
    sentPacket = ZoneTransferPacket(SequenceNumber(2), ZoneStatus(0), domain, domain)
    tcpSocket.write(str(sentPacket).encode())
    data = tcpSocket.read()
    receivedPacket = ZoneTransferPacket.from_str(data.decode())
    return receivedPacket.data


def acknowledgeNumberEntries(tcpSocket:socket, domain:str, entries:int) -> None:
    """
    Acknowledges the expected number of entries for a domain to the SP. Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket        -> the socket used to communicate with the SP
    domain : String  -> the name of the domain the number of entries refer to
    entries : int    -> the number of entries to expect
    """
    sentPacket = ZoneTransferPacket(SequenceNumber(4), ZoneStatus(0), domain, entries)
    tcpSocket.write(str(sentPacket).encode())

def getAllEntries(tcpSocket:socket, domain:Domain, entries:int) -> None:
    """
    Receives all entries for the given domain from the SP. Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket        -> the socket used to communicate with the SP
    domain  : String -> the name of the domain to get entries for
    entries : int    -> the number of entries to get
    """
    newEntries = []
    for i in range(entries):
        data = tcpSocket.read()
        receivedPacket = ZoneTransferPacket.from_str(data.decode())
        

        order = int(receivedPacket.data[0])
        entry = receivedPacket.data[1]

        newEntries.append(entry)

    domain.set_entries(newEntries)


def confirmEntries(tcpSocket:socket) -> None:
    """
    Confirms to the SP that it has received the expected number of entries. 
    Auxiliary function to zoneTransferSS

    Arguments:
    
    tcpSocket -> the socket used to communicate with the SP
    """
    sentPacket = ZoneTransferPacket(SequenceNumber(6), ZoneStatus(0), "")
    tcpSocket.write(str(sentPacket).encode())


def receiveEndOfTransfer(tcpSocket:socket) -> None:
    """
    Receives the end of transfer packet from the SP. Auxiliary function to zoneTransferSS

    Arguments:

    tcpSocket -> the socket used to communicate with the SP
    """
    tcpSocket.recv(maxSize)

def zoneTransferSS(serverData:ServerData, logger:Queue, domain_name:str) -> None:
    """
    Function implementing the zone transfer protocol from the point of view of an
    SS.

    Arguments:

    serverData : ServerData -> The configuration of the server
    """
    domain = serverData.get_domain(domain_name)
    while True:
        try:
            tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp.connect(utils.decompose_address(domain.primaryServer))
            tcpSocket = TCPWrapper(tcp, ZoneTransferPacket.split_messages, maxSize)
            
            versionNumber = getServerVersionNumber(tcpSocket, domain.name)

            #There is no new version of the database available
            if versionNumber == domain.get_serial():
                time.sleep(domain.get_refresh())
            else:
                numberEntries = getDomainNumberEntries(tcpSocket, domain.name)
                acknowledgeNumberEntries(tcpSocket, domain.name, numberEntries)
                getAllEntries(tcpSocket, domain, numberEntries)

            #TODO: Add bytes transferred and time elapsed/serial number
            logger.put(LogMessage(LoggingEntryType.ZT, domain.primaryServer, \
                ["SS"], domain_name))
        except:
            logger.put(LogMessage(LoggingEntryType.EZ, domain.primaryServer, \
                ["SS"], domain_name))
            # If zone transfer fails, retry after SOARETRY
            # seconds
            time.sleep(domain.get_retry())
            continue
        finally:
            tcpSocket.shutdown(socket.SHUT_WR)
            tcpSocket.close()
            serverData.set_domain(domain.name, domain)

        # Wait SOAREFRESH seconds before refreshing
        # database
        time.sleep(domain.get_refresh())