import random

class DNSMessage:

    def setHeaders(self, messageID = random.uniform(1,65356), query, recursive, authoritive, responseCode):
        self.messageID = messageID
        self.query = query
        self.recursive = recursive
        self.authoritive = authoritive
        self.responseCode = responseCode
        self.values = []
        self.authorities = []
        self.extraValues = []

    def setQueryInfo(self, name, typeOfValue):
        self.name = name
        self.type = typeOfValue

    def addResponse(self, response):
        self.values.append(response)

    def addAuthority(self, response):
        self.authorities.append(response)
    
    def addExtra(self, response):
        self.extraValues.append(response)

    def fromBytes(self, bytes):
        pass
