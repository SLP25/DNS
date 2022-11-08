import re
from common.dnsEntry import DNSEntry, ENTRY_TYPE
from server.exceptions import InvalidConfigFileException, InvalidDatabaseException

PARAMETER_CHAR = '[a-zA-Z0-9\-@]'


class Database:
    
    def __init__(self, file):
        self.macros = {}
        self.entries = []
        
        try:
            with open(file,'r') as file:
                for line in file.readlines():#this way we can get a list of all lines
                    self.__process_line__(line.rstrip('\n'))
        except:
            raise InvalidConfigFileException(f"invalid database file {file}")
                
        self.__get_origin__()
            
            
    def __get_origin__(self):
        origin = self.macros['@']
        
        if origin == None:
            raise InvalidDatabaseException('Origin (@) not found')
            
        return origin
    
    def __replace_macros__(self, exp):
        for k,v in self.macros.items:
            exp = exp.replace(k, v)
    
    def __process_line__(self, line):
        if re.search('^\s*#', line) or re.search('^\s*$', line):
            return
        
        match = re.search(f'^\s*({PARAMETER_CHAR}+)\s+DOMAIN\s+(.+?)\s*$', line)
        if match != None:
            self.macros[match.group(1)] = match.group(2)
            return
        
        match = re.search(
            f'^\s*({PARAMETER_CHAR}+)\s+({ENTRY_TYPE})\s+(.+?)\s+(\d+)\s+(\d+)?\s*$',
            self.__replace_macros__(line))
        if match != None:
            parameter = match.group(1)
            type = match.group(2)
            value = match.group(3)
            ttl = match.group(4)
            priority = match.group(5)
            
            if priority == None:
                ans = DNSEntry(parameter,type,value,ttl)
            else:
                ans = DNSEntry(parameter,type,value,ttl,priority)
                
            self.entries.append(ans)
            return
    
    def answer_query(self, hostname, value_type):
        return self.entries.filter(lambda e: e.type == value_type and e.parameter == hostname)