import re
import common.utils as utils
from common.dnsEntry import DNSEntry, ENTRY_TYPE
from server.exceptions import InvalidConfigFileException, InvalidDatabaseException

PARAMETER_CHAR = '[a-zA-Z0-9.-@]'


class Database:
    
    def __init__(self, path):
        self.macros = {}
        self.entries = []
        
        try:
            with open(path,'r') as file:
                lines = file.readlines()
                
        except:
            raise InvalidConfigFileException(f"invalid database file {path}")
        
        for line in lines:#this way we can get a list of all lines
            self.__process_line__(line.rstrip('\n'))
                
        self.__get_origin__()
            
            
    def __get_origin__(self):     
        if '@' not in self.macros:
            raise InvalidDatabaseException('Origin (@) not found')
        
        return self.macros['@']
    
    def __complete_domain__(self, domain):
        if domain[-1] == '.':
            return domain
        
        return domain + self.__get_origin__()
    
    def __replace_macros__(self, exp):
        for k,v in self.macros.items():
            exp = exp.replace(k, v)
        return exp
    
    def __process_line__(self, line):
        if re.search(utils.COMMENT_LINE, line):
            return
        
        match = re.search(f'^\s*(?P<k>{PARAMETER_CHAR}+)\s+DEFAULT\s+(?P<v>[^\s]+)\s*$', line)
        if match != None:
            self.macros[match.group('k')] = match.group('v')
            return
        
        match = re.search(
            f'^\s*(?P<p>{PARAMETER_CHAR}+)\s+(?P<t>{ENTRY_TYPE})\s+(?P<v>[^\s]+)\s+(?P<ttl>\d+)(\s+(?P<pr>\d+))?\s*$',
            self.__replace_macros__(line))
        
        if match == None:
            print(ENTRY_TYPE)
            raise InvalidDatabaseException(f"{line} doesn't match the pattern {{parameter}} {{type}} {{value}} {{ttl}} {{priority}}?")
    
        parameter = match.group('p')
        type = match.group('t')
        value = match.group('v')
        ttl = match.group('ttl')
        priority = match.group('pr')
        
        if type == 'PTR':
            value = self.__complete_domain__(value)
        elif type != 'CNAME':   #TODO: perguntar ao lost sobre CNAME
            parameter = self.__complete_domain__(parameter)
        
        ans = DNSEntry.from_text(parameter,type,value,ttl,priority)
        self.entries.append(ans)
    
    def answer_query(self, hostname, value_type):
        return self.entries.filter(lambda e: e.type == value_type and e.parameter == hostname)