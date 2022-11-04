'''
File implementing the class representing
a zone transfer packet

A zone transfer packet is used for zone transfer requests and
has a header made up of:

- Sequence number (c.f. SequenceNumber documentation)
- Response Code (c.f. ZoneStatus documentation)

and a data section, which depends on the sequence number (c.f. ZoneTransferPacket
documentation for more details)

Details regarding the zone transfer protocol can be found in the documentation for
zoneTransfer.py

Last modification: Creation
Date of modification: 30/10/2022 11:15
'''

from enum import Enum
import re
from common.dnsEntry import DNSEntry

from .exceptions import InvalidZoneTransferPacketException

class SequenceNumber(Enum):
    '''
    The sequence number indicates which part of the zone transfer
    protocol is being conducted

    SS_VERSION_NUMBER = 0, 'SS server requests the version number of the database for a domain'
    SP_VERSION_NUMBER = 1, 'SP replies with the version number of the database'
    SS_DOMAIN_NAME = 2, 'SS wants to do a zone transfer for a given domain'
    SP_NUMBER_ENTRIES = 3, 'SP sends the number of entries in the database for the domain'
    SS_NUMBER_ENTRIES = 4, 'SS acknowledges the number of entries'
    SP_DNS_ENTRY = 5, 'SP is sending an entry of the database for the domain'
    SS_ACKNOWLEDGE = 6, 'SS confirms having received all database entries'
    SP_ACKNOWLEDGE = 7, 'SP acknowledges and zone transfer terminates'
     
    '''
    SS_VERSION_NUMBER = 0
    SP_VERSION_NUMBER = 1
    SS_DOMAIN_NAME = 2
    SP_NUMBER_ENTRIES = 3
    SS_NUMBER_ENTRIES = 4
    SP_DNS_ENTRY = 5
    SS_ACKNOWLEDGE = 6
    SP_ACKNOWLEDGE = 7

class ZoneStatus(Enum):
    '''
    The status indicates the response code for the previous request.
    In other words, the SS will send a request (with status 0) and the
    SP in its reply will indicate the status for the request it was sent.
    
    So if a SS is not authorized to see information about a domain, the SP
    would put a 1 value in the status field of its reply


    SUCCESS = 0, 'No errors'
    UNAUTHORIZED = 1, 'SS not authorized to view information about the domain'
    NO_SUCH_DOMAIN = 2, 'SP does not have the given domain in the database'
    BAD_REQUEST = 3, 'The previous request was not in the correct format'
    '''
    SUCCESS = 0
    UNAUTHORIZED = 1
    NO_SUCH_DOMAIN = 2
    BAD_REQUEST = 3

class ZoneTransferPacket:
    '''
    A class representing a packet used for zone transfers.
    
    For more information regarding the zone transfer protocol, refer
    to the documentation of zoneTransfer.py
    '''
    def __init__(self, sequenceNumber, status, data):
        '''
        Initializes a ZoneTransfer packet.
        
        Arguments:
        
        - sequenceNumber: SequenceNumber
        - status : ZoneStatus
        - data : can be either a string (domain name), integer (number of entries in
        database, database version), or a tuple (order, dns_entry), with order being
        an integer from 0-65535 and dns_entry a DNSEntry object
        '''
        self.sequenceNumber = sequenceNumber
        self.status = status
        self.data = data
        pass

    @staticmethod
    def split_messages(buffer):
        """
        Splits the content of the buffer in the first message in it and
        the remaining of the buffer. Works like splitting a list in Haskell by 
        head and tail, only that each element of the list is a ZoneTransferPacket.
        
        This has no side effects.

        Args:
            buffer (bytes): the buffer to split

        Returns:
            (bytes | None, bytes): (The first message (None if not exists), the
            remaining buffer)
        """
        #TODO: Binary
        split = buffer.decode().split("\n", 1)

        if len(split) == 1:
            return (None, buffer)
        
        return (split[0], split[1])
        
    
    @staticmethod
    def from_str(string):
        '''
        Creates a ZoneTransferPacket from a given string.
        
        
        The string is a tuple with the following format:
        "(<sequence_number>,<status>,<data>)"

        and data can be:
        - an integer
        - a string (in quotes, e.g. (2,0,"example.com"))
        - a tuple in the format "(<order>,<dns_entry>)" with order being
        an integer from 0-65535 and dns_entry a DNSEntry in string form
        '''
        search = re.search("(\(([01234567])\,([012])\,(.*)\))", string)

        if search is None:
            raise InvalidZoneTransferPacketException("String " + string + " does not follow format")

        # The groups for the regex are: 0 -> whole thing 1-> whole thing again 2-> first match,
        # hence starting from 2 instead of 1
        sequenceNumber = SequenceNumber(int(search.group(2)))
        status = ZoneStatus(int(search.group(3)))

        data = None
        #TODO: Validate input
        if sequenceNumber.value in [0,2]:
            data = search.group(4)
        elif sequenceNumber.value in [1,3]:
            data = int(search.group(4))
        elif sequenceNumber.value in [5]:
            print(search.group(4))
            data_search = re.search("\\((([0-9]{1,5}|65535),(.*))\\)", search.group(4))
            if data_search is None:
                raise InvalidZoneTransferPacketException("No order for dns entry given")
            data = (int(data_search.group(2)), DNSEntry(data_search.group(3), fromFile= True))
        elif sequenceNumber.value in [4]:
            data_search = re.search("\\((([0-9]{1,5}|65535),(.*))\\)", search.group(4))
            if data_search is None:
                raise InvalidZoneTransferPacketException("Invalid packet")
            data = (int(data_search.group(2)), data_search.group(3))
        return ZoneTransferPacket(sequenceNumber, status, data)

    def __str__(self):
        '''
        Converts a zone transfer packet to a string.
        
        The string is a tuple with the following format:
        "(<sequence_number>,<status>,<data>)"

        and data can be:
        - an integer
        - a string (in quotes, e.g. (2,0,"example.com"))
        - a tuple in the format "(<order>,<dns_entry>)" with order being
        an integer from 0-65535 and dns_entry a DNSEntry in string form
        '''
            
        return "({sequenceNumber},{status},{data})\n".format(
            sequenceNumber = self.sequenceNumber.value,
            status = self.status.value, data = str(self.data) if self.sequenceNumber.value not in [4,5] else f"({str(self.data[0])},{str(self.data[1])})")