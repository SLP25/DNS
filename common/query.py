from common.dnsEntry import EntryType
import common.utils as utils
import itertools

class QueryInfo:
    def __init__(self, name:str, type:EntryType):
        self.name = name.lower()
        self.type = type
        
    def __str__(self):
        return f'{self.name},{self.type.name}'

class QueryResponse:
    def __init__(self, values = [], authorities = [], extra_values = [], authoritative = False):
        self.values = values
        self.authorities = authorities
        self.extra_values = extra_values
        self.authoritative = authoritative
    
    @staticmethod
    def from_entries(query:QueryInfo, entries, authoritative = False):
        #TODO: greatest priority or all? (enunciado diz all, lost diz priority)
        vals = list(filter(lambda e: e.type == query.type and e.parameter == query.name, entries))
        vals = [min(vals, key=lambda e: e.priority)] if vals else []

        all_auths = {}  #TODO: if query.type == NS, include auths anyway???
        for e in entries:
            if e.type == EntryType.NS and utils.is_subdomain(query.name, e.parameter):
                if e.parameter not in all_auths or e.priority < all_auths[e.parameter].priority:
                    all_auths[e.parameter] = e
        auths = all_auths.values()
        
        extra_dom = set(__get_relevant_domains__(vals) + [e.value for e in auths]) #dump in set to remove duplicates
        extras = list(utils.flat_map(lambda d: filter(lambda e: e.type == EntryType.A and e.parameter == d, entries), extra_dom))
        
        return QueryResponse(vals, auths, extras, authoritative)
    
    def positive(self):
        return self.values != []
    
    
def __get_relevant_domains__(entries):
    ans = []
    
    for e in entries:
        if e.type in [EntryType.SOASP, EntryType.NS]:
            ans.append(e.value)
        elif e.type == EntryType.MX:
            ans.append(e.value + '.')
        
    return ans