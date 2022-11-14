'''
File defining custom exceptions used in the common codebase

Last Modification: Added InvalidDNSMessageException
Date of Modification: 10/11/2022 16:37
'''
class InvalidDNSEntryException(Exception):
    '''
    The given DNS entry is not valid. Thrown when attempting
    to parse raw data (string or bytes) to DNSEntry
    '''
    pass

class InvalidDNSMessageException(Exception):
    '''
    The given DNS message is not valid. Thrown when attempting
    to parse raw data (string or bytes) to DNSMessage
    '''

class MainLoggerNotIniciatedException(Exception):
    '''
    The main logger was not initiated before trying to log data.
    '''
class LoggerNotIniciatedException(Exception):
    '''
    The logger was not iniciated before trying to log data
    '''