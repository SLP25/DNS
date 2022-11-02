from server.zoneTransfer import zoneTransferSP
from server.serverConfig import ServerConfig

config = ServerConfig("/home/ruioliveira02/Documents/Projetos/DNS/config/sp.conf")
zoneTransferSP(config, "127.0.0.1", 4200)