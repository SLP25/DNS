from enum import Enum
import math
from common.query import QueryInfo
from common.query import QueryResponse
from .exceptions import InvalidConfigFileException, NoConfigFileException
from common.dnsEntry import DNSEntry, EntryType
import common.utils as utils
from .domain import Domain, PrimaryDomain, SecondaryDomain
import re


class ConfigType(Enum):
    DB = 0
    SP = 1
    SS = 2
    DD = 3
    ST = 4
    LG = 5
    
    @staticmethod
    def get_all():
        return [e.name for e in ConfigType]
    
    
CONFIG_TYPE = f'({"|".join(ConfigType.get_all())})'


class ServerData:
    def __init__(self, filePath:str):
        self.domains = {} #TODO: separar em primary e secondary???
        self.defaultServers = {} #domain:value
        self.topServers = [] #ips
        self.logFiles = []

        try:
            with open(filePath, "r") as file:
                for line in file.readlines():
                    self.__parseLine__(line.rstrip('\n'))
                    
                if self.logFiles == []:
                    raise InvalidConfigFileException("No global log files specified")
                
                for d in self.domains.values():
                    d.validate()

        except FileNotFoundError:
            raise NoConfigFileException("Could not open " + filePath)
        
    def replaceDomainEntries(self, domain:str, newEntries):
        self.get_domain(domain, False).set_entries(newEntries) #TODO: entries to lower case?
        
    def get_log_files(self, domain_name:str):
        if domain_name not in self.domains:
            return self.logFiles
        
        logs = self.domains[domain_name].logFiles
        if logs == []:
            return self.logFiles
        else:
            return logs
        
    def get_default_server(self, domain:str):   #TODO: returns all matches, ordered from most to least specific (+roots?)
        d = utils.best_match(domain, self.defaultServers)
        if d:
            return self.defaultServers[d]
            
    def answer_query(self, query:QueryInfo):    #TODO: add answers from all domains instead? least specific first?
        d = utils.best_match(query.name, self.domains)
        if d:
            return self.domains[d].answer_query(query)
        else:
            return QueryResponse()

    #fetches the domain with the given name and primary status
    #if it doesn't exist, it is created. if the primary status isn't specified, an error is raised
    #if a domain with the same name but wrong primary status exists, an error is raised
    def get_domain(self, domain_name:str, primary = None):
        domain_name = domain_name.lower()
        if domain_name not in self.domains:
            if primary == None:
                raise InvalidConfigFileException(f"Domain {domain_name} doesn't exist")
            
            if primary:
                d = PrimaryDomain(domain_name)
            else:
                d = SecondaryDomain(domain_name)

            self.domains[domain_name] = d
        else:
            d = self.domains[domain_name]

            if primary != None:
                if primary and isinstance(d, SecondaryDomain):
                    raise InvalidConfigFileException(f"Secondary domain {domain_name} is treated as a primary domain")
                if not primary and isinstance(d, PrimaryDomain):
                    raise InvalidConfigFileException(f"Primary domain {domain_name} is treated as a secondary domain")
         
        return d
    
    def get_primary_domains(self):
        return filter(lambda d: d.primary, self.values())
    
    def get_secondary_domains(self):
        return filter(lambda d: not d.primary, self.domains.values())
    
    def __parseLine__(self, line):
        if re.search(utils.COMMENT_LINE, line):
            return

        match = re.search(f'^\s*(?P<d>{utils.DOMAIN})\s+(?P<t>{CONFIG_TYPE})\s+(?P<v>[^\s]+)\s*$', line)
        if match == None:
            raise InvalidConfigFileException(f"{line} doesn't match the pattern {{domain}} {{ConfigType}} {{data}}")
        
        domain = match.group('d').lower()
        valueType = match.group('t')
        data = match.group('v')

        try:
            lineType = ConfigType[valueType]
            
            if lineType == ConfigType.DB:
                self.get_domain(domain, True).set_databse(data)
            elif lineType == ConfigType.SP:
                self.get_domain(domain, False).set_primary_server(data)
            elif lineType == ConfigType.SS:
                self.get_domain(domain, True).add_authorizedSS(data)
            elif lineType == ConfigType.DD:
                if domain in self.defaultServers:
                    raise InvalidConfigFileException(f"Duplicated DD on domain {domain}")
                if not re.search(f'^{utils.IP_MAYBE_PORT}$', data):
                    raise InvalidConfigFileException(f"Invalid ip address {data}")
                self.defaultServers[domain] = data
            elif lineType == ConfigType.ST:
                if domain != 'root':
                    raise InvalidConfigFileException(f"ST parameter was {domain} expected root")
                try:
                    with open(data,'r') as file:
                        self.topServers+=file.readlines() #TODO: check values
                except:
                    raise InvalidConfigFileException(f"invalid ST file {data}")
            elif lineType == ConfigType.LG:
                if domain == 'all':
                    self.logFiles.append(data) #TODO: check data
                else:
                    self.get_domain(domain).add_log_file(data)
                    
        except ValueError:
            raise InvalidConfigFileException(line + " has no valid type")