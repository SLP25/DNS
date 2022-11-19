"""
File implementing class Domain and respective subclasses PrimaryDomain and SecondaryDomain

A primary domain can parse its dns entries from a database file. A secondary domain, on the
other hand, doesn't contain its entries in the local machine and must therefore query a
server which is primary to that domain through a zone transfer (see zoneTransfer.py)

Last Modification: Added documentation
Date of Modification: 14/11/2022 12:38
"""

from common.dnsEntry import DNSEntry, EntryType
from common.query import QueryInfo
from common.query import QueryResponse
from common.logger import LogCreate,LogMessage,LoggingEntryType
from server.exceptions import InvalidConfigFileException
import re
import common.utils as utils
from server.database import Database

class Domain:
    """
    Stores all information of an authoritative server (SP or SS) relative to a single domain
    """
    def __init__(self, name:str):
        """
        Creates an empty domain with the given name
        """
        self.name = name
        self.logFiles = []
    
    def add_log_file(self, log_file:str,logger):
        """
        Adds a specific log file path to the domian
        """
        logger.put(LogCreate(log_file, self.name))
        
class PrimaryDomain(Domain):
    """
    Stores all information of an authoritative server relative to a single primary domain
    """
    
    def __init__(self, name:str):
        """
        Creates an empty primary domain with the given name
        """
        super().__init__(name)
        self.authorizedSS = []
        self.database = None
        
    def is_authorized(self, ip):
        return ip in self.authorizedSS
        
    def set_database(self, path:str):    
        """
        Reads the database of the domain from the specidied path
        If the path to the file is invalid, an InvalidConfigFileException is raised
        If the parsing of the file fails, an InvalidDatabaseException is raised
        If the database already exists, raises an InvalidConfigFileException
        """
        if self.database != None:
            raise InvalidConfigFileException("Duplicated DB for domain " + self.name)

        self.database = Database(path)

    def add_authorizedSS(self, authorizedSS:str):
        """
        Adds the ip address of a SS to the list of authorized SS's
        If the string isn't a valid ip address (optionally with port), an InvalidConfigFileException is raised
        """
        if not re.search(f'^{utils.IP_MAYBE_PORT}$', authorizedSS):
            raise InvalidConfigFileException(f"Invalid ip address {authorizedSS}")

        self.authorizedSS.append(authorizedSS)

    def validate(self):
        """
        Determines whether the current instance has been fully parsed and can start answering queries
        If it isn't valid (doesn't contain a database yet), an InvalidConfigFileException is raised
        """
        if self.database == None:
            raise InvalidConfigFileException("No database file specified for primary domain " + self.name)

    def answer_query(self, query:QueryInfo):
        """
        Answers the given query by querying the database
        Returns a QueryResponse
        """
        return self.database.answer_query(query)

class SecondaryDomain(Domain):
    """
    Stores all information of an authoritative server relative to a single secondary domain
    """
    
    def __init__(self, name:str):
        """
        Creates an empty secondary domain with the given name
        """
        super().__init__(name)
        self.primaryServer = None
        self.aliases = None
        self.dnsEntries = None
        self.expire = 0
        self.retry = 0
        self.refresh = 0
        self.serial = 0
    
    def set_primary_server(self, primary_server:str):
        """
        Sets the ip address of a SP as the entity to contact when performing a zone transfer
        If the string isn't a valid ip address (optionally with port), an InvalidConfigFileException is raised
        If the primary server had already been set for this domain, an InvalidConfigFileException is raised
        """
        if self.primaryServer != None:
            raise InvalidConfigFileException("Duplicated SP for domain " + self.name)
        
        if not re.search(f'^{utils.IP_MAYBE_PORT}$', primary_server):
            raise InvalidConfigFileException(f"Invalid ip address {primary_server}")
        
        self.primaryServer = primary_server
    
    def get_expire(self):
        return self.expire
    
    def get_retry(self):
        return self.retry
    
    def get_refresh(self):
        return self.refresh
    
    def get_serial(self):
        return self.serial
    
    def validate(self):
        """
        Determines whether the current instance has been fully parsed and can start answering queries
        Note that being valid doesn't guarantee that the secondary domain already contains the entries
        returned from a zone transfer. Rather, it means that a zone transfer can take place to obtain them.
        If it isn't valid (doesn't have a set SP address), an InvalidConfigFileException is raised
        """
        if self.primaryServer == None:
            raise InvalidConfigFileException("No primary server specified for secondary domain " + self.name)

    #TODO: Thread safety
        """
        Replaces all entries of a certain domain with the given new entries.
        Used to update the copy of the original database in an SS after a zone transfer.

        This method WILL BE thread safe.

        More specifically, this method erases all entries for the domain in the copy of the database,
        and inserts the new ones in their place

        Arguments:
        new_entries : List (DNSEntry) -> A list with the new entries
        """
    def set_entries(self, new_entries):
        self.dnsEntries = new_entries
        self.aliases = {}
        for e in self.dnsEntries:
            if e.type == EntryType.CNAME:
                self.aliases[e.parameter] = e.value
            elif e.type == EntryType.SOAREFRESH:
                self.refresh = int(e.value)
            elif e.type == EntryType.SOARETRY:
                self.retry = int(e.value)
            elif e.type == EntryType.SOAEXPIRE:
                self.expire = int(e.value)
            elif e.type == EntryType.SOASERIAL:
                self.serial = int(e.value)
    
    #TODO: Thread safety
    def answer_query(self, query:QueryInfo):    #TODO: invalidate entries after SOAEXPIRE seconds
        """
        Answers the given query by searching the list of entries
        Returns a QueryResponse
        """
        hostname = self.__replace_aliases__(query.name)
        return QueryResponse.from_entries(QueryInfo(hostname, query.type), self.entries, True)
    
    def __replace_aliases__(self, domain:str):
        for k,v in self.macros.items():
            domain = domain.replace(k, v)
        return domain