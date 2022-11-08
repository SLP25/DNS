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

from common.udp import UDP
from common.dnsPacket import DNSPacket
from server.serverConfig import ServerConfig
import sys

class Server:
    
    def __init__(self, config_file):
        self.config = ServerConfig(config_file)
    
    
    def process_message(self, message, address):
        packet=DNSPacket().from_str(message)
        #TODO: pesquisar em cache
        
        if packet.get_QueryInfoName() in self.config.authorizedSS():
            #TODO:search DATABASE??
            #send packet
            return
        # if SDT IN CACHE
        #    std=chache[packet.get_]
        #else
        sdt=None
        for server in self.config.topServers:
            self.server.send(str(packet),server) #depois mudar isto para verificar se usa modo de debug ou n
            message,addr=self.server.receive()
            tpacket=DNSPacket().from_str(message)
            if tpacket.get_responseCode() == 0: 
                sdt=tpacket.get_responseValues()
                break
        #fora do else
        if sdt:
            #adicionar a cache
            if not packet.isRecursive():
                self.server.send(str(packet),std[0]) #depois mudar isto para verificar se usa modo de debug ou n
                message,addr=self.server.receive()
                self.server.send(message,address) #devolve o proximo a contactar/resposta
        #else enviar packet com erro  
            


        pass

    def run(self):
        '''
        Main server loop
        Receives DNS queries, and calls the processing function
        '''
        self.server = UDP(binding = True)

        while(True):
            msg, address =  self.server.receive()
            self.process_message(msg, address)
    
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
    -d : If the server is in debug mode
    '''
    global debug
    debug = "-d" in sys.argv

    global port
    port = int(extract_flag("-p"))
    if port < 0 or port > 65635:
        print("Invalid port")
        exit(1)

    global timeout
    timeout = int(extract_flag("-t"))

    #Config
    config_file = extract_flag("-c")
    server = Server(config_file)
    server.run()
    
if __name__ == "__main__":
    main()