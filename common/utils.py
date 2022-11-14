"""
File implementing a number of utilities useful throughout the project
Some examples: regex patterns, functions for domain name manipulation and functions
for serialization/deserialization

Last Modification: Adding documentation
Date of Modification: 14/11/2022 10:20
"""

"""
The default port to use if no port is specified in the ip address of a dns server
"""
DEFAULT_PORT = 53


"""
Defines a comment in all configuration files
"""
COMMENT_LINE = r'^\s*(#|$)'


"""
Defines a valid domain name character, excluding the separator (dot)
"""
DOMAIN_CHAR = r'[a-zA-Z0-9\-]'

"""
Defines a valid domain name without the terminating dot
"""
DOMAIN = f'({DOMAIN_CHAR}+\.)*{DOMAIN_CHAR}+'

"""
Defines a valid domain name with the terminating dot
"""
FULL_DOMAIN = f'(({DOMAIN_CHAR}+\.)+|\.)'


"""
Defines a valid email address character, excluding the separator (dot)
"""
EMAIL_CHAR = r'[A-Za-z0-9_%+-]'

"""
Defines a valid email address in an SP database file
Not that this isn't the regular email address format; rather, the dots before the @
character are escaped (\.) and the @ character is replaced by a dot
"""
EMAIL_ADDRESS = f'({EMAIL_CHAR}+\\\\\.)*{EMAIL_CHAR}+\.({DOMAIN_CHAR}+\.)+'


"""
An decimal representation of a byte (integer between 0 and 255)
"""
BYTE_RANGE = r'([0-1]?\d{0,2}|2[0-4]\d|25[0-5])'

"""
A valid port number (integer between 0 and 65535)
"""
PORT_RANGE = r'([0-5]?\d{0,4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])'

"""
A valid IPv4 address
"""
IP_ADDRESS = f'({BYTE_RANGE}\.){{3}}{BYTE_RANGE}'

"""
A valid IPv4 address, coupled with a port
"""
IP_AND_PORT = f'(?P<ip>{IP_ADDRESS}):(?P<port>{PORT_RANGE})'

"""
A valid IPv4 address, optionally coupled with a port
"""
IP_MAYBE_PORT = f'(?P<ip>{IP_ADDRESS})(:(?P<port>{PORT_RANGE}))?'


def flat_map(f, xs):
    """
    Given a function that produces lists and a list, flat_map applies the
    function to each element and concatenates the resulting lists
    Returns a generator (is lazy)
    Is a monad
    """
    return (y for ys in xs for y in f(ys))


def normalize_domain(domain:str):
    """
    Given a valid domain name (that matches DOMAIN or FULL_DOMAIN regexes), converts it
    to the normalized format: all lowercase, with a terminating dot
    """
    return (domain if domain[-1] == '.' else domain + '.').lower()


def split_domain(domain:str):
    """
    Given a valid domain name (that matches DOMAIN or FULL_DOMAIN regexes), returns a list
    with the subdomains, from highest to lowest hierarchically
    
    Examples:
        example.com. -> ['com', 'example']
        .            -> []
    """
    ans = list(filter(None, domain.lower().split('.')))
    ans.reverse()
    return ans


def is_subdomain(subdomain:str, domain:str):
    """
    Given two valid domain names (that match DOMAIN or FULL_DOMAIN regexes),
    determines whether the subdomain is hierarchically below the domain
    
    Examples:
        example.com. .          -> True
        com.         com.       -> True
        google.com.  abc.com.   -> False
    """
    sd = split_domain(subdomain)
    d = split_domain(domain)

    if len(sd) < len(d):
        return False

    for i,x in enumerate(d):
        if x != sd[i]:
            return False

    return True

#returns the domain in domains that best matches the subdomain
def best_match(subdomain:str, domains):
    """
    Given a valid domain name and a list of valid domain names (that match DOMAIN or FULL_DOMAIN regexes),
    determines the domain hierarchically closest to the subdomain
    Any domains that aren't hierarchically above the subdomain are ignored
    
    Example:
        www.example.com. ['com.', 'example.com.', '.org' ]  -> 'example.com.'
    """
    sd = split_domain(subdomain)
    best = None
    best_num = 0
    
    for domain in domains:
        if not is_subdomain(subdomain, domain):
            continue
        
        d = split_domain(domain)
        cur = min(len(d),len(sd))
        if cur > best_num:
            best = domain
            best_num = cur
            
    return best
    

def int_to_bytes(int:int, no_bytes:int):
    """
    Parses the given unsigned integer to an array of bytes using the specified number of bytes
    If the integer is too big for the given number of bytes, an error is raised
    """
    return int.to_bytes(no_bytes)

def bytes_to_int(bytes, no_bytes:int, start:int = 0):
    """
    Given an array of bytes, returns the unsigned integer it represents
    Starts the parsing at the specified position and ends after no_bytes bytes
    """
    return int.from_bytes(bytes[start:(start+no_bytes)])

def string_to_bytes(string:str):
    """
    Converts the given string to a null-terminated array of bytes
    """
    return string.encode() + b'\x00'

def bytes_to_string(bytes, start:int = 0):
    """
    Extracts a string from a null-terminated array of bytes
    Starts the parsing at the specified position
    All bytes after the null terminated are ignored
    """
    bytes[start:].split('\x00', 1)[0].decode()