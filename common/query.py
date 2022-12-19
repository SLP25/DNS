"""
Contains definitions for the classes QueryInfo and QueryResponse

Last Modification: Added documentation
Date of Modification: 14/11/2022 11:45
"""

from common.dnsEntry import DNSEntry, EntryType
import common.utils as utils
import itertools

class QueryInfo:
    """
    Represents a query
    Contains a hostname and an EntryType
    """
    
    def __init__(self, name:str, type:EntryType):
        self.name = name.lower()
        self.type = type
        
    def __str__(self) -> str:
        """turn the query info into its string representation

        Returns:
            String: the string representation of the object
        """
        return f'{self.name},{self.type.name}'

class QueryResponse:
    """
    Represents an answer to a query
    Contains the following attributes:
        values          -> list of DNSEntry's that match the query name and type
        authorities     -> list of DNSEntry's that match the query name and are of type NS
        extra_values    -> list of DNSEntry's that match the values and authorities parameter and are of type NS
        authoritative   -> whether the response came directly from an authoritative server on the queried domain
    """
    
    def __init__(self,values:list[DNSEntry]=[],authorities:list[DNSEntry]=[],extra_values:list[DNSEntry]=[],final:bool=False,authoritative:bool=False):
        self.values = values
        self.authorities = authorities
        self.extra_values = extra_values
        self.final = final or len(self.values) != 0
        self.authoritative = authoritative
    
    @staticmethod
    def from_entries(query:QueryInfo, entries:list[DNSEntry], final:bool=False, authoritative:bool = False) -> 'QueryResponse':
        """
        Searches the given DNSEntry's for a response to the given query and constructs a QueryResponse
        with the relevant values, authorities and extra_values and the specified authoritative flag
        """
        
        vals = list(filter(lambda e: e.type == query.type and e.parameter == query.name, entries))
        vals = [min(vals, key=lambda e: e.priority)] if vals else []

        all_auths = {}
        for e in entries:
            if e.type == EntryType.NS and utils.is_subdomain(e.parameter, query.name):
                if e.parameter not in all_auths or e.priority < all_auths[e.parameter].priority:
                    all_auths[e.parameter] = e
        auths = all_auths.values()
        
        extra_dom = set(__get_relevant_domains__(vals) + [e.value for e in auths]) #dump in set to remove duplicates
        extras = list(utils.flat_map(lambda d: filter(lambda e: e.type == EntryType.A and e.parameter == d, entries), extra_dom))

        return QueryResponse(vals, auths, extras, final, authoritative)
    
    @staticmethod
    def from_top_servers(topServers:list[str]):
        ttl = 1000000000
        enumerated = enumerate(topServers, 1)
        authorities = [DNSEntry('.', EntryType.NS, f'dns{i}.', ttl) for i,_ in enumerated]
        extras = [DNSEntry(f'dns{i}.', EntryType.A, st, ttl) for i,st in enumerated]
        return QueryResponse([], authorities, extras, False, False)
    
    def isFinal(self) -> bool:
        """
        Whether the response provides a definitive anwer to the query
        (responseCode is either 0 or 2).
        """
        return self.final
    
    
def __get_relevant_domains__(entries:list[DNSEntry]) -> list[str]:
    """gets the values of SOASP,NS and MX entries

    Args:
        entries (list): a list of entries

    Returns:
        list: a list of the values of the entries (with a . in the end if MX)
    """
    ans = []
    
    for e in entries:
        if e.type in [EntryType.SOASP, EntryType.NS]:
            ans.append(e.value)
        elif e.type == EntryType.MX:
            ans.append(e.value + '.')
        
    return ans