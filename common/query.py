from common.dnsEntry import EntryType

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
        values = min(filter(lambda e: e.type == query.type and e.parameter == query.name, entries), key=lambda e: e.priority)
        #TODO: authorities & extra values
        return QueryResponse(values, [], [], authoritative)
    
    def positive(self):
        return self.values != []