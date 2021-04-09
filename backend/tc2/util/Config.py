from enum import Enum


class BrokerEndpoint(Enum):
    PAPER = 1
    LIVE = 2


class Config:
    def __init__(self):
        self.reload()

    def reload(self):
        file = open("config.properties")
        lines = file.readlines()
        self.settings = {}
        for line in lines:
            if line.startswith("#") or len(line.strip()) == 0:
                continue
            comps = line.split("=")
            if len(comps) < 2:
                print("INVALID CONFIG LINE: '" + line + "'")
                continue
            key = line.split("=")[0].strip().lower()
            val = ''.join(line.split("=")[1:]).strip()
            self.settings[key] = val

    def get_setting(self, config_property: str) -> str:
        return self.settings[config_property] if config_property in self.settings else ""

    def get_endpoint(self) -> BrokerEndpoint:
        return BrokerEndpoint.LIVE if self.get_setting('alpaca.endpoint').lower() == 'live' else BrokerEndpoint.PAPER
