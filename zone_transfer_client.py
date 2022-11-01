from server.zoneTransfer import zoneTransferSS
from server.serverConfig import ServerConfig

config = ServerConfig("empty")
config.primaryDomains["batata"] = ("127.0.0.1",4200)
zoneTransferSS(config)