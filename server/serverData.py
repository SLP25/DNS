"""
File containing enum class ConfigType and class ServerData
This file is reponsible for handling the interaction between the server and its stored data

Last Modification: Added documentation
Date of Modification: 14/11/2022 14:58
"""

from enum import Enum
import math
from typing import Iterable, List, Optional
from common.query import QueryInfo
from common.query import QueryResponse
from .exceptions import InvalidConfigFileException, InvalidTopServersException, NoConfigFileException
from common.dnsEntry import DNSEntry, EntryType
import common.utils as utils

from common.logger import LogCreate,LogMessage,LoggingEntryType
from multiprocessing import Queue

from .domain import Domain, PrimaryDomain, SecondaryDomain
from collections import OrderedDict
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
    def get_all() -> list[str]:
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
        domains         -> OrderedDict[str,Domain] (stored by (full) domain name, ordered from higher to lower in the hierarchy)
        defaultServers  -> Dict[str,str] (full domain name to ip addresses)
        topServers      -> List[str] (ip adresses)
    """
    
    def __init__(self, filePath:str,logger:Queue):
        """
        Constructs an instance of ServerData from the given path to a server configuration file
        """
        
        self.logger=logger
        self.domains = OrderedDict()        #name:domain            separar em primary e seconday?
        self.defaultServers = OrderedDict() #domain name:ip[:port]
        self.topServers = []                #ips
        self.loggers = []                   #file paths
        self.count = 0

        try:
            with open(filePath, "r") as file:
                for line in file.readlines():
                    self.__parseLine__(line.rstrip('\n'))
                    
                if len(self.loggers) == 0:
                    raise InvalidConfigFileException("No global log files specified")
                
                if len(self.topServers) == 0:
                    raise InvalidConfigFileException("No top servers specified")
                
                #reorder domains to the correct order (from higher to lower in the hierarchy)
                self.domains = utils.order_dict(self.domains, lambda d: len(utils.split_domain(d)))
                self.defaultServers = utils.order_dict(self.defaultServers, lambda d: len(utils.split_domain(d)))
                
                for d in self.domains.values():
                    d.validate()

        except FileNotFoundError:
            raise NoConfigFileException("Could not open " + filePath)
    
    def set_domain(self, domain_name:str, domain:Domain) -> None:
        self.domains[domain_name] = domain
    
    def replaceDomainEntries(self, domain:str, new_entries:list[DNSEntry]) -> None:
        """
        Replaces the entries of the given secondary domain
        This method is called during zone transfers
        If no such secondary domain exists, an error is raised
        
        Arguments:
            domain_name -> A valid domain name (matches DOMAIN or FULL_DOMAIN). Case and termination insensitive
            new_entries -> A list of dnsEntry's to replace the current entries
        """
        self.get_domain(domain, False).set_entries(new_entries)
        
        
    def get_first_servers(self, domain_name:str) -> QueryResponse:
        """
        Determines the first servers to ask if a query can't be answered locally. This is
        the top servers if no default domain is set, or the default server if it is
        Returns a query response with the relevant information in the authorities and extra values fields
        
        Arguments:
            domain_name -> A valid domain name (matches DOMAIN or FULL_DOMAIN). Case and termination insensitive
        """
        matches = filter(lambda d: d != '127.0.0.1' and utils.is_subdomain(domain_name, d), self.defaultServers)
        domain = next(matches, None)

        if domain:
            dd_address = self.defaultServers[domain]
            dd_name = f"ns.{domain}"
            ttl = 1000000000
            return QueryResponse([], [DNSEntry(domain, EntryType.NS, dd_name, ttl)], \
                                     [DNSEntry(dd_name, EntryType.A, dd_address, ttl)])
        else:
            return QueryResponse.from_top_servers(self.topServers)
        
    def answers_query(self, d:str) -> bool:
        """
        Determines whether the current config allows the server to answer a query
        on the given domain. This is true if either no default servers were indicated,
        or if the given domain is a subdomain of one of the default servers
        """
        for k in self.defaultServers:
            if utils.is_subdomain(d, k):
                return True

        return len(self.defaultServers) == 0
        
    def answer_query(self, query:QueryInfo) -> QueryResponse:
        """
        Attempts to answer the given query using the stored domains (SP and SS)
        Returns a QueryResponse
        If no answer could be found, an empty QueryResponse is returned
        """
        matches = filter(lambda d: utils.is_subdomain(query.name, d.name), self.domains.values())
        
        for d in matches:
            final = utils.domain_depth(query.name) - 1 == utils.domain_depth(d.name)
            return d.answer_query(query, final)

        return QueryResponse()

    def get_domain(self, domain_name:str, primary:Optional[bool] = None, create:bool = False) -> Domain:
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
    
    def get_primary_domains(self) -> Iterable[Domain]:
        """
        Returns a list containing all primary domains (Domain) in the current instance
        """
        return filter(lambda d: d.primary, self.domains.values())

    def get_secondary_domains(self) -> Iterable[Domain]:
        """
        Returns a list containing all secondary domains (Domain) in the current instance
        """
        return list(filter(lambda d: isinstance(d, SecondaryDomain), self.domains.values()))

    def __parseLine__(self, line:str) -> None:
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
                self.get_domain(domain, True, True).set_database(data)
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
                        for line in file.readlines():
                            if not re.search(f'^{utils.IP_MAYBE_PORT}$', line):
                                raise InvalidTopServersException(f"{line} isn't a valid IP address")

                            self.topServers.append(line)
                except:
                    raise InvalidConfigFileException(f"invalid ST file {data}")
            elif lineType == ConfigType.LG:
                if domain == 'all.':
                    self.logger.put(LogCreate(data))
                    self.loggers.append(data)
                else:
                    self.logger.put(LogCreate(data, domain))
                    
        except ValueError:
            raise InvalidConfigFileException(line + " has no valid type")