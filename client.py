from common.udp import UDP

server = UDP()
server.send("Hello!".encode(), ("127.0.0.1", 4200))
message, addr = server.receive()
