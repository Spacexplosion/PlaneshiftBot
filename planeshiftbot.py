import sys
import os
import traceback
import logging
import getopt
import irclib
import modules

class PlaneshiftBot:

    def __init__(self, config_path="./"):
        self.modules = {}
        self.connections = []
        self.dccs = []
        self.irc = irclib.IRC()

        # initialize logging
        logging.basicConfig(format="%(levelname)s:%(message)s",
                            level=logging.DEBUG,
                            stream=sys.stdout)
        self.log = logging.getLogger(type(self).__name__)

        self.irc.add_global_handler("all_events", self._local_dispatcher)
        self.__load_config(config_path)
        self.__load_modules(config.MODULES)

    def __load_config(self, path):
        global config
        path = os.path.expanduser(path)
        path = os.path.normpath(path)
        self.log.debug("Loading config from %s", path)
        try:
            if path not in sys.path:
                sys.path.insert(0, path)
            os.chdir(path)
            config = __import__("config")
        except (ImportError, OSError):
            self.log.error("No config.py file found at %s \nQuitting...", path)
            sys.exit(1)
        if not (hasattr(config, "SERVER_LIST") and
                hasattr(config, "MODULES")):
            self.log.error("Necessary entries missing from config.py. Quitting...")
            sys.exit(1)

    def __load_modules(self, mod_list):
        for name in mod_list:
            try:
                __import__("modules." + name)
                mod = getattr(modules, name)
                self.add_module(name, mod.IRCModule())
            except ImportError:
                self.log.warn("Couldn't import module %s", name)

    def _local_dispatcher(self, connection, event):
        handler = "on_" + event.eventtype()
        if hasattr(self, handler):
            getattr(self, handler)(connection, event)

    def add_module(self, name, ircmod):
        """Register event handlers for a new module.

        name - string name for the module
        ircmod - an object containing irclib event handler methods
        """
        for evname in irclib.all_events + ['all_events']:
            handler = "on_" + evname
            if hasattr(ircmod, handler):
                self.irc.add_global_handler(evname, getattr(ircmod, handler))
        self.modules[name] = ircmod

    def del_module(self, name):
        """Unregister event handlers for a module.

        name - string name for the module
        """
        if name not in self.modules:
            return
        ircmod = self.modules[name]
        for evname in all_events + ['all_events']:
            handler = "on_" + evname
            if hasattr(ircmod, handler):
                self.irc.remove_global_handler(evname, getattr(ircmod, handler))
        del self.modules[name]

    def on_welcome(self, connection, event):
        connection.join("#planeshiftbot-testing")

    def connect(self, server_list):
        """Connect to a list of servers.

        server_list - a list of dictionaries containing keyword arguments for
                      irclib.ServerConnection.connect()
        """
        for serverargs in server_list:
            connection = self.irc.server()
            try:
                connection.connect(**serverargs)
                self.connections.append(connection)
            except irclib.ServerConnectionError:
                self.log.warn("Cannot connect to %s", serverargs['server'])
            except Exception:
                self.log.error("Configuration failure on %s", serverargs['server'])
                self.log.debug("".join(traceback.format_exception(*sys.exc_info())))

    def start(self):
        """Run the bot. Blocks forever."""
        self.connect(config.SERVER_LIST)
        self.irc.process_forever()

def main(args):
    path = "./"
    (optlist, otherargs) = getopt.getopt(args[1:], "c:dh", 
                                         ['help'])
    for (option, arg) in optlist:
        if option == "-c":
            path = arg
        if option == "-d":
            raise NotImplementedError # TODO daemonize
        if option == "-h" or option == "--help":
            print ("options:\n" +
                   "  -c <path> : change config/working directory\n"+
                   "  -d        : daemonize")
            sys.exit(0)
    bot = PlaneshiftBot(path)
    bot.start()

if __name__ == "__main__":
    main(sys.argv)
