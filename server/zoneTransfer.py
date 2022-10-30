import time
import socket
import sys
from common.dnsEntry import DNSEntry

#TODO: Handle errors (wrong status etc)
#TODO: Proper timeout

from server.zoneTransferPacket import SequenceNumber, ZoneTransferPacket, ZoneStatus

maxSize = 1024

def zoneTransferSP():
    pass

def getServerVersionNumber(tcpSocket, domain):
    sentPacket = ZoneTransferPacket(SequenceNumber(0), ZoneStatus(0), domain)
    tcpSocket.sendall(str(sentPacket))
    data = tcpSocket.recv(maxSize)
    receivedPacket = ZoneTransferPacket.from_str(data)
    return receivedPacket.data


def getDomainNumberEntries(tcpSocket, domain):
    sentPacket = ZoneTransferPacket(SequenceNumber(2), ZoneStatus(0), domain)
    tcpSocket.sendall(str(sentPacket))
    data = tcpSocket.recv(maxSize)
    receivedPacket = ZoneTransferPacket.from_str(data)
    return receivedPacket.data


def acknowledgeNumberEntries(tcpSocket, entries):
    sentPacket = ZoneTransferPacket(SequenceNumber(4), ZoneStatus(0), entries)
    tcpSocket.sendall(str(sentPacket))

def getAllEntries(tcpSocket, domain, entries):
    newEntries = {}
    for i in range(entries):
        data = tcpSocket.recv(maxSize)
        receivedPacket = ZoneTransferPacket.from_str(data)
        #TODO: Remove debug print
        print(str(receivedPacket))
        entry = DNSEntry(data, fromFile = True)
        
        if (domain, entry.type) not in newEntries.keys():
            newEntries[(domain, entry.type)] = []
        
        newEntries[(domain, entry.type)].append(entry)
        
        #TODO: Replace entries


def confirmEntries(tcpSocket):
    sentPacket = ZoneTransferPacket(SequenceNumber(6), ZoneStatus(0), None)
    tcpSocket.sendall(str(sentPacket))


def receiveEndOfTransfer(tcpSocket):
    tcpSocket.recv(maxSize)

def zoneTransferSS(serverConfig):
    while True:
        for domain in serverConfig.primaryDomains:
            server_address = serverConfig.primaryDomains[domain]
            # Create a TCP/IP socket
            tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpSocket.connect(server_address)

            try:
                versionNumber = getServerVersionNumber(tcpSocket, domain)

                #TODO: Check version Number
                if versionNumber < 0:
                    continue
                
                numberEntries = getDomainNumberEntries(tcpSocket, domain)
                acknowledgeNumberEntries(tcpSocket, domain, numberEntries)
                
                getAllEntries(tcpSocket, domain, numberEntries)
                
                confirmEntries(tcpSocket)
                
                receiveEndOfTransfer(tcpSocket)
            finally:
                print >>sys.stderr, 'closing socket'
                tcpSocket.close()

        time.sleep(10)