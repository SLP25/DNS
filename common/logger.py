import logging
from enum import Enum
#from server.exceptions import MainLoggerNotIniciatedException,LoggerNotIniciatedException
import datetime
import time
import sys
from multiprocessing import Queue,Process
from typing import Optional


class LoggingEntryType(Enum):
    """A enum representing each of the logging types possible
    """
    QR=0#data = PDU DATA
    QE=1#data = PDU DATA
    RP=2#data = PDU DATA
    RR=3#data = PDU DATA
    ZT=4#data = {SP ou SS},{duração em ms (opcional)},{bytes}
    EV=5#data = informação adicional sobre a atividade reportada
    ER=6#data = o que foi possível descodificar corretamente e em que parte/byte aconteceu o erro)
    EZ=7#data = (SP ou SS)
    FL=8#data = informação adicional sobre a situação de erro
    TO=9#data = ipo de timeout ocorreu (resposta a uma query ou tentativa de contato com um SP para saber informações sobre a versão da base de dados ou para iniciar uma transferência de zona)
    SP=10#data = informação adicional sobre a razão da paragem se for possível obtê-la
    ST=11#data = {porta de atendimento},{sobre o valor do timeout usado (em milissegundos)},{modo de funcionamento (modo “shy” ou modo debug)}.


class LogMessage:
    """
       The class representing a logging message 
    """
    def __init__(self,etype:LoggingEntryType,ip:str,data:list,domain:Optional[str]=None):
        """method to create a log message with the given data

        Args:
            etype (LoggingEntryType): the type of the logging message
            ip (str): the ip of the communication being processed when the logging occured
            data (list): the data to be added to the messages
            domain (str, optional): the domain to log to (ALL if None). Defaults to None.
        """
        self.etype=etype
        self.ip=ip
        self.data=data
        self.domain=domain
    
    def __stardizeMessage__(self) -> str:
        """Converts  a logMessage into a string

        Returns:
            String: the string representation of a log Message
        """
        now=datetime.datetime.now()
        timestamp=now.strftime("%d:%m:%Y.%H:%M:%S:")+now.strftime("%f")[:3]#19:10:2022.11:20:50:020
        return ' '.join([timestamp,str(self.etype.name),self.ip]+[str(x) for x in self.data])

class LogCreate:
    """
       The class representing adding a new file handler to a domain 
    """
    def __init__(self,filename,domain=None):
        """method to create a LogCreate

        Args:
            filename (String): the path to the file where to store the logging message from the domain
            domain (String, optional): the domain to map to the given file (All if None). Defaults to None.
        """
        self.filename=filename
        self.domain=domain

    

def logger_process(queue:Queue,debug:bool) -> None:
    """
    The queue will receive None,LogMessage,LogCreate:
        if None:
            close logger
        if LogCreate:
            To set a file for a given domain 
            if domain is None then use as ALL
        if LogMessage:
            To send a message for logging
            if domain is None then use as ALL
    Args:
        queue (Queue): the queue where messages come from
        debug (Bool): wheather to write also on stdout or not
    """
    mainLogger=None
    domainLoggers={}
    
    while True:
        message = queue.get()
        if message==None:
            break
        if isinstance(message,LogCreate):
            #Is to set a file
            if message.domain==None:
                #ALL
                if mainLogger == None:
                    #doesn't exist yet
                    mainLogger=logging.getLogger()
                    mainLogger.setLevel(logging.NOTSET)
                    if debug:
                        mainLogger.addHandler(logging.StreamHandler(sys.stdout))
                logger=mainLogger
            else:
                #idividual
                if message.domain not in domainLoggers:
                    #doesn't exist yet
                    domainLoggers[message.domain] = logging.getLogger(message.domain)
                    domainLoggers[message.domain].setLevel(logging.NOTSET)
                    domainLoggers[message.domain].propagate = False
                    if debug:
                        domainLoggers[message.domain].addHandler(logging.StreamHandler(sys.stdout))
                logger = domainLoggers[message.domain]
            logger.addHandler(logging.FileHandler(message.filename))
        elif isinstance(message,LogMessage):
            #Is to log data
            if message.domain not in domainLoggers:
                if mainLogger==None:
                    print("No ALL defined")
                    exit(1)
                logger = mainLogger
            else:
                logger = domainLoggers[message.domain]
            logger.critical(message.__stardizeMessage__())