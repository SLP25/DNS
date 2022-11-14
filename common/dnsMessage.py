"""
File defining the class DNSMessage

Last Modification: Added documentation
Date of Modification: 14/11/2022 11:31
"""

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
    def from_query(query:QueryInfo, recursive:bool, messageID:int = random.randrange(1,65356)):
        """
        Constructs a DNSMessage query from the given QueryInfo, recursive flag and messageID
        """
        ans = DNSMessage()
        ans.messageID = messageID
        ans.query = query
        ans.recursive = recursive
        return ans
    

    def generate_response(self, response:QueryResponse, supports_recursive:bool):
        """
        Generates a response DNSMessage to the current instance using the
        given QueryResponse and supports_recursive flag
        """
        ans = DNSMessage()
        ans.messageID = self.messageID
        ans.query = self.query
        ans.response = response
        ans.responseCode = 0 if response.positive() else 1 #2??? TODO: perguntar
        ans.supports_recursive = supports_recursive
        return ans
    
    def generate_error_response(self, supports_recursive:bool):
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
        
    def is_query(self):
        """
        Returns whether the current instance is a query. If false, the instance is a response
        """
        return not hasattr(self, 'response')
    
    #if self is a query, indicates whether
    #if self is a response, indicates whether the server supports recursive mode
    def __flag_recursive__(self):
        if self.is_query():
            return self.recursive
        else:
            return self.supports_recursive
        
    #if self is a query, returns False
    #if self is a response, indicates whether the response is authoritative
    def _flag_authoritative__(self):
        if self.is_query():
            return False
        else:
            return self.response.authoritative

    def __flags_as_string__(self):
        return '+'.join(f"{'Q' if self.is_query() else ''}{'R' if self.__flag_recursive__() else ''}{'A' if self._flag_authoritative__() else ''}")


    def __str__(self):
        """
        Determines the representation of the current instance as a string
        (as of examples 5 and 6 of the statement)
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

    @staticmethod
    def from_string(str):
        """
        Constructs an instance of DNSMessage from the given string representation
        (as of examples 5 and 6 of the statement)
        If the parsing fails, an InvalidDNSMessageException is raised
        """
        match = re.search(f'^(?P<id>\d+),(?P<flags>[QRA](\+[QRA]){{0,2}})?,(?P<code>[0-3]),(?P<vals>\d+),(?P<auths>\d+),(?P<extras>\d+);(?P<name>{utils.FULL_DOMAIN}),(?P<type>{ENTRY_TYPE});', str)
        if not match:
            raise InvalidDNSMessageException(f"{str} doesn't match the expected format")

        ans = DNSMessage()
        ans.messageID = match.group('id')
        flag_q, flag_r, flag_a = __read_flags__(match.group('flags'))
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
            ans.response = QueryResponse(vals, auths, extras, flag_a)
            
        if body != '':
            raise InvalidDNSMessageException(f"{body} not expected after DNS packet")
            
        return ans

    def to_bytes(self):
        """
        Converts the current instance to an array of bytes
        """
        #TODO using utils
        pass

    @staticmethod
    def from_bytes(bytes):
        """
        Constructs an instance of DNSMessage from an array of bytes
        If the parsing fails, an InvalidDNSMessageException is raised
        """
        #TODO using utils
        pass


def __read_flags__(str):
    for f in "QRA":
        if str.count(f) > 1:
            raise InvalidDNSMessageException(f"Multiple occurences of flag {f} in flags: {str}")
    
    return ('Q' in str, 'R' in str, 'A' in str)

def __read_entries__(str, expected):
        ans = []
        while expected > 0:
            expected -= 1
            
            m = re.search(f"^\n(?P<param>[^\s]+) (?P<type>{ENTRY_TYPE}) (?P<val>[^\s]+) (?P<ttl>\d+)( (?P<pr>\d+))?{',' if expected > 0 else ';'}", str)
            if not m:
                raise InvalidDNSMessageException(f"{str} doesn't contain the expected DNS entry format")
            
            ans.append(DNSEntry.from_text(m.group('param'), m.group('type'), m.group('val'), m.group('ttl'), m.group('pr')))
            str = str[m.end():]

        return (ans, str)