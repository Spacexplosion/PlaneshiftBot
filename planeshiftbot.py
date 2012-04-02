import irclib
import sys

class PlaneshiftBot:

    def __init__(self, config_path="./"):
        self.modules = {}
        self.connections = []
        self.dccs = []
        self.irc = irclib.IRC()

        self.__load_config(config_path)

    def __load_config(self, path):
        global config
        if path not in sys.path:
            sys.path.insert(0, path)
        config = __import__("config")
