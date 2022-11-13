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
    
    def supports_priority(self):
        return self == EntryType.NS or self == EntryType.A or self == EntryType.MX
    
    def validate_parameter(self, parameter):
        if self == EntryType.PTR:
            if not re.search(f'^{utils.IP_ADDRESS}$', parameter):
                raise InvalidDNSEntryException(f'{parameter} is not a valid IPv4 address')
        elif self == EntryType.CNAME:
            if not re.search(f'^{utils.DOMAIN}$', parameter):
                raise InvalidDNSEntryException(f'{parameter} is not a valid domain name')
            value = value.lower()
        else:
            if not re.search(f'^{utils.FULL_DOMAIN}$', parameter):
                raise InvalidDNSEntryException(f'{parameter} is not a valid full domain name')
            value = value.lower()
        return value
    
    def validate_value(self, value):
        if self == EntryType.SOASP or self == EntryType.NS or self == EntryType.PTR:
            if not re.search(f'^{utils.FULL_DOMAIN}$', value):
                raise InvalidDNSEntryException(f'{value} is not a valid full domain name')
            value = value.lower()
        elif self == EntryType.MX or self == EntryType.CNAME:
            if not re.search(f'^{utils.DOMAIN}$', value):
                raise InvalidDNSEntryException(f'{value} is not a valid domain name')
            value = value.lower()
        elif self == EntryType.A:
            if not re.search(f'^{utils.IP_ADDRESS}$', value):
                raise InvalidDNSEntryException(f'{value} is not a valid IPv4 address')
        elif self == EntryType.SOAADMIN:
            if not re.search(f'^{utils.EMAIL_ADDRESS}$', value):
                raise InvalidDNSEntryException(f'{value} is not a valid email address')
        return value
    
    @staticmethod
    def get_all():
        return [e.name for e in EntryType]
    

ENTRY_TYPE = f'{"|".join(EntryType.get_all())}'

class DNSEntry:
    def __init__(self, parameter, type, value, ttl, priority = None):
        if ttl < 0:
            raise InvalidDNSEntryException(f"TTL ({ttl}) must be positive")
        
        if priority != None and not type.supports_priority:
            raise InvalidDNSEntryException(f"DNS EntryType {type} doesn't support priority")
        
        if priority == None and type.supports_priority:
            priority = 0
            
        if priority < 0 or priority > 255:
            raise InvalidDNSEntryException(f"Priority {priority} must be between 0 and 255")
        
        self.parameter = type.validate_parameter(parameter)
        self.type = type
        self.value = type.validate_value(value)
        self.ttl = ttl
        self.priority = priority
       
    @staticmethod     
    def from_text(parameter, type, value, ttl, priority = None):
        try:
            _type = EntryType[type]
        except ValueError:
            raise InvalidDNSEntryException("Unknown entry type")
        
        try:
            _ttl = int(ttl)
            _priority = None if priority == None else int(priority)
        except ValueError:
            raise InvalidDNSEntryException("TTL and priority must be integers")
        
        return DNSEntry(parameter, _type, value, _ttl, _priority)
            
    @staticmethod
    def from_bytes(data):
        pos = 0
        
        parameter = utils.bytes_to_string(data, pos)
        pos += len(parameter) + 1
        
        type = utils.bytes_to_int(data, 1, pos)
        pos += 1
        
        value = utils.bytes_to_string(data, pos)
        pos += len(value) + 1
        
        ttl = utils.bytes_to_int(data, 4, pos)
        pos += 4
        
        priority = utils.bytes_to_int(data, 1, pos)
        pos += 1
        
        return DNSEntry(parameter, type, value, ttl, priority)

    def to_bytes__(self):
        return utils.string_to_bytes(self.parameter) + utils.int_to_bytes(self.type.value, 1) + utils.string_to_bytes(self.value) + utils.int_to_bytes(self.ttl.value, 4) + utils.int_to_bytes(self.priority.value, 1)

    def __str__(self):
        return f"{self.parameter} {self.type.name} {self.value} {self.ttl} {self.priority}"