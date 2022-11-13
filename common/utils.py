COMMENT_LINE = r'^\s*(#|$)'

DOMAIN_CHAR = r'[a-zA-Z0-9\-]'
DOMAIN = f'({DOMAIN_CHAR}+\.)*{DOMAIN_CHAR}+'
FULL_DOMAIN = f'({DOMAIN_CHAR}+\.)+'

EMAIL_CHAR = r'[A-Za-z0-9_%+-]' #dot is also supported, but must be preceeded by escape
EMAIL_ADDRESS = f'({EMAIL_CHAR}+\\\\\.)*{EMAIL_CHAR}+\.({DOMAIN_CHAR}+\.)+'

BYTE_RANGE = r'([0-1]?\d{0,2}|2[0-4]\d|25[0-5])'
PORT_RANGE = r'([0-5]?\d{0,4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])'
IP_ADDRESS = f'({BYTE_RANGE}\.){{3}}{BYTE_RANGE}'
IP_AND_PORT = f'(?P<ip>{IP_ADDRESS}):(?P<port>{PORT_RANGE})'
IP_MAYBE_PORT = f'(?P<ip>{IP_ADDRESS})(:(?P<port>{PORT_RANGE}))?' #TODO: trocar ips para ip&port e ipmaybeport


#Same as haskell's flatmap
#Is lazy (returns a generator)
flat_map = lambda f, xs: (y for ys in xs for y in f(ys))


#the string is converted to lowercase
#also, if the domain doesn't end in . it is appended
def normalize_domain(domain:str):
    if domain == '':
        return '.'
    
    return (domain if domain[-1] == '.' else domain + '.').lower()

#domain must be lowercase and match DOMAIN
#the return value starts from the top domain and goes down the hierarchy
#exs:
# example.com. -> ['com', 'example']
# .            -> []
def split_domain(domain:str):
    return filter(None, domain.split('.')).reverse()

#domain and subdomain must be lowercase
#if they are the same, returns True
def is_subdomain(subdomain:str, domain:str):
    sd = split_domain(subdomain)
    d = split_domain(domain)

    if len(sd) < len(d):
        return False

    for i,x in enumerate(d):
        if x != sd[i]:
            return False

    return True

#domains and subdomain must be lowercase
#returns the domain in domains that best matches the subdomain
def best_match(subdomain:str, domains):
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
    

def int_to_bytes(int:int, no_bytes):
    return int.to_bytes(no_bytes)

def bytes_to_int(bytes, no_bytes:int, start:int = 0):
    return int.from_bytes(bytes[start:(start+no_bytes)])

def string_to_bytes(string:str):
    return string + b'\x00'

def bytes_to_string(bytes, start:int = 0):
    bytes[start:].split('\x00', 1)[0]