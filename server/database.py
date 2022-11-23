"""
File responsible for parsing and storing SP's databases

Last Modification: Added documentation
Date of Modification: 14/11/2022 12:03
"""

import re
from common.query import QueryInfo
from common.query import QueryResponse
import common.utils as utils
from common.dnsEntry import DNSEntry, ENTRY_TYPE, PARAMETER_CHAR, EntryType
from server.exceptions import InvalidConfigFileException, InvalidDatabaseException


class Database:
    """
    Represents a SP's database
    Contains the following attributes:
        macros  -> Dict[str,str]
        aliases -> Dict[str,str]
        entries -> List[DNSEntry]
    """
    
    def __init__(self, path:str):
        """
        Constructs a database from the given database file
        If the path to the file is invalid, an InvalidConfigFileException is raised
        If the parsing of the file fails, an InvalidDatabaseException is raised
        """
        self.macros = {}
        self.aliases = {}
        self.entries = []
        self.serial = 0
        
        try:
            with open(path,'r') as file:
                lines = file.readlines()
        except:
            raise InvalidConfigFileException(f"invalid database file {path}")
        
        for line in lines:#this way we can get a list of all lines
            self.__process_line__(line.rstrip('\n'))
                
        self.get_origin()
            
            
    def get_origin(self):     
        if '@' not in self.macros:
            raise InvalidDatabaseException('Origin (@) not found')
        
        return self.macros['@']
    
    def __complete_domain__(self, domain):
        if domain[-1] == '.':
            return domain
        
        origin = self.get_origin()
        return domain + '.' + (origin if origin != '.' else '')
    
    def __replace_macros__(self, exp):
        for k,v in self.macros.items():
            exp = exp.replace(k, v)
        return exp
    
    def __replace_aliases__(self, domain):
        for k,v in self.macros.items():
            domain = domain.replace(k, v)
        return domain
    
    def __process_line__(self, line):
        if re.search(utils.COMMENT_LINE, line):
            return
        
        match = re.search(f'^\s*(?P<k>{PARAMETER_CHAR}+)\s+DEFAULT\s+(?P<v>[^\s]*)\s*$', line)
        if match != None:
            if match.group('k') == '@' and not re.search(f'^{utils.FULL_DOMAIN}$', match.group('v')):
                raise InvalidDatabaseException(f"{match.group('v')} isn't a valid dabatase origin (@)")
            self.macros[match.group('k')] = match.group('v')
            return
        
        match = re.search(f'^\s*(?P<k>{utils.DOMAIN})\s+CNAME\s+(?P<v>{utils.DOMAIN})\s+(?P<ttl>\d+)\s*$', line)
        if match != None:
            self.aliases[match.group('k')] = match.group('v')   #TODO: TTL???
        
        match = re.search(
            f'^\s*(?P<p>{PARAMETER_CHAR}+)\s+(?P<t>{ENTRY_TYPE})\s+(?P<v>[^\s]+)\s+(?P<ttl>\d+)(\s+(?P<pr>\d+))?\s*$',
            self.__replace_macros__(line))
        
        if match == None:
            raise InvalidDatabaseException(f"{line} doesn't match the pattern {{parameter}} {{type}} {{value}} {{ttl}} {{priority}}?")
    
        parameter = match.group('p')
        type = match.group('t')
        value = match.group('v')
        ttl = match.group('ttl')
        priority = match.group('pr')
        
        if type in ['SOASP', 'SOAADMIN', 'SOASERIAL', 'SOAREFRESH', 'SOARETRY', 'SOAEXPIRE', 'NS', 'MX', 'A']:
            parameter = self.__complete_domain__(parameter)
        
        if type in ['SOASP', 'NS', 'PTR']:
            value = self.__complete_domain__(value)
        
        ans = DNSEntry.from_text(parameter,type,value,ttl,priority)
        self.entries.append(ans)
        
        if ans.type == EntryType.SOASERIAL:
            self.serial = int(ans.value)
    
    def answer_query(self, query:QueryInfo):
        """
        Answers the query with the available DNSEntry's
        Returns a QueryResponse
        """
        hostname = self.__replace_aliases__(query.name)
        return QueryResponse.from_entries(QueryInfo(hostname, query.type), self.entries, True)