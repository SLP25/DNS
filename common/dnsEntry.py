"""
File containing classes DNSEntry and EntryType

Last Modification: Fix __str__ when priority is None
Date of Modification: 19/11/2022 18:11
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
    
    def supports_priority(self) -> bool:
        """
        Whether DNSEntry's of this type support priority
        """
        return self == EntryType.NS or self == EntryType.A or self == EntryType.MX
    
    def validate_parameter(self, parameter:str) -> str:
        """
        Validates the given string as a parameter of a DNSEntry of this type
        If the given parameter is invalid, raises an InvalidDNSEntryException
        Returns the validated parameter (this may be different from the received parameter if a
        domain name is expected; in that case, the domain name is normalized - see utils.normalize_domain())
        """
        #if self == EntryType.PTR:
        #    if not re.search(f'^{utils.IP_ADDRESS}$', parameter):
        #        raise InvalidDNSEntryException(f'{parameter} is not a valid IPv4 address')
        if self == EntryType.CNAME:
            if not re.search(f'^{utils.DOMAIN}$', parameter):
                raise InvalidDNSEntryException(f'{parameter} is not a valid domain name')
            parameter = parameter.lower()
        else:
            if not re.search(f'^{utils.FULL_DOMAIN}$', parameter):
                raise InvalidDNSEntryException(f'{parameter} is not a valid full domain name')
            parameter = parameter.lower()
        return parameter
    
    def validate_value(self, value:str) -> str:
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
    def get_all() -> list[str]:
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
    def from_str(line: str) -> 'DNSEntry':
        """ creates a dnsEntry from the string representation validating if the string is valid

        Args:
            line (str): the string representation of a dns entry

        Raises:
            ValueError: if the string doesn't match a dns Entry message

        Returns:
            _type_: a new DNS entry with the data inside
        """
        match = re.search(
            f'^\s*(?P<p>{PARAMETER_CHAR}+)\s+(?P<t>{ENTRY_TYPE})\s+(?P<v>[^\s]+)\s+(?P<ttl>\d+)(\s+(?P<pr>\d+))?\s*$',
            line)
        
        if match == None:
            raise ValueError(f"{line} doesn't match the pattern {{parameter}} {{type}} {{value}} {{ttl}} {{priority}}?")
    
        parameter = match.group('p')
        type = match.group('t')
        value = match.group('v')
        ttl = match.group('ttl')
        priority = match.group('pr')
        
        return DNSEntry.from_text(parameter,type,value,ttl,priority)
        
        
    @staticmethod     
    def from_text(parameter:str, type:str, value:str, ttl:str, priority:Optional[str] = None) -> 'DNSEntry':
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
        except KeyError:
            raise InvalidDNSEntryException("Unknown entry type")
        
        try:
            _ttl = int(ttl)
            _priority = None if priority == None else int(priority)
        except ValueError:
            raise InvalidDNSEntryException("TTL and priority must be integers")
        
        return DNSEntry(parameter, _type, value, _ttl, _priority)
            
    @staticmethod
    def from_bytes(data, pos = 0) -> tuple['DNSEntry',int]:
        """
        Constructs a DNSEntry from an array of bytes
        If the parsing fails, an InvalidDNSEntryException is thrown
        Returns a pair containing the dnsEntry and the number of consumed bytes
        """

        parameter, pos = utils.bytes_to_string(data, pos)

        type = utils.bytes_to_int(data, 1, pos)

        try:
            _type = EntryType(type)
        except ValueError:
            raise InvalidDNSEntryException("Unknown entry type")
        pos += 1

        value, pos = utils.bytes_to_string(data, pos)

        ttl = utils.bytes_to_int(data, 4, pos)

        pos += 4

        
        if _type.supports_priority():
            priority = utils.bytes_to_int(data, 1, pos)
            pos += 1
        else:
            priority = None
        
        return (DNSEntry(parameter, _type, value, ttl, priority), pos)

    def to_bytes(self) -> bytes:
        """
        Converts the current instance of DNSEntry to an array of bytes
        """        
        ans = utils.string_to_bytes(self.parameter) + utils.int_to_bytes(self.type.value, 1) + utils.string_to_bytes(self.value) + utils.int_to_bytes(self.ttl, 4)
        
        if self.type.supports_priority():
            ans += utils.int_to_bytes(self.priority, 1)
        
        return ans

    def __str__(self) -> str:
        """
        Converts the current instance of DNSEntry to its string representation
        """
        if self.priority:
            return f"{self.parameter} {self.type.name} {self.value} {self.ttl} {self.priority}"
        else:
            return f"{self.parameter} {self.type.name} {self.value} {self.ttl}"