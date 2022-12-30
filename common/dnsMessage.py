"""
File defining the class DNSMessage

Last Modification: Added documentation
Date of Modification: 14/11/2022 11:31
"""

import itertools
import random
import re

from common.dnsEntry import DNSEntry, EntryType
from common.exceptions import InvalidDNSMessageException
from common.query import QueryInfo, QueryResponse
import common.utils as utils
from common.dnsEntry import ENTRY_TYPE

class DNSMessage:
    """
    Class representing a dns message sent between servers asking and answering dns queries
    Instances of DNSMessage have the following attributes:
        messageID   -> int (between 1 and 65356)
        query       -> QueryInfo

    If the instance is a query:
        recursive   -> bool
        
    If the instance is an answer:
        response            -> QueryResponse
        responseCode        -> int (between 0 and 3)
        supports_recursive  -> bool
    """
    
    @staticmethod
    def from_query(query:QueryInfo, recursive:bool, messageID:int = random.randrange(1,65357)) -> 'DNSMessage':
        """
        Constructs a DNSMessage query from the given QueryInfo, recursive flag and messageID
        """
        
        if messageID < 1 or messageID > 65356:
            raise InvalidDNSMessageException(f"messageID ({messageID}) must be between 0 and 65356.")
        
        ans = DNSMessage()
        ans.messageID = messageID
        ans.query = query
        ans.recursive = recursive
        
        return ans
    

    def generate_response(self, response:QueryResponse, supports_recursive:bool) -> 'DNSMessage':
        """
        Generates a response DNSMessage to the current instance using the
        given QueryResponse and supports_recursive flag
        """
        ans = DNSMessage()
        ans.messageID = self.messageID
        ans.query = self.query
        ans.response = response
        ans.responseCode = (2 if len(response.values) == 0 else 0) if response.isFinal() else 1
        ans.supports_recursive = supports_recursive
        return ans
    
    def generate_error_response(self, supports_recursive:bool) -> 'DNSMessage':
        """
        Generates an error response DNSMessage to the current instance (responseCode = 3)
        using the given supports_recursive flag
        """
        ans = DNSMessage()
        ans.messageID = self.messageID
        ans.query = self.query
        ans.response = QueryResponse()
        ans.responseCode = 3
        ans.supports_recursive = supports_recursive
        return ans
    
    @staticmethod
    def error_response(supports_recursive:bool) -> 'DNSMessage':
        """
        Generates an error response DNSMessage(responseCode = 3) using the given supports_recursive flag
        """
        ans = DNSMessage()
        ans.messageID = 1
        ans.query = QueryInfo("", EntryType.A)
        ans.response = QueryResponse()
        ans.responseCode = 3
        ans.supports_recursive = supports_recursive
        return ans
        
    def is_query(self) -> bool:
        """
        Returns whether the current instance is a query. If false, the instance is a response
        """
        return not hasattr(self, 'response')
    

    def __flag_recursive__(self) -> bool:
        """if query    : return the state of the recursive flag
           if response : return if supports recursive mode
        

        Returns:
            Bool: if is query then return if the recursive flag is set.if is response will return if it supports recursive mode
        """
        if self.is_query():
            return self.recursive
        else:
            return self.supports_recursive
        
    #if self is a query, returns False
    #if self is a response, indicates whether the response is authoritative
    def __flag_authoritative__(self) -> bool:
        """if query    : return False
           if response : return if the response is authoritative

        Returns:
            Bool: if query will return false. If response will indicate if the response is authorative
        """
        if self.is_query():
            return False
        else:
            return self.response.authoritative

    def __flags_as_string__(self) -> str:
        """Return the flags of the message as a string Representation

        Returns:
            String: the string representation of the message flags
        """
        return '+'.join(f"{'Q' if self.is_query() else ''}{'R' if self.__flag_recursive__() else ''}{'A' if self.__flag_authoritative__() else ''}")


    def __str__(self) -> str:
        """
        Determines the representation of the current instance as a string
        (as of examples 5 and 7 of the statement)
        """
        ans = f'{self.messageID},' \
            + f'{self.__flags_as_string__()},' \
            + f'{self.responseCode if not self.is_query() else 0},' \
            + f'{len(self.response.values) if not self.is_query() else 0},' \
            + f'{len(self.response.authorities) if not self.is_query() else 0},' \
            + f'{len(self.response.extra_values) if not self.is_query() else 0};' \
            + f'{self.query};'
        
        if not self.is_query():
            br = '\n'
            ans += f"{br}{f',{br}'.join(map(str, self.response.values))};"
            ans += f"{br}{f',{br}'.join(map(str, self.response.authorities))};"
            ans += f"{br}{f',{br}'.join(map(str, self.response.extra_values))};"

        return ans
    
    def print(self) -> str:
        """
        Determines the pretty representation of the current instance as a string
        (as of examples 4, 6 and 8 of the statement)
        """
        ans = '# Header\n' \
            + f'MESSAGE-ID = {self.messageID}, ' \
            + f'FLAGS = {self.__flags_as_string__()}, ' \
            + f'RESPONSE-CODE = {self.responseCode if not self.is_query() else 0},\n' \
            + f'N-VALUES = {len(self.response.values) if not self.is_query() else 0}, ' \
            + f'N-AUTHORITIES = {len(self.response.authorities) if not self.is_query() else 0}, ' \
            + f'N-EXTRA-VALUES = {len(self.response.extra_values) if not self.is_query() else 0},;\n' \
            + f'# Data: Query Info\n' \
            + f'QUERY-INFO.NAME = {self.query.name}, QUERY-INFO.TYPE = {self.query.type},;\n' \
            + f'# Data: List of Response, Authorities and Extra Values\n'
            
        ans += f'{__print_list__("RESPONSE-VALUES", [] if self.is_query() else self.response.values)}\n'
        ans += f'{__print_list__("AUTHORITIES-VALUES", [] if self.is_query() else self.response.authorities)}\n'
        ans += f'{__print_list__("EXTRA-VALUES", [] if self.is_query() else self.response.extra_values)}'
        
        return ans            

    @staticmethod
    def from_string(str:str) -> 'DNSMessage':
        """
        Constructs an instance of DNSMessage from the given string representation
        (as of examples 5 and 6 of the statement)
        If the parsing fails, an InvalidDNSMessageException is raised
        """
        match = re.search(f'^(?P<id>\d+),(?P<flags>[QRA](\+[QRA]){{0,2}})?,(?P<code>[0-3]),(?P<vals>\d+),(?P<auths>\d+),(?P<extras>\d+);(?P<name>{utils.FULL_DOMAIN}),(?P<type>{ENTRY_TYPE});', str)
        if not match:
            raise InvalidDNSMessageException(f"{str} doesn't match the expected format")

        ans = DNSMessage()
        ans.messageID = int(match.group('id'))
        if ans.messageID < 1 or ans.messageID > 65356:
            raise InvalidDNSMessageException(f"messageID ({ans.messageID}) must be between 0 and 65356.")
        
        flag_str = match.group('flags')
        flag_q, flag_r, flag_a = __read_flags__(flag_str if flag_str else "")
        ans.query = QueryInfo(match.group('name'), EntryType[match.group('type')])
        body = str[match.end():]
        
        if flag_q:
            ans.recursive = flag_r
        else:
            ans.supports_recursive = flag_r
            ans.responseCode = int(match.group('code'))
            vals, body = __read_entries__(body, int(match.group('vals')))
            auths, body = __read_entries__(body, int(match.group('auths')))
            extras, body = __read_entries__(body, int(match.group('extras')))
            ans.response = QueryResponse(vals, auths, extras, ans.responseCode == 2, flag_a)
            
        if body != '':
            raise InvalidDNSMessageException(f"{body} not expected after DNS packet")
            
        return ans

    def to_bytes(self) -> bytes:
        """
        Converts the current instance to an array of bytes
        """
        flags = (1 if self.is_query() else 0) << 2 | (1 if self.__flag_recursive__() else 0) << 1 | (1 if self.__flag_authoritative__() else 0)
        flags_plus_response_code = flags << 2 | (self.responseCode if not self.is_query() else 0)
        
        ans = utils.int_to_bytes(self.messageID - 1, 2) \
            + utils.int_to_bytes(flags_plus_response_code, 1) \
            + utils.int_to_bytes(len(self.response.values) if not self.is_query() else 0, 1) \
            + utils.int_to_bytes(len(self.response.authorities) if not self.is_query() else 0, 1) \
            + utils.int_to_bytes(len(self.response.extra_values) if not self.is_query() else 0, 1) \
            + utils.string_to_bytes(self.query.name) \
            + utils.int_to_bytes(self.query.type.value, 1)
        
        if not self.is_query():
            for e in itertools.chain(self.response.values, self.response.authorities, self.response.extra_values):
                ans += e.to_bytes()
        
        return ans

    @staticmethod
    def from_bytes(data:bytes) -> tuple['DNSMessage',int]:
        """
        Constructs an instance of DNSMessage from an array of bytes
        If the parsing fails, an InvalidDNSMessageException is raised
        """
        ans = DNSMessage()
        pos = 0
        
        ans.messageID = utils.bytes_to_int(data, 2, pos) + 1
        pos += 2
        
        aux = utils.bytes_to_int(data, 1, pos)
        flag_q = aux & 0b10000
        flag_r = aux & 0b1000
        flag_a = aux & 0b100
        responseCode = aux & 0b11
        pos += 1
        
        vals = utils.bytes_to_int(data, 1, pos)
        pos += 1
        
        auths = utils.bytes_to_int(data, 1, pos)
        pos += 1
        
        extra_vals = utils.bytes_to_int(data, 1, pos)
        pos += 1
        
        name, pos = utils.bytes_to_string(data, pos)
        
        type = EntryType(utils.bytes_to_int(data, 1, pos))
        pos += 1
        
        if flag_q:
            ans.recursive = flag_r
        else:
            ans.supports_recursive = flag_r
            ans.responseCode = responseCode
            values, pos = __parse_entries__(data, vals, pos)
            authorities, pos = __parse_entries__(data, auths, pos)
            extra_values, pos = __parse_entries__(data, extra_vals, pos)
            ans.response = QueryResponse(values, authorities, extra_values, ans.responseCode == 2, flag_a)
        
        ans.query = QueryInfo(name, type)
        return (ans, pos)


def __read_flags__(str:str) -> tuple[bool,bool,bool]:
    """returns a tuple of the state of each flags in the order: Query,Recursive,Authoritative

    Args:
        str (String): the flags to read 

    Raises:
        InvalidDNSMessageException: in case there are repeted flags in the input

    Returns:
        Tuple: the state of each flags in the order: Query,Recursive,Authoritative
    """
    for f in "QRA":
        if str.count(f) > 1:
            raise InvalidDNSMessageException(f"Multiple occurences of flag {f} in flags: {str}")
    
    return ('Q' in str, 'R' in str, 'A' in str)

def __read_entries__(str:str, expected:int) -> tuple[list[DNSEntry],str]:
    """parse a given number of entries from a string

    Args:
        str (String): the string containing the entries to be parsed
        expected (int): the number of entries expected to be found

    Raises:
        InvalidDNSMessageException: if the format of one of the entries isn't correct

    Returns:
        Tuple: list of all entries found and the rest of the string that wasn't read
    """
    ans = []
    
    if expected == 0:
        m = re.search(f"^\n;", str)
        str = str[m.end():]
    else:
        while expected > 0:
            expected -= 1
            
            m = re.search(f"^\n(?P<param>[^\s]+) (?P<type>{ENTRY_TYPE}) (?P<val>[^\s]+) (?P<ttl>\d+)( (?P<pr>\d+))?{',' if expected > 0 else ';'}", str)
            if not m:
                raise InvalidDNSMessageException(f"{str} doesn't contain the expected DNS entry format")
            
            ans.append(DNSEntry.from_text(m.group('param'), m.group('type'), m.group('val'), m.group('ttl'), m.group('pr')))
            str = str[m.end():]

    return (ans, str)

def __parse_entries__(data:bytes, expected:int, pos:int = 0) -> tuple[list[DNSEntry],int]:
    """_summary_

    Args:
        data (_type_): _description_
        expected (int): _description_
        pos (int, optional): _description_. Defaults to 0.

    Returns:
        _type_: _description_
    """
    ans = []
    
    for i in range(0, expected):
        entry, pos = DNSEntry.from_bytes(data, pos)
        ans.append(entry)
        
    return (ans, pos)

def __print_list__(list_name:str, list:list[DNSEntry]):
    
    if list == []:
        return f'{list_name} = (Null)'
    else:
        return '\n'.join([f'{list_name} = {e}' for e in list])