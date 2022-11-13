from common.dnsEntry import DNSEntry, EntryType
from common.query import QueryInfo
from common.query import QueryResponse
from server.exceptions import InvalidConfigFileException
import re
import common.utils as utils
from server.database import Database

class Domain:
    def __init__(self, name:str):
        self.name = name
        self.logFiles = []
    
        
    def add_log_file(self, log_file:str): #TODO: check value/open file immediately
        self.logFiles.append(log_file)
        
class PrimaryDomain(Domain):
    def __init__(self, name:str):
        super().__init__(name)
        self.authorizedSS = []
        self.database = None
        
    def set_databse(self, path:str):        
        if self.database != None:
            raise InvalidConfigFileException("Duplicated DB for domain " + self.name)
        
        self.database = Database(path)
        
    def add_authorizedSS(self, authorizedSS:str):  
        if not re.search(f'^{utils.IP_MAYBE_PORT}$', authorizedSS):
            raise InvalidConfigFileException(f"Invalid ip address {authorizedSS}")
        
        self.authorizedSS.append(authorizedSS)
        
    def validate(self):
        if self.database == None:
            raise InvalidConfigFileException("No database file specified for primary domain " + self.name)
    
    def answer_query(self, query:QueryInfo):
            return self.database.answer_query(query)
    
class SecondaryDomain(Domain):
    def __init__(self, name:str):
        super().__init__(name)
        self.primaryServer = None
        self.aliases = None
        self.dnsEntries = None
    
    def set_primary_server(self, primary_server:str):
        if self.primaryServer != None:
            raise InvalidConfigFileException("Duplicated SP for domain " + self.name)
        
        if not re.search(f'^{utils.IP_MAYBE_PORT}$', primary_server):
            raise InvalidConfigFileException(f"Invalid ip address {primary_server}")
        
        #split = data.split(":")
        #Throw exception if invalid ip:port
        #self.primaryDomains[domain]=(split[0], int(split[1]))
        self.primaryServer = primary_server
        
    def validate(self):
        if self.primaryServer == None:
            raise InvalidConfigFileException("No primary server specified for secondary domain " + self.name)
        
    #TODO: Thread safety
        """
        Replaces all entries of a certain domain with the given new entries.
        Used to update the copy of the original database in an SS after a zone transfer.

        This method WILL BE thread safe.

        More specifically, this method erases all entries for the domain in the copy of the database,
        and inserts the new ones in their place

        Arguments:
        new_entries : List (DNSEntry) -> A list with the new entries
        """
    def set_entries(self, new_entries):
        self.dnsEntries = new_entries
        self.aliases = {}
        for e in self.dnsEntries:
            if e.type == EntryType.CNAME:
                self.aliases[e.parameter] = e.value
    
    #TODO: Thread safety
    def answer_query(self, query:QueryInfo):
        hostname = self.__replace_aliases__(query.name)
        return QueryResponse.from_entries(QueryInfo(hostname, query.type), self.entries, True)
    
    def __replace_aliases__(self, domain:str):
        for k,v in self.macros.items():
            domain = domain.replace(k, v)
        return domain