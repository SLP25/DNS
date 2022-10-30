'''
File defining custom exceptions used in the server codebase

Last Modification: Documentation
Date of Modification: 30/10/2022 11:57
'''

class NoConfigFileException(Exception):
    '''
    The config file could not be found or opened
    '''
    pass

class InvalidConfigFileException(Exception):
    '''
    The config file is invalid, i.e., it does not follow
    the specification
    '''
    pass

class InvalidZoneTransferPacketException(Exception):
    '''
    The zone transfer packet given is not valid. Thrown when
    parsing raw data (either string or bytes) to ZoneTransferPacket
    '''
    pass

