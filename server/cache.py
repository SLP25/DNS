import time
import itertools
from common.dnsEntry import DNSEntry
from common.query import QueryInfo
from common.query import QueryResponse


class CacheLine:
    def __init__(self, dnsEntry, limitDate):
        self.dnsEntry = dnsEntry
        self.limitDate = limitDate
        
#TODO: negative caching
#TODO: hash tables/other optimizations?
class Cache:
    def __init__(self):
        self.lines = []
        
    def add_entry(self, dnsEntry:DNSEntry):
        self.lines.append(CacheLine(dnsEntry, time.time() + dnsEntry.ttl))
        
    def query(self, query:QueryInfo):
        cur_time = time.time()
        self.lines = list(filter(lambda l: l.limitDate < cur_time, self.lines))
        return QueryResponse.from_entries(query, [l.dnsEntry for l in self.lines], False)
    
    def add_response(self, response:QueryResponse):
        for entry in itertools.chain(response.values, response.authorities, response.extra_values):
            self.add_entry(entry)