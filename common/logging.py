import logging
import enum
from exceptions import MainLoggerNotIniciatedException,LoggerNotIniciatedException
import datetime
import time
import sys

class LoggingEntryType(enum):
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


class Logging:
    mainLogger=None
    domains={}
    
    def __init__(self,debug=False):
        self.debug=debug
    
    def __setup_logger__(self,name, log_file):
        """creates a logger with a given name
        or the root logger if no name is givver
        stores the data in the log_file

        Args:
            name (str): name of the logger (root logger if None)
            log_file (str): path to the log file
        """
        if name==None:
            if self.mainLogger==None:
                logger = logging.getLogger()
            else:
                logger  = self.mainLogger
        elif name in self.domains:
            logger=self.domains[name]
        else:
            logger = logging.getLogger(name)
            
        handlerF = logging.FileHandler(log_file)    
        logger.addHandler(handlerF)
        if self.debug:
            handlerC = logging.StreamHandler(sys.stdout) 
            logger.addHandler(handlerC)
        if name==None:
            self.mainLogger=logger
        else:
            self.domains[name]=logger
    
    def setupLogger(self,filename:str,domain:str,isRoot=False):
        """
        sets up the logger inside the class
        if isRoot is True then the name will not be used
        Args:
            filename (str): the file path where to store data
            name ("str"): name of the domain
            isRoot (bool, optional): is the main logger. Defaults to False.
        """
        if isRoot:
            self.__setup_logger__(None,filename)
        else:
            self.__setup_logger__(domain,filename)
    
    def __stardizeMessage__(self,etype:LoggingEntryType,ip:str,data:list):
        now=datetime.datetime.now()
        timestamp=now.strftime("%d:%m:%Y.%H:%M:%S:")+now.strftime("%f")[:3]#19:10:2022.11:20:50:020
        return ' '.join([timestamp,str(etype),ip]+[str(x) for x in data])
        
        
        
    def log(self,etype:LoggingEntryType,ip:str,data:list,domain=None):
        if not domain:
            if not self.mainLogger:
                raise MainLoggerNotIniciatedException()
            logger=self.mainLogger
        else:
            logger=self.domains[domain]
        logger.info(self.__stardizeMessage__(etype,ip,data))
        
            
    
                
        
        
        
    

