import struct
import re
from dnsEntry import DNSEntry,EntryType
#this converts something into an unsigned short

lambda u16 = x: struct.unpack('H', struct.pack('h', x))



class DNSPacket:
    class Header:
        def __init__(self,id:int,flag:str,responseCode:int,numberOfValues:int,\
            numberOfAuthorities:int,numberOfExtraValues:int):
            self.id=id
            self.flag=flag
            self.responseCode=responseCode
            self.numberOfValues=numberOfValues
            self.numberOfAuthorities=numberOfAuthorities
            self.numberOfExtraValues=numberOfExtraValues
            self.__validate__()
            
            
        def __validate_flag__(self):
            if not (len(self.flag)>0 and len(self.flag)<4):
                raise ValueError(f"there can only be 1-3 flags {len(self.flag)} recieved")
            if not re.match('^[QRA]*$', self.flag):
                raise ValueError("Flags must be only composed of QRA")
            for c in 'QRA':
                if self.flag.count(c)>1:
                    raise ValueError(f"Flag {c} repeted more than once")
                
                
        def __validate__(self):
            if not 1<=self.id<=65536:
                raise ValueError("Id must be a number between 1-65536")
            self.__validate_flag__()
            if not 0<=self.responseCode<=3:
                raise ValueError("Response Code must be a number between 0-3")
            if not 0<=self.numberOfValues<=255:
                raise ValueError("Number of Values must be a number between 0-255")
            if not 0<=self.numberOfAuthorities<=255:
                raise ValueError("Number of Authorities must be a number between 0-255")
            if not 0<=self.numberOfExtraValues<=255:
                raise ValueError("Number of Extra Values must be a number between 0-255")
            
            
        def __str__(self):
            elements=[
                self.id,
                self.flag,
                self.responseCode,
                self.numberOfValues,
                self.numberOfAuthorities,
                self.numberOfExtraValues,
            ]
            return ','.join(str(element) for element in elements)+';'
        
            
    class Body:
        def __init__(self,name:str,typeOfValue:EntryType,responseValues:list[DNSEntry],\
            authoritativeValues:list[str],extraValues:list[str]):
            self.name = name 
            self.typeOfValue = typeOfValue
            self.responseValues = responseValues
            self.authoritativeValues = authoritativeValues
            self.extraValues = extraValues
            self.__validate__()
            
        def __VerifyExtraValuesIPv4__(self):
            for extraValue in self.extraValues:
                if len(re.findall("^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", extraValue))!=1: #TODO: verificar este regex q eu copiei da net n o verifiquei 
                    raise ValueError(f"extra value {extraValue} doesn't match a IPv4 address")
                    
                    
        def __validate__(self):
            self.__VerifyExtraValuesIPv4__()
            
        def __str__(self):
            elements=[
                [self.name,self.typeOfValue],
                self.responseValues,
                self.authoritativeValues,
                self.extraValues,
            ]
            return ';'.join(','.join(str(e) for e in element)for element in elements)+';'
            
                
            
        
            
    def __init__(self,id:int,flag:str,responseCode:int,\
        name:str,typeOfValue:EntryType,responseValues:list[DNSEntry],\
        authoritativeValues:list[str],extraValues:list[str],\
        numberOfValues=None,numberOfAuthorities=None,numberOfExtraValues=None):
        
        if numberOfValues==None:
            numberOfValues=len(responseValues)    
        if numberOfAuthorities==None:
            numberOfAuthorities=len(authoritativeValues)
        if numberOfExtraValues==None:
            numberOfExtraValues=len(extraValues)
        

        self.header=self.Header(id, flag, responseCode, numberOfValues, numberOfAuthorities, numberOfExtraValues)
        self.body=self.Body(name, typeOfValue, responseValues, authoritativeValues, extraValues)
        self.__validate__()
        
        
    def __validate__(self):
        if self.header.numberOfValues != len(self.body.responseValues):
            raise ValueError("Number of Response Values doesn't match the number of values in the header")
        if self.header.numberOfAuthorities != len(self.body.authoritativeValues):
            raise ValueError("Number of Type Of Authorities doesn't match the number of authorities in the header")
        if self.header.numberOfExtraValues != len(self.body.extraValues):
            raise ValueError("Number of Extra Values doesn't match the number of Extra Values in the header")
        
    def __str__(self):
        return str(self.header)+str(self.body)

            
            
    
    
    
    def __init__(self):
        se
    