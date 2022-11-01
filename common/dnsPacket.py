import struct
import re
from dnsEntry import DNSEntry,EntryType
import random
#this converts something into an unsigned short

lambda u16 = x: struct.unpack('H', struct.pack('h', x))



class DNSPacket:
    class Header:
        
        def get_id(self):
            return self.id
        def get_flags(self):
            return self.flags
        def get_responseCode(self):
            return self.responseCode
        def get_numberOfValues(self):
            return self.numberOfValues
        def get_numberOfAuthorities(self):
            return self.numberOfAuthorities
        def get_numberOfExtraValues(self):
            return self.numberOfExtraValues
        
        def set_id(self,a):
            self.id = a
        def set_flags(self,a):
            self.flags = a
        def set_responseCode(self,a):
            self.responseCode = a
        def set_numberOfValues(self,a):
            self.numberOfValues = a
        def set_numberOfAuthorities(self,a):
            self.numberOfAuthorities = a
        def set_numberOfExtraValues(self,a):
            self.numberOfExtraValues = a
            
        def isRecursive(self):
            return 'Q' in self.flags
        
        
        
            
        def __validate_flags__(self):
            if not (len(self.flags)>0 and len(self.flasg)<4):
                raise ValueError(f"there can only be 1-3 flags {len(self.flags)} recieved")
            if not re.match('^[QRA]*$', self.flags):
                raise ValueError("Flags must be only composed of QRA")
            for c in 'QRA':
                if self.flags.count(c)>1:
                    raise ValueError(f"Flag {c} repeted more than once")
                
                
        def get_numberOfNonCounters(self):
            elements=[
                self.numberOfValues,
                self.numberOfAuthorities,
                self.numberOfExtraValues,
            ]
            return sum(map(lambda x: 1 if x>0 else 0,elements))#counter the number of lists that will be used (this will be helpful in the body fromString function)
                
                
        def __validate__(self):
            if not 1<=self.id<=65536:
                raise ValueError("Id must be a number between 1-65536")
            self.__validate_flags__()
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
                self.flags,
                self.responseCode,
                self.numberOfValues,
                self.numberOfAuthorities,
                self.numberOfExtraValues,
            ]
            return ','.join(str(element) for element in elements)+';'
        def toBytes(self):
            pass
        
        def from_str(self,data:str):
            header=data.split(',')
            if len(header)!=6:
                raise ValueError(f"header contains the wrong number of arguments:{len(header)} expected 6")
            messageId,flags,responseCode,numberOfValues,numberOfAuthorities,numberOfExtraValues=header
            self.id=int(messageId)
            self.flags=flags
            self.responseCode=int(responseCode)
            self.numberOfValues=int(numberOfValues)
            self.numberOfAuthorities=int(numberOfAuthorities)
            self.numberOfExtraValues=int(numberOfExtraValues)
            self.__validate__()
            
            
            
        
            
    class Body:
        
        def get_name(self):
            return self.name
        def get_typeOfValue(self):
            return self.typeOfValue
        def get_responseValues(self):
            return self.responseValues
        def get_authoritativeValues(self):
            return self.authoritativeValues
        def get_extraValues(self):
            return self.extraValues
        
        def set_name(self,name):
            self.name = name
        def set_typeOfValue(self,typeOfValue):
            self.typeOfValue = typeOfValue
        def set_responseValues(self,responseValues):
            self.responseValues = responseValues
        def set_authoritativeValues(self,authoritativeValues):
            self.authoritativeValues = authoritativeValues
        def set_extraValues(self,extraValues):
            self.extraValues = extraValues
            
        def add_responseValues(self,responseValue):
            self.responseValues.append(responseValue)
        def add_authoritativeValues(self,authoritativeValue):
            self.authoritativeValues.append(authoritativeValue)
        def add_extraValues(self,extraValue):
            self.extraValues.append(extraValue)
        
        
        
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
        def toBytes(self):
            pass
        
        def queryInfo_fromString(self,data:str):
            queryInfo=data.split(',')
            if len(queryInfo)!=2:
                raise ValueError(f"Query info invalid number of fields expected 2 but {len(queryInfo)} were given")
            self.name = queryInfo[0]
            self.typeOfValue = EntryType[queryInfo[1]]
        
        def responseValues_fromString(self,data:str):
            values=data.split(',')
            self.responseValues=list(map(lambda x: DNSEntry(x),values))
            
        def authorities_fromString(self,data:str):
            values=data.split(',')
            self.authoritativeValues=values

            
        def extraValues_fromString(self,data:str):
            values=data.split(',')
            self.extraValues=values

        
        
        def from_str(self,header:self.Header,data:str):
            """
            assumes the data doesn't end with ; pls remove before sending here
            """
            body=data.split(';')
            if len(body)!=1+header.get_numberOfNonCounters():
                raise ValueError(f"body contains the wrong number of paramenters {len(body)} were given, expected {1+header.get_numberOfNonCounters()}")
            queryInfo = body.pop(0)
            self.queryInfo_fromString(body.pop(0))
            if header.get_numberOfValues()>0:
                values=body.pop(0)
                self.responseValues_fromString(values)
            else:
                self.responseValues=[]
            if header.get_numberOfAuthorities()>0:
                authorities=body.pop(0)
                self.authorities_fromString(authorities)
            else:
                self.authoritativeValues=[]
            if header.get_numberOfExtraValues()>0:
                extraValues=body.pop(0)
                self.extraValues_fromString(extraValues)
            else:
                self.extraValues=[]
            self.__validate__()
                
                

            
    def __init__(self):
        self.header=self.Header()
        self.body=self.Body()
        
        
    def __validate__(self):
        if self.header.numberOfValues != len(self.body.responseValues):
            raise ValueError("Number of Response Values doesn't match the number of values in the header")
        if self.header.numberOfAuthorities != len(self.body.authoritativeValues):
            raise ValueError("Number of Type Of Authorities doesn't match the number of authorities in the header")
        if self.header.numberOfExtraValues != len(self.body.extraValues):
            raise ValueError("Number of Extra Values doesn't match the number of Extra Values in the header")
        
    def __str__(self):
        return str(self.header)+str(self.body)
    
    def from_str(self,data:str):
        pos=myString.find(';')
        if pos==-1: #first separator not found
            raise ValueError("no separator found")
        self.header.from_str(data[:pos])
        self.body.from_str(self.header, data[pos+1:-1])
        self.__validate__()
        
    def createEmptyMessage(self,name:str,typeOfValue:EntryType,messageId=random.randint(1, 65356),query=False,recursive=False,authorative=False):
        self.header.set_id(messageID)
        flagsBool=[query,recursive,authorative]
        strFlags=''
        for p,i in enumerate('QRA'):
            if flagsBool[p]:
                strFlags+=i
        self.header.set_flags(strFlags)
        self.header.set_responseCode(0)
        self.header.set_numberOfValues(0)
        self.header.set_numberOfAuthorities(0)
        self.header.set_numberOfExtraValues(0)
        self.body.set_name(name)
        self.body.set_typeOfValue(typeOfValue)
        
        
    def addValue(self, responseValue):
        self.header.set_numberOfValues(self.header.get_numberOfValues()+1)
        self.body.add_responseValues(responseValue)

    def addAuthority(self, authoritativeValue):
        self.header.set_numberOfAuthorities(self.header.get_numberOfAuthorities()+1)
        self.body.add_authoritativeValues(authoritativeValue)
    
    def addExtraValue(self, extraValue):
        self.header.set_numberOfExtraValues(self.header.get_numberOfExtraValues()+1)
        self.body.add_extraValues(extraValue)
    
    def isRecursive(self):
        return self.header.isRecursive()

    def get_QueryInfoName(self):
        return self.body.get_name()
    def get_QueryInfoTypeOfValue(self):
        return self.body.get_typeOfValue()
    def get_responseCode(self):
        return self.header.get_responseCode()
    def get_responseValues(self):
            return self.responseValues

        
            
        
    def toBytes(self):
        pass