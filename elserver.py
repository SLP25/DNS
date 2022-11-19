'''
Main server file.

This file reads the arguments of the program and sets
the server state accordingly. It also has the main function
responsible for receiving and sending DNS messages. Processing is
done in another file.

Last modification: Multiprocessing
Date of Modification: 19/11/2022 18:11
'''
#TODO: Terminate on SIGINT/SIGTERM

from multiprocessing import Process
import multiprocessing
from multiprocessing.managers import BaseManager
import random
import socket

from common.logger import logger_process, LoggingEntryType,LogCreate,LogMessage
from multiprocessing import Queue,Process

from common.query import QueryResponse
from server.cache import Cache
from server.zoneTransfer import zoneTransferSP, zoneTransferSS
from common.dnsEntry import EntryType
from common.udp import UDP
from common.dnsMessage import DNSMessage, QueryInfo
from server.serverData import ServerData
import common.utils as utils
import sys

class MyManager(BaseManager):
    pass

'''
Represents a DNS Server, with its own cache and configuration data
'''
class Server:
    def __init__(self, resolver:bool, config_file:str):
        '''
        Creates a new instance of the class with the given resolver status and
        the given configuration file path
        '''
        MyManager.register('ServerData', ServerData)

        self.manager = MyManager()
        self.manager.start()
        self.config = self.manager.ServerData(config_file, logger)
        self.resolver = resolver
        self.supports_recursive = resolver

        self.cache = Cache()

        #TODO: init zone transfers

    def answers_query(self, query:QueryInfo):
        '''
        Determines whether the server should answer the specified query

        If the server is a resolver (initialized with -r flag), it answers every query
        Otherwise, only queries about certain domains (DD in config file) are answered
        '''
        if self.resolver:
            return True

        for k in self.config.defaultServers:
            if utils.is_subdomain(query.name, k):
                return True

        return False

    def query(self, address, query:QueryInfo, recursive:bool):
        """
        Queries the dns server in address with the given query
        Returns the QueryResponse, or None if the request timed out or response failed to parse
        """
        ip, port = utils.decompose_address(address)
        udp = UDP(timeout=timeout)
        msg = DNSMessage.from_query(query, recursive)
        
        logger.put(LogMessage(LoggingEntryType.QE, address, [msg],query.name))

        try:
            udp.send(str(msg).encode(), ip, port) #TODO: check debug mode (if off, send bytes instead of string)
            bytes, _, _ = udp.receive()
        except socket.timeout:
            logger.put(LogMessage(LoggingEntryType.TO, address, ['DNS query timed out'],query.name))
            return None

        try:
            ans = DNSMessage.from_string(bytes.decode()) #TODO: check debug mode

            if ans.is_query():
                logger.put(LogMessage(LoggingEntryType.ER, address, ["The received DNSMessage isn't a response: ", ans],query.name))
                return None
            else:
                logger.put(LogMessage(LoggingEntryType.RR, address, [ans],query.name))
                return ans.response
        except:
            logger.put(LogMessage(LoggingEntryType.ER, address, ["TODO: meter msg de erro aqui"],query.name))
            return None

    def query_any(self, addresses, query:QueryInfo, recursive:bool):
        """
        Queries the dns servers listed in addresses with the given query
        Returns the QueryResponse of the first answer, or None if none answered
        """
        for a in addresses:
            ans = self.query(a, query, recursive)
            if ans:
                return ans

    def resolve_address(self, hostname):
        """
        For the given domain name, returns a list with the corresponding ip addresses
        If the hostname can't be resolved, an empty list is returned
        """
        ans = self.answer_query(QueryInfo(hostname, EntryType.A), True)
        return ans.values if ans else []

    def answer_query(self, query:QueryInfo, recursive:bool):
        """
        Given a query and whether to run recursively, returns an
        answering QueryResponse or None if it isn't possible to answer
        """

        ans = self.cache.answer_query(query)    #try cache
        if ans.positive():
            return ans

        ans = self.config.answer_query(query)   #try database
        if ans.positive() or not recursive:
            return ans

        #start search from the root/default servers
        next_dns = self.config.get_first_servers(query.name)
        prev_ans = None

        while True:
            ans = self.query_any(next_dns, query, recursive)
            if not ans:     #can't contact anyone :(
                return prev_ans if prev_ans else QueryResponse() #TODO: nao responder? resposta vazia? ou resposta anterior?

            self.cache.add_response(ans)
            if ans.positive() or not recursive:     #success!
                return ans

            prev_ans = ans  #store previous answer

            #Query wasn't successful yet, so the next step is to contact the next dns in the hierarchy
            #First, order received authorities from least to most specific (assume all of them match)
            ans.authorities.sort(key=lambda e: len(utils.split_domain(e.parameter)))
            auths = [e.value for e in ans.authorities]                              #next, get the hostname of their dns
            next_dns = utils.flat_map(lambda dns: self.resolve_address(dns), auths) #lazily fetch address for each one

    def process_message(self, message, ip, port):
        '''
        Processes the received message from the given address
        Returns a response message, or None if the query shouldn't be answered (see answers_query())
        '''
        address = f'{ip}:{port}'

        try:
            msg = DNSMessage.from_string(message.decode())
        except:
            logger.put(LogMessage(LoggingEntryType.ER, address, ["TODO: meter msg de erro aqui"]))
            return None 
        
        if not msg.is_query():
            logger.put(LogMessage(LoggingEntryType.ER, address, ["The received DNSMessage isn't a query:", msg]))
            return None

        if not msg.is_query():
            #logger.log(LoggingEntryType.ER, address, ["The received DNSMessage isn't a query:", msg])
            return None

        if not self.answers_query(msg.query):
            return None
        
        logger.put(LogMessage(LoggingEntryType.QE, address, [msg],msg.query.name))
        ans = self.answer_query(msg.query, msg.recursive and self.supports_recursive)
        if ans:
            resp = msg.generate_response(ans, self.supports_recursive)
            logger.put(LogMessage(LoggingEntryType.RP, address, [resp],msg.query.name))
            return str(resp).encode()

    def run_main(self):
        '''
        Main server loop
        Receives DNS queries, and calls the processing function
        '''
        logger.put(LogMessage(LoggingEntryType.ST, '127.0.0.1', ['port:', port, 'timeout:', timeout, 'debug:', debug]))
        self.server = UDP(localPort=port,binding = True)

        while(True):
            msg, ip, p = self.server.receive()
            ans = self.process_message(msg, ip, p)
            if ans:
                self.server.send(ans, ip, p)

    def run(self):
        procs = []
        #Add the single SP zone transfer process to the list
        procs.append(Process(target=zoneTransferSP, args=[self.config, "127.0.0.1", port]))
        #TODO: Add locks
        #Add one zone transfer process to the list for
        #each domain the server is an SS for
        for domain in self.config.get_secondary_domains():
            procs.append(Process(target=zoneTransferSS, args=[self.config, domain.name]))

        for proc in procs:
            proc.start()

        self.run_main()

        #logger.log(LoggingEntryType.SP, '127.0.0.1', ['TODO: cenas aqui'])
    
def extract_flag(flag):
    '''
    Extracts the value of the given flag in the system arguments

    Parameters:
    flag: a string containing the flag to extract (format -<flag>)

    Example:

    For example, if the process is called with ("-p 5000") this function
    will return "5000" (as a string)
    '''
    index = sys.argv.index(flag)
    return sys.argv[index + 1]

def main():
    '''
    The entry point for the server. Parses the program arguments
    and sets the global configuration

    The server receives the following arguments:
    -p : The port to listen to UDP datagrams on
    -t : The number of seconds to wait for the response to a query
    -c : The path to the configuration file
    -r : Whether this server is a resolver (SR) or not
    -d : If the server is in debug mode
    '''
    global debug
    debug = "-d" in sys.argv
    resolver = "-r" in sys.argv

    global port
    port = int(extract_flag("-p"))
    if port < 0 or port > 65635:
        print("Invalid port")
        exit(1)

    global timeout
    timeout = int(extract_flag("-t")) / 1000    #convert to seconds
    
    global logger
    m = multiprocessing.Manager()
    logger=m.Queue()
    p=Process(target=logger_process,args=(logger, debug))
    p.start()

    #Config
    config_file = extract_flag("-c")
    server = Server(resolver, config_file)
    print(logger)
    server.run()

if __name__ == "__main__":
    main()