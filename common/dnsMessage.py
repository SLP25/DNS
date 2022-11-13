import random
import re

from common.dnsEntry import DNSEntry, EntryType
from common.exceptions import InvalidDNSMessageException
from common.query import QueryInfo, QueryResponse
import common.utils as utils
from common.dnsEntry import ENTRY_TYPE

class DNSMessage:
    
    #wraps a query into a DNSMessage
    @staticmethod
    def from_query(query:QueryInfo, recursive:bool, messageID = random.randrange(1,65356)):
        ans = DNSMessage()
        ans.messageID = messageID
        ans.query = query
        ans.recursive = recursive
        return ans
    
    #creates a new DNSMessage that answers self
    def generate_response(self, response:QueryResponse, supports_recursive:bool):
        ans = DNSMessage()
        ans.messageID = self.messageID
        ans.query = self.query
        ans.response = response
        ans.responseCode = 0 if response.positive() else 1 #2??? TODO: perguntar
        ans.supports_recursive = supports_recursive
        return ans
    
    #creates a new DNSMessage that answers self with an error
    def generate_error_response(self, supports_recursive:bool):
        ans = DNSMessage()
        ans.messageID = self.messageID
        ans.query = self.query
        ans.response = QueryResponse()
        ans.responseCode = 3
        ans.supports_recursive = supports_recursive
        return ans
        
    def is_query(self):
        return not hasattr(self, 'response')
    
    #if self is a query, indicates whether the query is recursive
    #if self is a response, indicates whether the server supports recursive mode
    def flag_recursive(self):
        if self.is_query():
            return self.recursive
        else:
            return self.supports_recursive
        
    #if self is a query, returns False
    #if self is a response, indicates whether the response is authoritative
    def flag_authoritative(self):
        if self.is_query():
            return False
        else:
            return self.response.authoritative

    def __flags_as_string__(self):
        return '+'.join(f"{'Q' if self.is_query() else ''}{'R' if self.flag_recursive() else ''}{'A' if self.flag_authoritative() else ''}")


    def __str__(self):
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
        #TODO using utils
        pass

    @staticmethod
    def from_bytes(bytes):
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