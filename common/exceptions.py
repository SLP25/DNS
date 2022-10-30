'''
File defining custom exceptions used in the common codebase

Last Modification: Documentation
Date of Modification: 30/10/2022 11:57
'''
class InvalidDNSEntryException(Exception):
    '''
    The given DNS entry is not valid. Thrown when attempting
    to parse raw data (string or bytes) to DNSEntry
    '''
    pass
