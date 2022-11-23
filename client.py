import re
import sys
import common.utils as utils
from common.dnsEntry import EntryType, ENTRY_TYPE
from common.dnsMessage import DNSMessage
from common.query import QueryInfo
from common.udp import UDP


args = ' '.join(sys.argv[1:])
match = re.search(f'{utils.IP_MAYBE_PORT} (?P<d>{utils.FULL_DOMAIN}) (?P<t>{ENTRY_TYPE})(?P<r> -?[rR])?', args)
if not match:
    raise ValueError("Invalid format for program args")

ip = match.group('ip')
port = int(match.group('port')) if match.group('port') else utils.DEFAULT_PORT

query = QueryInfo(match.group('d'), EntryType[match.group('t')])
msg = DNSMessage.from_query(query, match.group('r') != None)

server = UDP(timeout=5)  #TODO: timeout?
server.send(str(msg).encode(), ip, port)    #TODO: normal mode (send as binary)
message, _, _ = server.receive()
print(message.decode()) #TODO: user-friendly mode (Exemplo 6 do enunciado)