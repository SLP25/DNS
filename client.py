import re
import sys
import common.utils as utils
from common.dnsEntry import EntryType, ENTRY_TYPE
from common.dnsMessage import DNSMessage
from common.query import QueryInfo
from common.udp import UDP

def encode_msg(msg:DNSMessage) -> bytes:
    '''
    From a DNSMessage, returns the bytes to be sent through the socket
    '''
    return str(msg).encode() if debug else msg.to_bytes()

def decode_msg(bytes:bytes) -> DNSMessage:
    '''
    From the bytes received from the socket, returns the encoded DNSMessage
    If the bytes don't correspond to a valid DNSMessage, an InvalidDNSMessageException is raised
    '''
    if debug:
        return DNSMessage.from_string(bytes.decode())
    else:
        (msg, _) = DNSMessage.from_bytes(bytes)
        return msg

args = ' '.join(sys.argv[1:4])
match = re.search(f'{utils.IP_MAYBE_PORT} (?P<d>{utils.FULL_DOMAIN}) (?P<t>{ENTRY_TYPE})', args)
if not match:
    raise ValueError("Invalid format for program args")
recursive = '-r' in sys.argv
debug = '-n' not in sys.argv    #by default, runs in debug mode

ip = match.group('ip')
port = int(match.group('port')) if match.group('port') else utils.DEFAULT_PORT

query = QueryInfo(match.group('d'), EntryType[match.group('t')])
msg = DNSMessage.from_query(query, recursive)

try:
    server = UDP(timeout=3)
    server.send(encode_msg(msg), ip, port)
    resp, _, _ = server.receive()
    response = decode_msg(resp)
    print(response.print())
except Exception as e:
    print("Query failed:", e)