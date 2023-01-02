"""
File implementing the cache
The cache stores received answers from previously asked queries and can be
queried to prevent redundant queries to dns servers

Last Modification: Added documentation
Date of Modification: 14/11/2022 11:53
"""

import traceback
from typing import Optional
import time
import itertools
from common.dnsEntry import DNSEntry
from common.query import QueryInfo
from common.query import QueryResponse


class CacheLine:
    """
    Represents a line (minimum storing unit) of the cache
    Each line has the following attributes:
        dnsEntry    -> DNSEntry
        limitDate   -> float (seconds after the epoch)
    """
    
    def __init__(self, dnsEntry:DNSEntry, limitDate:float):
        self.dnsEntry = dnsEntry
        self.limitDate = limitDate
        
#TODO: hash tables/other optimizations?
class Cache:
    """
    Stores DNSEntry's and answers queries using the still valid entries
    """
    
    def __init__(self):
        """
        Constructs an empty cache
        """
        self.lines:list[CacheLine] = []
        self.negative:dict[QueryInfo,float] = {}
        
    def add_entry(self, dnsEntry:DNSEntry) -> None:
        """
        Adds a DNSEntry to the cache
        """
        self.lines.append(CacheLine(dnsEntry, time.time() + dnsEntry.ttl))
        
    def answer_query(self, query:QueryInfo) -> QueryResponse:
        """
        Searches the valid entries to answer the query
        Returns a QueryResponse
        """
        cur_time = time.time()

        if query in self.negative:
            if self.negative[query] >= cur_time:
                return QueryResponse([],[],[],True)
            else:
                del self.negative[query]

        self.lines = list(filter(lambda l: l.limitDate >= cur_time, self.lines))

        return QueryResponse.from_entries(query, [l.dnsEntry for l in self.lines])
    
    def add_response(self, response:QueryResponse, query:Optional[QueryInfo]=None) -> None:
        """
        Adds all DNSEntry's in the given response to the cache
        """
        for entry in itertools.chain(response.values, response.authorities, response.extra_values):
            self.add_entry(entry)

        if query != None and response.isFinal() and len(response.values) == 0:
            self.negative[query] = time.time() + 60