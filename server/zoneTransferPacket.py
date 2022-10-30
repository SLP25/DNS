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

from exceptions import InvalidZoneTransferPacketException

class SequenceNumber(Enum):
    '''
    The sequence number indicates which part of the zone transfer
    protocol is being conducted
    '''
    SS_VERSION_NUMBER = 0, 'SS server requests the version number of the database for a domain'
    SP_VERSION_NUMBER = 1, 'SP replies with the version number of the database'
    SS_DOMAIN_NAME = 2, 'SS wants to do a zone transfer for a given domain'
    SP_NUMBER_ENTRIES = 3, 'SP sends the number of entries in the database for the domain'
    SS_NUMBER_ENTRIES = 4, 'SS acknowledges the number of entries'
    SP_DNS_ENTRY = 5, 'SP is sending an entry of the database for the domain'
    SS_ACKNOWLEDGE = 6, 'SS confirms having received all database entries'
    SP_ACKNOWLEDGE = 7, 'SP acknowledges and zone transfer terminates'

class ZoneStatus(Enum):
    '''
    The status indicates the response code for the previous request.
    In other words, the SS will send a request (with status 0) and the
    SP in its reply will indicate the status for the request it was sent.
    
    So if a SS is not authorized to see information about a domain, the SP
    would put a 1 value in the status field of its reply
    '''
    SUCCESS = 0, 'No errors'
    UNAUTHORIZED = 1, 'SS not authorized to view information about the domain'
    NO_SUCH_DOMAIN = 2, 'SP does not have the given domain in the database'
    BAD_REQUEST = 3, 'The previous request was not in the correct format'

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
            raise InvalidZoneTransferPacketException("String does not follow format")

        sequenceNumber = SequenceNumber(int(search.group(1)))
        status = ZoneStatus(int(search.group(2)))

        data = None
        #TODO: Validate input
        if sequenceNumber in [0,2]:
            data = search.group(3)
        elif sequenceNumber in [1,3,4]:
            data = int(search.group(3))
        elif sequenceNumber in [5]:
            data_search = re.search("([1-9][0-9]{0,4}|65535)", search.group(3))
            if data_search is None:
                raise InvalidZoneTransferPacketException("No order for dns entry given")
            data = (int(data_search.group(1)), DNSEntry(data_search.group(2), fromFile= True))

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
        return "({sequenceNumber},{status},{data})".format(
            sequenceNumber = self.sequenceNumber,
            status = self.status, data = self.data)