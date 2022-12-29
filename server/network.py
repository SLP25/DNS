from multiprocessing import Manager, Queue,Pool
from common.udp import UDP
from threading import Lock, Thread

class Network:             
    def __init__(self, port:int=53, binding:bool= True, processMessage = None):
        self.udp = UDP(localPort=port, binding=binding)
        self.lock = Lock()
        self.table = {}
        self.m = Manager()
        self.sendQueue = self.m.Queue()
        self.pool = Pool(processes=1)
        self.processMessage = processMessage

    def run(self):
        t1 = Thread(target=self.__receive__)
        t2 = Thread(target=self.__send__)

        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
    
    def __receive__(self):
        while True:
            print("AQUI RECEIVE")
            msg, ip, p = self.udp.receive()
            print("DEPOIS RECEIVE")
            self.pool.apply(self.processMessage, (self.sendQueue, msg,ip, p))
        
    def __send__(self):
        while True:
            (message, ip, p) = self.sendQueue.get()
            print("A ENVIAR")
            if message == None:
                break
            
            self.udp.send(message, ip, p)
        