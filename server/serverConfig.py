from enum import Enum
from .exceptions import InvalidConfigFileException, NoConfigFileException
from common.dnsEntry import DNSEntry
import common.utils as utils
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
    
    
CONFIG_TYPE = f'({"|".join(ConfigType.get_all())})'


class ServerConfig:
    def __init__(self, filePath):
        self.domains = {} #TODO: separar em primary e secondary???
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
        
        self.domains[domain.lower()].replaceDomainEntries(newEntries) #TODO: entries to lower case
        
    #returns a list of all DNS entries that match the queried hostname and valuetype
    #TODO: authoritative values and extra values
    def answer_query(self, hostname, value_type):
        hostname = hostname.lower()
        default = self.defaultServers[hostname]
        
        if default == None:
            return #TODO: if sp/ss, ignore query
                   #      if sr, make queries/look at cache
        elif default == '127.0.0.1':
            ans = []
            for name,domain in self.domains.items():
                if utils.is_subdomain(hostname, name):    #TODO: make more eficient (suffix trees?)
                    ans += domain.answer_query(hostname, value_type)
            return ans
        else:
            return #TODO: query server 'default'/cache
            #TODO: recursive vs iterative
        
    def get_log_files(self, domain_name):
        domain_name = domain_name.lower()
        if domain_name not in self.domains:
            return self.logFiles
        
        logs = self.domains[domain_name].logFiles
        if logs == []:
            return self.logFiles
        else:
            return logs

    #fetches the domain with the given domain and primary status
    #if it doesn't exist, it is created. if the primary status isn't specified, an error is raised
    #if a domain with the same name but wrong primary status exists, an error is raised
    def get_domain(self, domain_name, primary = None):
        domain_name = domain_name.lower()
        d = self.domains[domain_name]
        
        if d == None:
            if primary == None:
                raise InvalidConfigFileException(domain_name + " domain doesn't exist")
            
            d = Domain(domain_name, primary)
            self.domains[domain_name] = d
            
        if d.primary != primary:
            raise InvalidConfigFileException(domain_name + " domain is treated as both SP and SS")
        
        return d
    
    def get_primary_domains(self):
        return filter(lambda d: d.primary, self.domains)
    
    def get_secondary_domains(self):
        return filter(lambda d: not d.primary, self.domains)
    
    def __parseLine__(self, line):
        if re.search('(^$)|(^\s#)', line):
            return

        match = re.search(f'^\s*({utils.DOMAIN})\s+({CONFIG_TYPE})\s+(.+?)\s*$', line)
        if match == None:
            raise InvalidConfigFileException(line + " doesn't match the pattern \{domain\} \{ConfigType\} \{data\}")
        
        domain, valueType, data = match.group(1).lower(), match.group(2), match.group(3)

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
                if not re.search(f'^{utils.IP_ADDRESS}$', data):
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