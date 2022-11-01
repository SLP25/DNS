import time
import socket
import sys
from common.dnsEntry import DNSEntry

#TODO: Handle errors (wrong status etc)
#TODO: Proper timeout
#TODO: Domain verification on acknowledgement
from server.zoneTransferPacket import SequenceNumber, ZoneTransferPacket, ZoneStatus

maxSize = 1024

#TODO: Validate request
def processPacket(packet):
    if packet.sequenceNumber == SequenceNumber(0):
        return ZoneTransferPacket(SequenceNumber(1), ZoneStatus(0), 1)

    if packet.sequenceNumber == SequenceNumber(2):
        return ZoneTransferPacket(SequenceNumber(3), ZoneStatus(0), 1)


    if packet.sequenceNumber == SequenceNumber(4):
        return ZoneTransferPacket(SequenceNumber(5), ZoneStatus(0), (0,DNSEntry("ns1 CNAME batata 100 100", fromFile = True)))

    
    if packet.sequenceNumber == SequenceNumber(6):
        return ZoneTransferPacket(SequenceNumber(7), ZoneStatus(0), None)

def zoneTransferSP(localIP, port):
    
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSocket.bind((localIP, port))
    tcpSocket.listen()

    try:
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
    sentPacket = ZoneTransferPacket(SequenceNumber(0), ZoneStatus(0), domain)
    tcpSocket.send(str(sentPacket).encode())
    data = tcpSocket.recv(maxSize)
    receivedPacket = ZoneTransferPacket.from_str(data.decode())
    return receivedPacket.data


def getDomainNumberEntries(tcpSocket, domain):
    sentPacket = ZoneTransferPacket(SequenceNumber(2), ZoneStatus(0), domain)
    tcpSocket.send(str(sentPacket).encode())
    data = tcpSocket.recv(maxSize)
    receivedPacket = ZoneTransferPacket.from_str(data.decode())
    return receivedPacket.data


def acknowledgeNumberEntries(tcpSocket, domain, entries):
    sentPacket = ZoneTransferPacket(SequenceNumber(4), ZoneStatus(0), (entries, domain))
    tcpSocket.sendall(str(sentPacket).encode())

def getAllEntries(tcpSocket, domain, entries):
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
    sentPacket = ZoneTransferPacket(SequenceNumber(6), ZoneStatus(0), None)
    tcpSocket.sendall(str(sentPacket).encode())


def receiveEndOfTransfer(tcpSocket):
    tcpSocket.recv(maxSize)

def zoneTransferSS(serverConfig):
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