from server.zoneTransfer import zoneTransferSS
from server.serverConfig import ServerConfig

config = ServerConfig("config/ss.conf")
zoneTransferSS(config)