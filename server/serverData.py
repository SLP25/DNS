"""
File containing enum class ConfigType and class ServerData
This file is reponsible for handling the interaction between the server and its stored data

Last Modification: Added documentation
Date of Modification: 14/11/2022 14:58
"""

from enum import Enum
import math
from typing import List, Optional
from common.query import QueryInfo
from common.query import QueryResponse
from .exceptions import InvalidConfigFileException, NoConfigFileException
from common.dnsEntry import DNSEntry, EntryType
import common.utils as utils
from .domain import Domain, PrimaryDomain, SecondaryDomain
import re


class ConfigType(Enum):
    """
    Represents the type of value in the configuration file of a server
    """
    
    DB = 0
    SP = 1
    SS = 2
    DD = 3
    ST = 4
    LG = 5
    
    @staticmethod
    def get_all():
        """
        Returns a list containing the names of all ConfigType's
        """
        return [e.name for e in ConfigType]
    
"""
A regex pattern that matches all names of ConfigType's
"""
CONFIG_TYPE = f'({"|".join(ConfigType.get_all())})'


class ServerData:
    """
    Is responsible for storing all configuration data of the server. This includes:
        domains         -> Dict[str,Domain] (stored by (full) domain name)
        defaultServers  -> Dict[str,str] (full domain name to ip addresses)
        topServers      -> List[str] (ip adresses)
        logFiles        -> List[str] (file names)
    """
    
    def __init__(self, filePath:str):
        """
        Constructs an instance of ServerData from the given path to a server configuration file
        """
        
        self.domains = {}   #name:domain  #TODO: separar em primary e seconday??
        self.defaultServers = {}    #domain:value
        self.topServers = []    #ips
        self.logFiles = []      #file names

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
        
    def replaceDomainEntries(self, domain:str, new_entries:List[DNSEntry]):
        """
        Replaces the entries of the given secondary domain
        This method is called during zone transfers
        If no such secondary domain exists, an error is raised
        
        Arguments:
            domain_name -> A valid domain name (matches DOMAIN or FULL_DOMAIN). Case and termination insensitive
            new_entries -> A list of dnsEntry's to replace the current entries
        """
        self.get_domain(domain, False).set_entries(new_entries)
        
    def get_log_files(self, domain_name:str):
        """
        Determines the list of log files that should be used when logging
        events about the given domain
        Returns a list of log file paths
        
        Arguments:
            domain_name -> A valid domain name (matches DOMAIN or FULL_DOMAIN). Case and termination insensitive
        """
        domain_name = utils.normalize_domain(domain_name)
        
        if domain_name not in self.domains:
            return self.logFiles
        
        logs = self.domains[domain_name].logFiles
        if logs == []:
            return self.logFiles
        else:
            return logs
        
    def get_first_servers(self, domain_name:str):   #TODO: return all matches, ordered from most to least specific?
        """
        Determines the first servers to ask if a query can't be answered locally. This is
        the top servers if no default domain is set, or the default server (+ the roots) if it is
        Returns a list of ip addresses
        
        Arguments:
            domain_name -> A valid domain name (matches DOMAIN or FULL_DOMAIN). Case and termination insensitive
        """
        d = utils.best_match(domain_name, self.defaultServers)
        if d:
            return [self.defaultServers[d]] + self.topServers
        else:
            return self.topServers
            
    def answer_query(self, query:QueryInfo):    #TODO: add answers from all domains instead? least specific first?
        """
        Attempts to answer the given query using the stored domains (SP and SS)
        Returns a QueryResponse
        If no answer could be found, an empty QueryResponse is returned
        """
        d = utils.best_match(query.name, self.domains)
        if d:
            return self.domains[d].answer_query(query)
        else:
            return QueryResponse()

    def get_domain(self, domain_name:str, primary:Optional[bool] = None, create:bool = False):
        """
        Fetches the domain with the given domain name and specified primary status
        Returns a Domain, or raises an error if no such domain exists
        
        Arguments:
            domain_name -> A valid domain name (matches DOMAIN or FULL_DOMAIN). Case and termination insensitive
            primary     -> Whether the domain to fetch is primary or not (secondary). If None, both types of domain match
            create      -> Whether to create a domain instead of raising an error when no matching domain is found.
                            If a creation operation is triggered and primary is None, an error is raised
        """     
        domain_name = utils.normalize_domain(domain_name)
        if domain_name not in self.domains:
            if not create or primary == None:
                raise ValueError(f"Domain {domain_name} doesn't exist")
            
            if primary:
                d = PrimaryDomain(domain_name)
            else:
                d = SecondaryDomain(domain_name)

            self.domains[domain_name] = d
        else:
            d = self.domains[domain_name]

            if primary != None:
                if primary and isinstance(d, SecondaryDomain):
                    raise ValueError(f"Secondary domain {domain_name} is treated as a primary domain")
                if not primary and isinstance(d, PrimaryDomain):
                    raise ValueError(f"Primary domain {domain_name} is treated as a secondary domain")
         
        return d
    
    def get_primary_domains(self):
        """
        Returns a list containing all primary domains (Domain) in the current instance
        """
        return filter(lambda d: d.primary, self.values())
    
    def get_secondary_domains(self):
        """
        Returns a list containing all secondary domains (Domain) in the current instance
        """
        return filter(lambda d: not d.primary, self.domains.values())
    
    def __parseLine__(self, line):
        if re.search(utils.COMMENT_LINE, line):
            return

        match = re.search(f'^\s*(?P<d>{utils.DOMAIN}|\.)\s+(?P<t>{CONFIG_TYPE})\s+(?P<v>[^\s]+)\s*$', line)
        if match == None:
            raise InvalidConfigFileException(f"{line} doesn't match the pattern {{domain}} {{ConfigType}} {{data}}")
        
        domain = utils.normalize_domain(match.group('d'))
        valueType = match.group('t')
        data = match.group('v')

        try:
            lineType = ConfigType[valueType]
            
            if lineType == ConfigType.DB:
                self.get_domain(domain, True, True).set_databse(data)
            elif lineType == ConfigType.SP:
                self.get_domain(domain, False, True).set_primary_server(data)
            elif lineType == ConfigType.SS:
                self.get_domain(domain, True, True).add_authorizedSS(data)
            elif lineType == ConfigType.DD:
                if domain in self.defaultServers:
                    raise InvalidConfigFileException(f"Duplicated DD on domain {domain}")
                if not re.search(f'^{utils.IP_MAYBE_PORT}$', data):
                    raise InvalidConfigFileException(f"Invalid ip address {data}")
                self.defaultServers[domain] = data
            elif lineType == ConfigType.ST:
                if domain != 'root.':
                    raise InvalidConfigFileException(f"ST parameter was {domain} expected root")
                try:
                    with open(data,'r') as file:
                        self.topServers+=file.readlines() #TODO: check values
                except:
                    raise InvalidConfigFileException(f"invalid ST file {data}")
            elif lineType == ConfigType.LG:
                if domain == 'all.':
                    self.logFiles.append(data) #TODO: check data
                else:
                    self.get_domain(domain, create=True).add_log_file(data)
                    
        except ValueError:
            raise InvalidConfigFileException(line + " has no valid type")