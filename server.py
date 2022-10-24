from common.udp import UDP

server = UDP(binding = True)

while(True):
    msg, address = server.receive()
    server.send("Batata".encode(), address)