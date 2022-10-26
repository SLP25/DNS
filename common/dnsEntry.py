from enum import Enum
from exceptions import InvalidDNSEntryException

class EntryType(Enum):
    SOASP = 0
    SOAADMIN = 1
    SOASERIAL = 2
    SOAREFRESH = 3
    SOARETRY = 4
    SOAEXPIRE = 5
    NS = 6
    A = 7
    CNAME = 8
    MX = 9
    PTR = 10

class DNSEntry:
    def __init__(self, data, fromFile = False):
        if fromFile:
            self.__init_from_file__(data)
        else:
            self.__init_from_bytes__(data)

    def __init_from_file__(self, str):
        types = [member.name for member in EntryType]
        split = str.split()


        if len(split) in [4,5]:
            self.parameter = split[0]
            self.value = split[2]

            try:
                self.type = EntryType(types.index(split[1]))
            except ValueError:
                raise InvalidDNSEntryException("Unknown entry type")

            try:
                self.ttl = int(split[3])
                self.priority = 0 if len(split) == 4 else int(split[4])
            except ValueError:
                raise InvalidDNSEntryException("Priority and TTL must be integers")
        else:
            raise InvalidDNSEntryException("Line has more than 4/5 words")

        self.__validate_entry()

    def __init_from_bytes__(self, bytes):
        return

    def __validate_entry__(self):
        return None

    def to_bytes__(self):
        return []

    def __str__(self):
        return "{parameter} {type} {value} {ttl} {priority}".format(parameter = self.parameter, type = self.type.value, value = self.value, ttl = self.ttl, priority = self.priority)