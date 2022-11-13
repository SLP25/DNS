'''
Main server file.

This file reads the arguments of the program and sets
the server state accordingly. It also has the main function
responsible for receiving and sending DNS messages. Processing is
done in another file.

Last modification: Creation
Date of Modification: 29/10/2022 18:05
'''
#TODO: Terminate on SIGINT/SIGTERM

import random
from server.cache import Cache
from common.dnsEntry import EntryType
from common.udp import UDP
from common.dnsMessage import DNSMessage, QueryInfo
from server.serverData import ServerData
import common.utils as utils
import sys

class Server:
    
    def __init__(self, resolver, config_file):
        self.resolver = resolver
        self.supports_recursive = resolver
        self.config = ServerData(config_file)
        self.cache = Cache()
        #TODO: init zone transfers
        
    def answers_query(self, query:QueryInfo):
        if self.resolver:
            return True
        
        for k in self.config.defaultServers:
            if utils.is_subdomain(query.name, k):
                return True
            
        return False
    
    #TODO: timeout
    def query(self, address, query:QueryInfo):
        udp = UDP(localPort=port)   #TODO: use another port
        msg = DNSMessage.from_query(query, True)
        
        udp.send(str(msg), address) #TODO: check debug mode (if off, send bytes instead of string)
        bytes, _ = udp.receive()
        
        ans = DNSMessage.from_string(bytes) #TODO: check debug mode
        return ans.response
    
    #returns the result of the first answered query, or None if none was answered
    def query_all(self, addresses, query:QueryInfo):
        for a in addresses:
            ans = self.query()
            if ans:
                return ans
            
    #returns a list of returned addresses
    def resolve_address(self, hostname):
        ans = self.answer_query(QueryInfo(hostname, EntryType.A), True)
        return ans.values if ans else []
    
    #returns an instance of QueryResponse, or None if it wasn't possible to determine the answer
    #TODO: distinguish no response from domain doesn't exist
    def answer_query(self, query:QueryInfo, recursive:bool):
        ans = self.cache.query(query)           #try cache
        if ans.positive():
            return ans
        
        ans = self.config.answer_query(query)   #try database
        self.cache.add_response(ans)
        if ans.positive():
            return ans
        
        #start search from the root/default servers
        default = self.config.get_default_server(query.name)
        next_dns = ([default] if default else []) + self.config.topServers
        
        while True:
            ans = self.query_all(next_dns, query)
            if not ans:     #can't contact anyone :(
                return None
            
            self.cache.add_response(ans)
            if ans.positive() or not recursive:
                return ans
        
            #Query wasn't successful yet, so the next step is to contact the next dns in the hierarchy
            #First order received authorities from most to least specific (assume all of them match)
            ans.authorities.sort(reverse=True, key=lambda e: len(utils.split_domain(e.parameter)))
            auths = map(lambda e: e.value, ans.authorities)                         #next get the hostname of their dns
            next_dns = utils.flat_map(lambda dns: self.resolve_address(dns), auths) #lazily fetch address for each one

    
    #returns the response message (string/bytes), or None if no response is to be given
    def process_message(self, message, address):
        msg = DNSMessage().from_str(message)
        
        if not self.answers_query(msg.query):
            return None
        
        ans = self.answer_query(msg.query, self.supports_recursive)
        if ans:
            return str(msg.generate_response(ans, self.supports_recursive))

    def run(self):
        '''
        Main server loop
        Receives DNS queries, and calls the processing function
        '''
        self.server = UDP(binding = True)

        while(True):
            msg, address =  self.server.receive()
            ans = self.process_message(msg, address)
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