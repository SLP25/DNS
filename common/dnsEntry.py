from enum import Enum
import re
from .exceptions import InvalidDNSEntryException
import common.utils as utils


class EntryType(Enum):
    SOASP = 0
    SOAADMIN = 1
    SOASERIAL = 2
    SOAREFRESH = 3
    SOARETRY = 4
    SOAEXPIRE = 5
    NS = 6
    A = 7
    CNAME = 8
    MX = 9
    PTR = 10
    
    def parameter_is_domain(self):
        return self != EntryType.PTR
    
    def validate_parameter(self, parameter):
        if self.parameter_is_domain():
            if not re.search(f'^{utils.DOMAIN}$', parameter):
                raise InvalidDNSEntryException('parameter is not a valid domain name')
        else:   #parameter is ip address
            if not re.search(f'^{utils.IP_ADDRESS}$', parameter):
                raise InvalidDNSEntryException('parameter is not a valid IPv4 address')
    
    def validate_value(self, value):
        if self == EntryType.SOASP or self == EntryType.NS or self == EntryType.MX or self == EntryType.PTR:
            if not re.search(f'^{utils.DOMAIN}$', value):
                raise InvalidDNSEntryException('value is not a valid domain name')
        elif self == EntryType.A:
            if not re.search(f'^{utils.IP_ADDRESS}$', value):
                raise InvalidDNSEntryException('value is not a valid IPv4 address')
        elif self == EntryType.SOAADMIN:
            if not re.search(f'^{utils.EMAIL_ADDRESS}$', value):
                raise InvalidDNSEntryException('value is not a valid email address')
        else:   #value is an unsigned integer
            if not re.search('^\d+$', value):
                raise InvalidDNSEntryException('value is not an unsigned integer')
    
    @staticmethod
    def get_all():
        return [e.name for e in EntryType]
    

ENTRY_TYPE = f'({"|".join(EntryType.get_all())})'

class DNSEntry:
    def __init__(self, parameter, type, value, ttl, priority = 0):

        self.parameter = parameter
        self.type = type
        self.value = value
        self.ttl = ttl
        self.priority = priority

        self.type.validate_parameter(parameter)
        self.type.validate_value(value)
        
        if self.priority >= 256:
            raise InvalidDNSEntryException("Priority must be between 0 and 255")
        
       
    @staticmethod     
    def from_text(parameter, type, value, ttl, priority = '0'):
        _parameter = parameter
        _value = value
        
        try:
            _type = EntryType[type]
        except ValueError:
            raise InvalidDNSEntryException("Unknown entry type")
        
        try:
            _ttl = int(ttl)
            _priority = int(priority)
        except ValueError:
            raise InvalidDNSEntryException("TTL and priority must be integers")
        
        return DNSEntry(_parameter, _type, _value, _ttl, _priority)
            
    @staticmethod
    def from_bytes(data):
        ...

    def __validate_entry__(self):
        return None

    def to_bytes__(self):
        return []

    def __str__(self):
        return f"{self.parameter} {self.type.name} {self.value} {self.ttl} {self.priority}"