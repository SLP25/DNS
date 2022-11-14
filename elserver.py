'''
Main server file.

This file reads the arguments of the program and sets
the server state accordingly. It also has the main function
responsible for receiving and sending DNS messages. Processing is
done in another file.

Last modification: Added documentation
Date of Modification: 14/11/2022 15:03
'''
#TODO: Terminate on SIGINT/SIGTERM

import random
from common.query import QueryResponse
from server.cache import Cache
from common.dnsEntry import EntryType
from common.udp import UDP
from common.dnsMessage import DNSMessage, QueryInfo
from server.serverData import ServerData
import common.utils as utils
import sys

'''
Represents a DNS Server, with its own cache and configuration data
'''
class Server:
    
    def __init__(self, resolver:bool, config_file:str):
        '''
        Creates a new instance of the class with the given resolver status and
        the given configuration file path
        '''
        self.resolver = resolver
        self.supports_recursive = resolver
        self.config = ServerData(config_file)
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
    
    #TODO: timeout
    def query(self, address, query:QueryInfo):
        """
        Queries the dns server in address with the given query
        Returns the QueryResponse, or None if the request timed out or response failed to parse
        """
        udp = UDP(localPort=port)   #TODO: use another port
        msg = DNSMessage.from_query(query, True)
        
        udp.send(str(msg).encode(), address) #TODO: check debug mode (if off, send bytes instead of string)
        bytes, _ = udp.receive()
        
        try:
            ans = DNSMessage.from_string(bytes.decode()) #TODO: check debug mode
            return ans.response
        except:
            return None
    
    #returns the result of the first answered query, or None if none was answered
    def query_all(self, addresses, query:QueryInfo):
        """
        Queries the dns servers listed in addresses with the given query
        Returns the QueryResponse of the first answer, or None if none answered
        """
        for a in addresses:
            ans = self.query(a, query)
            if ans:
                return ans
            
    def resolve_address(self, hostname):
        """
        For the given domain name, returns a list with the corresponding ip addresses
        If the hostname can't be resolved, an empty list is returned
        """
        ans = self.answer_query(QueryInfo(hostname, EntryType.A), True)
        return ans.values if ans else []
    
    #TODO: distinguish no response from domain doesn't exist
    def answer_query(self, query:QueryInfo, recursive:bool):
        """
        Given a query and whether to run recursively, returns an
        answering QueryResponse or None if it isn't possible to answer
        """
        ans = self.cache.answer_query(query)           #try cache
        if ans.positive():
            return ans
        
        ans = self.config.answer_query(query)   #try database
        self.cache.add_response(ans)
        if ans.positive():
            return ans
        
        #start search from the root/default servers
        next_dns = self.config.get_first_servers(query.name)
        prev_ans = None
        
        while True:
            ans = self.query_all(next_dns, query)
            if not ans:     #can't contact anyone :(
                return prev_ans if prev_ans else QueryResponse()
            
            self.cache.add_response(ans)
            if ans.positive() or not recursive:     #success!
                return ans
        
            prev_ans = ans  #store previous answer
        
            #Query wasn't successful yet, so the next step is to contact the next dns in the hierarchy
            #First, order received authorities from most to least specific (assume all of them match)
            ans.authorities.sort(reverse=True, key=lambda e: len(utils.split_domain(e.parameter)))
            auths = [e.value for e in ans.authorities]                              #next, get the hostname of their dns
            next_dns = utils.flat_map(lambda dns: self.resolve_address(dns), auths) #lazily fetch address for each one

    
    def process_message(self, message, address):
        '''
        Processes the received message from the given address
        Returns a response message, or None if the query shouldn't be answered (see answers_query())
        '''
        msg = DNSMessage().from_string(message.decode())
        
        if not self.answers_query(msg.query):
            return None
        
        ans = self.answer_query(msg.query, self.supports_recursive)
        if ans:
            return str(msg.generate_response(ans, self.supports_recursive)).encode()

    def run(self):
        '''
        Main server loop
        Receives DNS queries, and calls the processing function
        '''
        self.server = UDP(localPort=port,binding = True)

        while(True):
            print("receiveing messages!")
            msg, address = self.server.receive()
            print("message received!")
            print(msg)
            ans = self.process_message(msg, address)
            print(ans)
            if ans:
                self.server.send(ans, address)
    
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
    timeout = int(extract_flag("-t"))

    #Config
    config_file = extract_flag("-c")
    server = Server(resolver, config_file)
    server.run()
    
if __name__ == "__main__":
    main()