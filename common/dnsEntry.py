"""
File containing classes DNSEntry and EntryType 

Last Modification: Added documentation
Date of Modification: 14/11/2022 11:11
"""

from enum import Enum
import re
from .exceptions import InvalidDNSEntryException
import common.utils as utils
from typing import Optional


class EntryType(Enum):
    """
    Enum class, representing all possible types of dns entry
    Note that DEFAULT isn't an entry type, even though it is present in the SP database file.
    Rather, it alters other entries, but is transparent to the users
    """
    
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
        """
        Whether DNSEntry's of this type support priority
        """
        return self == EntryType.NS or self == EntryType.A or self == EntryType.MX
    
    def validate_parameter(self, parameter:str):
        """
        Validates the given string as a parameter of a DNSEntry of this type
        If the given parameter is invalid, raises an InvalidDNSEntryException
        Returns the validated parameter (this may be different from the received parameter if a
        domain name is expected; in that case, the domain name is normalized - see utils.normalize_domain())
        """
        if self == EntryType.PTR:
            if not re.search(f'^{utils.IP_ADDRESS}$', parameter):
                raise InvalidDNSEntryException(f'{parameter} is not a valid IPv4 address')
        elif self == EntryType.CNAME:
            if not re.search(f'^{utils.DOMAIN}$', parameter):
                raise InvalidDNSEntryException(f'{parameter} is not a valid domain name')
            parameter = parameter.lower()
        else:
            if not re.search(f'^{utils.FULL_DOMAIN}$', parameter):
                raise InvalidDNSEntryException(f'{parameter} is not a valid full domain name')
            parameter = parameter.lower()
        return parameter
    
    def validate_value(self, value:str):
        """
        Validates the given string as a value of a DNSEntry of this type
        If the received value is invalid, raises an InvalidDNSEntryException
        Returns the validated value (this may be different from the received value if a
        domain name is expected; in that case, the domain name is normalized - see utils.normalize_domain())
        """
        if self in [EntryType.SOASP, EntryType.NS, EntryType.PTR]:
            if not re.search(f'^{utils.FULL_DOMAIN}$', value):
                raise InvalidDNSEntryException(f'{value} is not a valid full domain name')
            value = value.lower()
        elif self in [EntryType.MX, EntryType.CNAME]:
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
        """
        Returns a list of all names of EntryTypes
        """
        return [e.name for e in EntryType]
    

"""
A regex pattern that matches all names of EntryTypes
"""
ENTRY_TYPE = f'{"|".join(EntryType.get_all())}'

"""
Regex pattern that matchs valid characters for the parameter attribute of a DNSEntry 
"""
PARAMETER_CHAR = r'[a-zA-Z0-9.-@]'

class DNSEntry:
    """
    Class representing a dns entry in SP databases, caches, etc
    Is composed of 5 attributes: a parameter (usually a domain name), a type (EntryType),
    a value, a TTL (unsigned integer) and a priority (integer between 0 and 255)
    """
    
    def __init__(self, parameter:str, type:EntryType, value:str, ttl:int, priority:Optional[int] = None):
        """
        Constructs a DNSEntry. If any parameter is deemed invalid,
        an InvalidDNSEntryException is raised

        Arguments:
        
        parameter : str         -> usually a domain name
        type      : EntryType   -> the type of entry
        value     : str
        ttl       : int         -> unsigned
        priority  : int/None    -> between 0 and 255. If None is passed, the default value 0 is used
        """
        
        if ttl < 0:
            raise InvalidDNSEntryException(f"TTL ({ttl}) must be non-negative")
        
        if priority != None and not type.supports_priority():
            raise InvalidDNSEntryException(f"DNS EntryType {type} doesn't support priority")
        
        if priority == None and type.supports_priority():
            priority = 0
            
        if priority != None and (priority < 0 or priority > 255):
            raise InvalidDNSEntryException(f"Priority {priority} must be between 0 and 255")
        
        self.parameter = type.validate_parameter(parameter)
        self.type = type
        self.value = type.validate_value(value)
        self.ttl = ttl
        self.priority = priority
       
    @staticmethod     
    def from_text(parameter:str, type:str, value:str, ttl:str, priority:Optional[str] = None):
        """
        Constructs a DNSEntry from string representations of each of the attributes
        If any of the attributes is deemed invalid, an InvalidDNSEntryException is raised

        Arguments:
        
        parameter : str         -> usually a domain name
        type      : str         -> the name of the type of entry
        value     : str
        ttl       : int         -> unsigned
        priority  : str/None    -> between 0 and 255. If None is passed, the default value 0 is used
        """
        
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
        """
        Constructs a DNSEntry from an array of bytes
        If the parsing fails, an InvalidDNSEntryException is thrown
        """
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
        """
        Converts the current instance of DNSEntry to an array of bytes
        """
        #TODO: pass type as 4 bits instead of 1 byte? or padding
        return utils.string_to_bytes(self.parameter) + utils.int_to_bytes(self.type.value, 1) + utils.string_to_bytes(self.value) + utils.int_to_bytes(self.ttl.value, 4) + utils.int_to_bytes(self.priority.value, 1)

    def __str__(self):  #TODO: tirar priority se o type nao suporta?
        """
        Converts the current instance of DNSEntry to its string representation
        """
        return f"{self.parameter} {self.type.name} {self.value} {self.ttl} {self.priority}"