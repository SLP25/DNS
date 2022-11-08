from common.dnsEntry import DNSEntry
from server.exceptions import InvalidConfigFileException
import re
import common.utils as utils
from server.database import Database

class Domain:
    def __init__(self, name):
        self.name = name
        self.logFiles = []   #allow only one???
    
        
    def add_log_file(self, log_file): #TODO: check value/open file immediately
        self.logFiles.append(log_file)
        
class PrimaryDomain(Domain):
    def __init__(self, name):
        super().__init__(name)
        self.authorizedSS = []
        self.database = None
        
    def set_databse(self, path):        
        if self.database != None:
            raise InvalidConfigFileException("Duplicated DB for domain " + self.name)
        
        self.database = Database(path)
        
    def add_authorizedSS(self, authorizedSS):  
        if not re.search(f'^{utils.IP_MAYBE_PORT}$', authorizedSS):
            raise InvalidConfigFileException(f"Invalid ip address {authorizedSS}")
        
        self.authorizedSS.append(authorizedSS)
        
    def validate(self):
        if self.database == None:
            raise InvalidConfigFileException("No database file specified for primary domain " + self.name)
        
    def get_entries(self):
        return self.database.entries
    
    def answer_query(self, hostname, value_type):
            return self.database.answer_query(hostname, value_type)
    
class SecondaryDomain(Domain):
    def __init__(self, name):
        super().__init__(name)
        self.primaryServer = None
        self.dnsEntries = None
    
    def set_primary_server(self, primary_server):        
        if self.primaryServer != None:
            raise InvalidConfigFileException("Duplicated SP for domain " + self.name)
        
        if not re.search(f'^{utils.IP_ADDRESS}$', primary_server):
            raise InvalidConfigFileException(f"Invalid ip address {primary_server}")
        
        #split = data.split(":")
        #TODO: Throw exception if invalid ip:port
        #self.primaryDomains[domain]=(split[0], int(split[1]))
        #self.primaryServer = primary_server
        
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
        new_entries : Dict (Domain : String, Type : EntryType) => DNSEntry -> A dict with the new entries
        """
    def set_entries(self, new_entries):
        self.dnsEntries = new_entries
        
    def get_entries(self):
        return self.dnsEntries
    
    def answer_query(self, hostname, value_type):
        return self.dnsEntries.filter(lambda e: e.type == value_type and e.parameter == hostname)