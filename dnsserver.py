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
from typing import Iterable, Optional

from common.logger import logger_process, LoggingEntryType,LogCreate,LogMessage
from multiprocessing import Queue,Process
from server.network import Network
from common.query import QueryResponse
from server.cache import Cache
from server.zoneTransfer import zoneTransferSP, zoneTransferSS
from common.dnsEntry import EntryType
from common.udp import UDP
from common.dnsMessage import DNSMessage, QueryInfo
from server.serverData import ServerData
import common.utils as utils
import sys

def processMessage(id:int, sendQueue : Queue, receiveQueue : Queue, msg: bytes, ip:str, p:int):
    global server
    global tag
    tag = id
    ans = server.process_message(msg, ip, p, sendQueue, receiveQueue)
    if ans:
        sendQueue.put((server.encode_msg(ans),ip,p, False), block=False)

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
        self.manager = MyManager()
        self.manager.start()
        self.config = self.manager.ServerData(config_file, logger)
        self.resolver = resolver
        self.supports_recursive = resolver
        self.cache = Cache()
        
    def encode_msg(self, msg:DNSMessage) -> bytes:
        '''
        From a DNSMessage, returns the bytes to be sent through the socket
        '''
        return str(msg).encode() if utils.debug else msg.to_bytes()
    
    def decode_msg(self, bytes:bytes) -> DNSMessage:
        '''
        From the bytes received from the socket, returns the encoded DNSMessage
        If the bytes don't correspond to a valid DNSMessage, an InvalidDNSMessageException is raised
        '''
        if utils.debug:
            return DNSMessage.from_string(bytes.decode())
        else:
            (msg, _) = DNSMessage.from_bytes(bytes)
            return msg

    def answers_query(self, query:QueryInfo) -> bool:
        '''
        Determines whether the server should answer the specified query

        If the server is a resolver (initialized with -r flag), it answers every query
        Otherwise, only queries about certain domains (DD in config file) are answered
        '''
        return self.resolver or self.config.answers_query(query.name)

    def query(self, address:str, query:QueryInfo, recursive:bool, sq, rq) -> Optional[QueryResponse]:
        """
        Queries the dns server in address with the given query
        Returns the QueryResponse, or None if the request timed out or response failed to parse
        """
        ip, port = utils.decompose_address(address)
        #udp = UDP(timeout=timeout)
        msg = DNSMessage.from_query(query, recursive)
        
        logger.put(LogMessage(LoggingEntryType.QE, address, [msg],query.name))

        try:
            global tag
            data = sq.put((self.encode_msg(msg), ip, port, tag))
            bytes, _, _ = rq.get()
        except socket.timeout:
            logger.put(LogMessage(LoggingEntryType.TO, address, ['DNS query timed out'],query.name))
            return None

        try:
            ans = self.decode_msg(bytes)
            if ans.is_query():
                logger.put(LogMessage(LoggingEntryType.ER, address, ["The received DNSMessage isn't a response: ", ans],query.name))
                return None
            else:
                logger.put(LogMessage(LoggingEntryType.RR, address, [ans], query.name))
                return ans.response
        except Exception as e:
            logger.put(LogMessage(LoggingEntryType.ER, address, [e], query.name))
            return None

    def query_any(self, addresses, query:QueryInfo, recursive:bool, sq, rq) -> Optional[QueryResponse]:
        """
        Queries the dns servers listed in addresses with the given query
        Returns the QueryResponse of the first answer, or None if none answered
        """
        for a in addresses:
            ans = self.query(a, query, recursive, sq, rq)

            if ans:
                return ans

    def resolve_address(self, hostname) -> Iterable[str]:
        """
        For the given domain name, returns a list with the corresponding ip addresses
        If the hostname can't be resolved, an empty list is returned
        """
        ans = self.answer_query(QueryInfo(hostname, EntryType.A), True)
        return map(lambda e: e.value, ans.values) if ans else []

    #TODO: response code 2 when domain doesn't exist (flag A)
    def answer_query(self, query:QueryInfo, recursive:bool, sq, rq) -> Optional[QueryResponse]:
        """
        Given a query and whether to run recursively, returns an
        answering QueryResponse or None if it isn't possible to answer
        """
        ans = self.config.answer_query(query)   #try database
        if ans.isFinal():
            return ans

        ans = self.cache.answer_query(query)    #try cache
        if ans.isFinal():
            return ans

        if not recursive:   #give up :)
            return self.config.get_first_servers(query.name)
        
        #start search from the root/default servers
        prev_ans:QueryResponse = self.config.get_first_servers(query.name)
        
        self.cache.add_response(prev_ans)
        
        while True:
            #Query wasn't successful yet, so the next step is to contact the next dns in the hierarchy
            #First, order received authorities from least to most specific (assume all of them match)
            prev_ans.authorities.sort(key=lambda e: len(utils.split_domain(e.parameter)))
            auths:list[str] = [e.value for e in prev_ans.authorities]               #next, get the hostname of their dns
            next_dns = [e.value for e in prev_ans.extra_values]#utils.flat_map(lambda dns: self.resolve_address(dns), auths) #lazily fetch address for each one
            ans:Optional[QueryResponse] = self.query_any(next_dns, query, recursive, sq, rq)

            if not ans:   
                #can't contact anyone :(
                return prev_ans

            if ans.isFinal():  #success!
                self.cache.add_response(ans, query)
                return ans

            prev_ans = ans  #store previous answer

    def process_message(self, message:bytes, ip:str, port:int, sq, rq) -> Optional[DNSMessage]:
        '''
        Processes the received message from the given address
        Returns a response message, or None if the query shouldn't be answered (see answers_query())
        '''
        address = f'{ip}:{port}'

        try:
            msg = self.decode_msg(message)
        except Exception as e:
            resp = DNSMessage.error_response(self.supports_recursive)
            logger.put(LogMessage(LoggingEntryType.ER, address, ["Error decoding DNSMessage:", e]))
            logger.put(LogMessage(LoggingEntryType.RP, address, [resp]))
            return resp
        
        if not msg.is_query():
            logger.put(LogMessage(LoggingEntryType.ER, address, ["The received DNSMessage isn't a query:", msg]))
            resp = msg.generate_error_response(self.supports_recursive)
            logger.put(LogMessage(LoggingEntryType.RP, address, [resp]))
            return resp

        if not self.answers_query(msg.query):
            logger.put(LogMessage(LoggingEntryType.ER, address, ["The received query shouldn't be answered:", msg]))
            return None
        
        logger.put(LogMessage(LoggingEntryType.QE, address, [msg], msg.query.name))

        ans = self.answer_query(msg.query, msg.recursive and self.supports_recursive, sq, rq)

        if ans:
            resp = msg.generate_response(ans, self.supports_recursive)
            logger.put(LogMessage(LoggingEntryType.RP, address, [resp], msg.query.name))
            return resp

    def run(self) -> None:
        procs = []
        #Add the single SP zone transfer process to the list
        procs.append(Process(target=zoneTransferSP, args=[self.config, logger, utils.get_local_ip(), port]))

        for domain in self.config.get_secondary_domains():
            procs.append(Process(target=zoneTransferSS, args=[self.config, logger, domain.name]))

        for proc in procs:
            proc.start()


        logger.put(LogMessage(LoggingEntryType.ST, utils.get_local_ip(), ['port:', port, 'timeout(ms):', timeout * 1000, 'debug:', utils.debug]))
        #self.server = UDP(localPort=port,binding = True)
        try:  
            self.network = Network(port, True, processMessage)          
            self.network.run()
            #while(True):
            #    msg, ip, p = self.server.receive()
            #    ans = self.process_message(msg, ip, p)
            #    if ans:
            #       self.server.send(self.encode_msg(ans), ip, p)
        except Exception as e:
            logger.put(LoggingEntryType.SP, utils.get_local_ip(), ['Unexpected termination:', e])
    
def extract_flag(flag:str) -> str:
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

def main() -> None:
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
    MyManager.register('ServerData', ServerData)
    utils.debug = "-d" in sys.argv
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
    p=Process(target=logger_process,args=(logger, utils.debug))
    p.start()

    #Config
    config_file = extract_flag("-c")
    global server
    server = Server(resolver, config_file)
    server.run()

if __name__ == "__main__":
    main()