COMMENT_LINE = r'^\s*(#|$)'

DOMAIN_CHAR = r'[a-zA-Z0-9\-]'
DOMAIN = f'({DOMAIN_CHAR}+\.)*{DOMAIN_CHAR}*'
FULL_DOMAIN = f'({DOMAIN_CHAR}+\.)+'

EMAIL_CHAR = r'[A-Za-z0-9_%+-]' #dot is also supported, but must be preceeded by escape
EMAIL_ADDRESS = f'({EMAIL_CHAR}+\\\\\.)*{EMAIL_CHAR}+\.({DOMAIN_CHAR}+\.)+'

BYTE_RANGE = r'([0-1]?\d{0,2}|2[0-4]\d|25[0-5])'
PORT_RANGE = r'([0-5]?\d{0,4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])'
IP_ADDRESS = f'({BYTE_RANGE}\.){{3}}{BYTE_RANGE}'
IP_AND_PORT = f'{IP_ADDRESS}:{PORT_RANGE}'
IP_MAYBE_PORT = f'{IP_ADDRESS}(:{PORT_RANGE})?' #TODO: trocar ips para ip&port e ipmaybeport

#domain must be lowercase and fit DOMAIN
#the return value starts from the top domain and goes down the hierarchy
#exs:
# example.com. -> ['com', 'example']
# .            -> []
def split_domain(domain):
    return filter(None, domain.split('.')).reverse()

#domain and subdomain must be lowercase
#if they are the same, returns True
def is_subdomain(subdomain, domain):
    sd = split_domain(subdomain)
    d = split_domain(domain)

    if len(sd) < len(d):
        return False

    for i,x in enumerate(d):
        if x != sd[i]:
            return False

    return True