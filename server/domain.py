from common.dnsEntry import DNSEntry
from server.exceptions import InvalidConfigFileException
import re
from server.serverConfig import IP_ADDRESS


class Domain:
    
    def __init__(self, name, primary):
        self.name = name
        self.primary = primary
        self.logFiles = []   #allow only one???
        self.dnsEntries = [] #TODO: database
        
        #if auth:
        self.authorizedSS = []
        
        #if not auth:
        self.primaryServer = None
        
    def set_databse(self, path):
        if self.primary != True:
            raise InvalidConfigFileException("DB for non-primary domain " + self.name)
        
        if self.database != None:
            raise InvalidConfigFileException("Duplicated DB for domain " + self.name)
        
        try:
            with open(path,'r') as file:
                lines=file.readlines()#this way we can get a list of all lines
        except:
            raise InvalidConfigFileException(f"invalid database file {path}")
        self.dnsEntries=[DNSEntry(line,fromFile=True) for line in lines]
        
        
    def set_primary_server(self, primary_server): #TODO: check value
        if self.primary != False:
            raise InvalidConfigFileException("SP for primary domain " + self.domain)
        
        if self.primaryServer != None:
            raise InvalidConfigFileException("Duplicated SP for domain " + self.name)
        
        if not re.search(f'^{IP_ADDRESS}$', primary_server):
            raise InvalidConfigFileException(f"Invalid ip address {primary_server}")
        
        #split = data.split(":")
        #TODO: Throw exception if invalid ip:port
        #self.primaryDomains[domain]=(split[0], int(split[1]))
        #self.primaryServer = primary_server
        
    def add_authorizedSS(self, authorizedSS): #TODO: check value
        if self.primary != True:
            raise InvalidConfigFileException("SS for non-primary domain " + self.domain)
        
        if not re.search(f'^{IP_ADDRESS}$', authorizedSS):
            raise InvalidConfigFileException(f"Invalid ip address {authorizedSS}")
        
        self.authorizedSS.append(authorizedSS)
        
    def add_log_file(self, log_file): #TODO: check value
        self.logFiles.append(log_file)
        
    
    def validate(self):
        #if self.primary and self.database == None:
        #    raise InvalidConfigFileException("No database file specified for primary domain " + self.name)
        
        if not self.primary and self.primaryServer == None:
            raise InvalidConfigFileException("No primary server specified for non-primary domain " + self.name)
    
    
    def replaceDomainEntries(self, newEntries):
        self.dnsEntries = newEntries
    
    def answer_query(self, hostname, value_type):
        #TODO: meter mais eficiente, ordenar por prioridades?
        return self.dnsEntries.filter(lambda e: e.type == value_type and e.parameter == hostname)