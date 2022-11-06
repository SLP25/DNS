from enum import Enum
from .exceptions import InvalidConfigFileException, NoConfigFileException
from common.dnsEntry import DNSEntry
from domain import Domain
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
    
    
VALID_DOMAIN_CHAR = '[a-zA-Z0-9\-]'
DOMAIN = f'({VALID_DOMAIN_CHAR}+\.)*{VALID_DOMAIN_CHAR}+'
CONFIG_TYPE = f'({"|".join(ConfigType.get_all())})'
BYTE_RANGE = '([0-1]?[0-9]?[0-9]?|2[0-4][0-9]|25[0-5])'
IP_ADDRESS = f'({BYTE_RANGE}\.){{3}}{BYTE_RANGE}'

class ServerConfig:
    def __init__(self, filePath):
        self.domains = {}
        self.defaultServers = {} #domain:value
        self.topServers = [] #ips
        self.logFiles = []

        try:
            with open(filePath, "r") as file:
                lines = file.readlines()

                for line in lines:
                    self.__parseLine__(line)
                    
                if self.logFiles == []:
                    raise InvalidConfigFileException("No global log files specified")
                
                for d in self.domains.values():
                    d.validate()

        except FileNotFoundError:
            raise NoConfigFileException("Could not open " + filePath)
        
    def replaceDomainEntries(self, domain, newEntries):
        #TODO: Thread safety
        """
        Replaces all entries of a certain domain with the given new entries.
        Used to update the copy of the original database in an SS after a zone transfer.

        This method WILL BE thread safe.

        More specifically, this method erases all entries for the domain in the copy of the database,
        and inserts the new ones in their place

        Arguments:

        domain     : String                                               -> The given domain
        newEntries : Dict (Domain : String, Type : EntryType) => DNSEntry -> A dict with the new entries
        """
        self.domains.replaceDomainEntries(newEntries)
        
    #returns a list of all DNS entries that match the queried hostname and valuetype
    def answer_query(self, hostname, value_type):
        default = self.defaultServers[hostname]
        
        if default == '127.0.0.1':
            domain = self.domains
            
            if domain == None:
                return #TODO: ?
            else:
                return domain.answer_query(hostname, value_type)
        else:
            return #TODO: query server 'default'
            #TODO: recursive vs iterative
        
    def get_log_files(self, domain):
        if domain not in self.domains:
            return self.logFiles
        
        logs = self.domains[domain].logFiles
        if logs == []:
            return self.logFiles
        else:
            return logs

    #fetches the domain with the given domain and primary status
    #if it doesn't exist, it is created. if the primary status isn't specified, an error is raised
    #if a domain with the same name but wrong primary status exists, an error is raised
    def __get_domain__(self, domain, primary = None):
        d = self.domains[domain]
        
        if d == None:
            if primary == None:   #TODO: fix
                raise InvalidConfigFileException(domain + " domain doesn't exist")
            
            d = Domain(domain, primary)
            self.domains[domain] = d
            
        if d.primary != primary:
            raise InvalidConfigFileException(domain + " domain is treated as both SP and SS")
        
        return d
    
    def __parseLine__(self, line):
        if re.search('(^$)|(^\s#)', line):
            return

        match = re.search(f'^\s*({DOMAIN})\s+({CONFIG_TYPE})\s+(.+?)\s*$', line)
        if match == None:
            raise InvalidConfigFileException(line + " doesn't match the pattern \{domain\} \{ConfigType\} \{data\}")
        
        domain, valueType, data = match.group(1), match.group(2), match.group(3)

        try:
            lineType = ConfigType[valueType]
            
            if lineType == ConfigType.DB:
                self.__get_domain__(domain, True).set_databse(data)
            elif lineType == ConfigType.SP:
                self.__get_domain__(domain, False).set_primary_server(data)
            elif lineType == ConfigType.SS:
                self.__get_domain__(domain, True).add_authorizedSS(data)
            elif lineType == ConfigType.DD:
                if domain in self.defaultServers:
                    raise InvalidConfigFileException(f"Duplicated DD on domain {domain}")
                if not re.search(f'^{IP_ADDRESS}$', data):
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
                    self.__get_domain__(domain).add_log_file(data)
                    
        except ValueError:
            raise InvalidConfigFileException(line + " has no valid type")