DOMAIN_CHAR = '[a-zA-Z0-9\-]'
DOMAIN = f'({DOMAIN_CHAR}+\.)*{DOMAIN_CHAR}*\.'
DOMAIN_STEP = f'[^\.]{DOMAIN_CHAR}+[\.$]'

EMAIL_CHAR = '[A-Za-z0-9_%+-]' #dot is also supported, but must be preceeded by escape
EMAIL_ADDRESS = f'({EMAIL_CHAR}+\\\.)*{EMAIL_CHAR}+\.({DOMAIN_CHAR}+\.)+'

BYTE_RANGE = '([0-1]?[0-9]?[0-9]?|2[0-4][0-9]|25[0-5])'
IP_ADDRESS = f'({BYTE_RANGE}\.){{3}}{BYTE_RANGE}'

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