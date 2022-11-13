from server.zoneTransfer import zoneTransferSS
from server.serverData import ServerData

config = ServerData("config/ss.conf")
zoneTransferSS(config)