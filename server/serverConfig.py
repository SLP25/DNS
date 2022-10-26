from enum import Enum
from exceptions import NoConfigFileException

class ConfigType(Enum):
    DB = 0
    SP = 1
    SS = 2
    DD = 3
    ST = 4
    LG = 5

class ServerConfig:
    def __init__(self, filePath):
        self.primaryDomains = {}
        self.topServers = []
        self.logFile = ""
        self.authorizedSS = {}
        self.defaultServers = {}

        try:
            with open(filePath, "r") as file:
                data = file.read()

                for line in data.split('\n'):
                    self.__parseLine__(line)

        except FileNotFoundError:
            raise NoConfigFileException("Could not open " + filePath)

    def __parseLine__(self, line):
        if line == "":
            return

        if line[0] == '#':
            return

        types = [member.name for member in ConfigType]
        split = line.split()

        if len(split) == 3:
            try:
                lineType = ConfigType(types.index(split[1]))

                if lineType == ConfigType.DB:
                    self.__parse_db__(split)
                elif lineType == ConfigType.SP:
                    self.__parse_sp__(split)
                elif lineType == ConfigType.SS:
                    self.__parse_ss__(split)
                elif lineType == ConfigType.DD:
                    self.__parse_dd__(split)
                elif lineType == ConfigType.ST:
                    self.__parse_st__(split)
                elif lineType == ConfigType.LG:
                    self.__parse_lg__(split)
            except ValueError:
                raise InvalidConfigFileException(line + "has no valid type")
        else:
            raise InvalidConfigFileException(line + " contains more than 3 words")


    def __parse__db__(self, split):
        return

    def __validate_entry__(self):
        return None