from enum import Enum
from exceptions import NoConfigFileException
from ..common.dnsEntry import DNSEntry

class ConfigType(Enum):
    DB = 0
    SP = 1
    SS = 2
    DD = 3
    ST = 4
    LG = 5

class ServerConfig:

            
    
    def __init__(self, filePath):
        self.primaryDomains = {}#domain:serverData
        self.dnsEntries = {}#domain:DNSEntry
        self.topServers = [] #ips
        self.logFile = None
        self.especificLogFiles = {} # domain:file
        self.authorizedSS = {}#domain:serverData
        self.defaultServers = {}#domain:serverData

        try:
            with open(filePath, "r") as file:
                lines = file.readlines()

                for line in lines:
                    self.__parseLine__(line)

        except FileNotFoundError:
            raise NoConfigFileException("Could not open " + filePath)

    def __parseLine__(self, line):
        if line == "":
            return

        if line.startswith('#'):
            return

        types = [member.name for member in ConfigType]
        args = line.split()

        if len(args) == 3:
            domain,valueType,data=args
            try:
                lineType = ConfigType(types.index(valueType))
                

                if lineType == ConfigType.DB:
                    self.__parse_db__(domain,data)
                elif lineType == ConfigType.SP:
                    self.__parse_sp__(domain,data)
                elif lineType == ConfigType.SS:
                    self.__parse_ss__(domain,data)
                elif lineType == ConfigType.DD:
                    self.__parse_dd__(domain,data)
                elif lineType == ConfigType.ST:
                    self.__parse_st__(domain,data)
                elif lineType == ConfigType.LG:
                    self.__parse_lg__(domain,data)
            except ValueError:
                raise InvalidConfigFileException(line + "has no valid type")
        else:
            raise InvalidConfigFileException(line + " contains more than 3 words")


    def __parse__db__(self,domain,data):
        if domain in self.dnsEntries:
            raise InvalidConfigFileException(f"duplicated dns entry in {domain} domain")
        try:
            with open(filepath,'r') as file:
                lines=file.readLines()#this way we can get a list of all lines
        except:
             raise InvalidConfigFileException(f"invalid file {data}")
        self.dnsEntries[domain]=[DNSEntry(line,fromFile=True) for line in lines]
        

    def __parse_sp__(self,domain,data):
        if domain in self.primaryDomains:
            raise InvalidConfigFileException(f"duplicated primary server in {domain} domain")
        self.primaryDomains[domain]=data
    def __parse_ss__(self,domain,data):
        if domain not in self.authorizedSS:
            self.authorizedSS[domain]=[]
        self.authorizedSS[domain].append(data)
    def __parse_dd__(self,domain,data):
        if domain not in self.defaultServers:
            self.defaultServers[domain]=[]
        self.defaultServers[domain].append(data)
    def __parse_st__(self,domain,data):
        if 'root' != domain:
            raise InvalidConfigFileException(f"ST parameter was {domain} expected root")
        try:
            with open(data,'r') as file:
                self.topServers+=file.readlines()
        except:
             raise InvalidConfigFileException(f"invalid file {data}")
    def __parse_lg__(self,domain,data):
        if domain == 'all':
            self.logFile=data
        elif domain in self.especificLogFiles:
            raise InvalidConfigFileException(f"duplicated log files in {domain} domain")
        elif domain not in self.authorizedSS and domain not in self.primaryDomains:
            raise InvalidConfigFileException(f"log files for non existing domain {domain}")
        else:
            self.especificLogFiles[domain]=data
    
    
    
    

    def __validate_entry__(self):
        return None