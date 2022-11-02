from enum import Enum
from .exceptions import InvalidConfigFileException, NoConfigFileException
from common.dnsEntry import DNSEntry

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
        #Deleting old values
        for key, value in self.dnsEntries.items():
            if key[0] == domain:
                self.dnsEntries.pop(key) 
                
        #Inserting new values
        self.dnsEntries.update(newEntries)

    def __parseLine__(self, line):
        if line == "":
            return

        if line.startswith('#'):
            return
        args = line.split()

        if len(args) == 3:
            domain,valueType,data=args
            try:
                lineType = ConfigType[valueType]
                

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


    def __parse_db__(self,domain,data):
        if domain in self.dnsEntries:
            raise InvalidConfigFileException(f"duplicated dns entry in {domain} domain")
        try:
            with open(data,'r') as file:
                lines=file.readlines()#this way we can get a list of all lines
        except:
            raise InvalidConfigFileException(f"invalid file {data}")
        self.dnsEntries[domain]=[DNSEntry(line,fromFile=True) for line in lines]
        

    def __parse_sp__(self,domain,data):
        if domain in self.primaryDomains:
            raise InvalidConfigFileException(f"duplicated primary server in {domain} domain")
        split = data.split(":")
        #TODO: Throw exception if invalid ip:port
        self.primaryDomains[domain]=(split[0], int(split[1]))
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