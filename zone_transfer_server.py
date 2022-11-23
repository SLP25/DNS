from server.zoneTransfer import zoneTransferSP
from server.serverData import ServerData

config = ServerData("/home/ruioliveira02/Documents/Projetos/DNS/config/sp.conf")
zoneTransferSP(config, "utils.get_local_ip()", 4200)