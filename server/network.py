from multiprocessing import Manager, Queue,Pool
from common.udp import UDP
from threading import Lock, Thread

class Network:             
    def __init__(self, port:int=53, binding:bool= True, processMessage = None):
        print("?")
        self.udp = UDP(localPort=port, binding=binding)
        print("AQUI")
        self.lock = Lock()
        self.table = {}
        self.m = Manager()
        self.sendQueue = self.m.Queue()
        self.receiveQueues = []
        self.counter = 0
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
            msg, ip, p = self.udp.receive()
            print("BADUMTSSSSSSss")
            with self.lock:
                print("LOCK")
                if (ip,p) in self.table:
                    print("IN TABLE")
                    self.receiveQueues[self.table[(ip,p)]].put((msg,ip,p))
                    self.table.pop((ip,p))
                else:
                    print("UPS")
                    m = Manager()
                    rq = m.Queue()
                    self.receiveQueues.append(rq)
                    self.pool.apply_async(self.processMessage, (self.counter, self.sendQueue, rq, msg,ip, p))
                    self.counter += 1
        
    def __send__(self):
        while True:
            print("WAITING")
            (message, ip, p, wait) = self.sendQueue.get()
            print("SENDING")
            if message == None:
                break
            print(f"AFTER BREAK: {wait}")
            self.udp.send(message, ip, p)
            
            if wait == False:
                with self.lock:
                    print("ADICIONADO")
                    self.table[(ip,p)] = wait
        