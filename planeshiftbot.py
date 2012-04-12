from __future__ import with_statement
import sys
import os
import traceback
import logging
import threading
import getopt
import irclib
import modules

logging.basicConfig(format="%(levelname)s: %(message)s",
                    level=logging.INFO,
                    stream=sys.stdout)

class PlaneshiftBot:

    def __init__(self, config_path="./"):
        self.modules = {}
        self.connections = {}
        self.dccs = []
        self.irc = irclib.IRC(fn_to_add_timeout=self._add_timer)
        self._timers = set()
        self._timers_lock = threading.Lock()
        self.log = logging.getLogger("ircbot")

        self.__load_config(config_path)

        if not os.path.isdir("logs"):
            os.mkdir("logs")
        logformat = logging.Formatter("%(asctime)s %(levelname)s: %(message)s",
                                      "%Y-%m-%d %H:%M:%S")
        loghandler = logging.FileHandler("logs/bot.log")
        loghandler.setFormatter(logformat)
        if hasattr(config, "LOGLEVEL"):
            self.log.setLevel(getattr(logging, config.LOGLEVEL))
            loghandler.setLevel(self.log.level)
            logging.root.handlers[0].setLevel(logging.ERROR)
        self.log.addHandler(loghandler)

        self.irc.add_global_handler("all_events", self._local_dispatcher)
        self.__load_modules(config.MODULES)

    def __load_config(self, path):
        global config
        self.log.info("Loading config from %s", path)
        try:
            if path not in sys.path:
                sys.path.insert(0, path)
            config = __import__("config")
        except (ImportError, OSError):
            self.log.critical("No config.py file found at %s \nQuitting...", path)
            sys.exit(1)
        if not (hasattr(config, "SERVER_LIST") and
                hasattr(config, "MODULES")):
            self.log.critical("Necessary entries missing from config.py. Quitting...")
            sys.exit(1)

    def __load_modules(self, mod_list):
        for name in mod_list:
            self.log.info("Loading module %s", name)
            try:
                __import__("modules." + name)
                mod = getattr(modules, name)
                if hasattr(mod, "IRCModule"):
                    self.add_module(name, mod.IRCModule())
            except ImportError:
                self.log.error("Couldn't import module %s", name)

    def _local_dispatcher(self, connection, event):
        handler = "on_" + event.eventtype()
        if hasattr(self, handler):
            getattr(self, handler)(connection, event)

    def _add_timer(self, secs):
        self.log.debug("Scheduling timeout for %d seconds", secs)
        t = threading.Timer(secs, self._timer_callback)
        with self._timers_lock:
            self._timers.add(t)
            t.start()

    def _timer_callback(self):
        self.log.debug("Timeout triggered")
        self.irc.process_timeout()
        if self._timers_lock.acquire(False):
            for t in list(self._timers):
                if not t.isAlive():
                    self._timers.remove(t)
            self._timers_lock.release()

    def add_module(self, name, ircmod):
        """Register event handlers for a new module.

        name - string name for the module
        ircmod - an object containing irclib event handler methods
        """
        for evname in irclib.all_events + ['all_events'] + unlisted_events:
            handler = "on_" + evname
            priority = 0
            if hasattr(ircmod, handler + "_priority"):
                priority = getattr(ircmod, handler + "_priority")
            if hasattr(ircmod, handler):
                self.irc.add_global_handler(evname, 
                                            getattr(ircmod, handler),
                                            priority)
        self.modules[name] = ircmod

    def del_module(self, name):
        """Unregister event handlers for a module.

        name - string name for the module
        """
        if name not in self.modules:
            return
        ircmod = self.modules[name]
        for evname in irclib.all_events + ['all_events'] + unlisted_events:
            handler = "on_" + evname
            if hasattr(ircmod, handler):
                self.irc.remove_global_handler(evname, getattr(ircmod, handler))
        del self.modules[name]

    def connect(self, server_list):
        """Connect to a list of servers.

        server_list - a list of dictionaries containing keyword arguments for
                      irclib.ServerConnection.connect()
        """
        for serverargs in server_list:
            connection = self.irc.server()
            try:
                self.log.info("Connecting to %s", serverargs['server'])
                self.connections[serverargs['server']] = connection
                # As of irclib 0.5.0, ipv6 is the only parameter not stored 
                #  inside the ServerConnection. If that changes, this if block 
                #  can go.
                if "ipv6" in serverargs:
                    connection.ipv6 = serverargs['ipv6']
                else:
                    connection.ipv6 = False
                connection.connect(**serverargs)
            except irclib.ServerConnectionError:
                e = irclib.Event("disconnect", "", "", ["Failed to connect"])
                self.on_disconnect(connection, e)
            except Exception:
                self.log.error("Configuration failure on %s", serverargs['server'])
                self.log.debug("".join(traceback.format_exception(*sys.exc_info())))

    def reconnect(self, connection=None, server=""):
        """Reconnect to a server.

        connection - irclib.ServerConnection that has previously connected
        server - hostname to look up; ignored if connection is given
        """
        if connection is None and server not in self.connections:
            self.log.error("Tried to reconnect to new server: %s", server)
            return
        elif connection is None:
            connection = self.connections[server]
        self.log.info("Reconnecting to %s", connection.server)
        c = connection
        try:
            connection.connect(c.server, c.port, c.nickname, c.password, 
                               c.username, c.ircname, c.localaddress, 
                               c.localport, (c.ssl is not None), c.ipv6)
        except irclib.ServerConnectionError:
            e = irclib.Event("disconnect", "", "", ["Failed to reconnect"])
            self.on_disconnect(connection, e)

    def on_disconnect(self, connection, event):
        """Handle disconnect events by scheduling reconnect."""
        self.log.warn("Disconnected from %s: %s", 
                      connection.server, event.arguments()[0])
        if hasattr(config, "RECONNECT_WAIT"):
            delay = config.RECONNECT_WAIT
        else:
            delay = 60
        if delay >= 0:
            self.irc.execute_delayed(delay, self.reconnect, (connection,))

    def start(self):
        """Run the bot. Blocks forever."""
        self.connect(config.SERVER_LIST)
        self.irc.process_forever()


# As of irclib 0.5.0, these events are not listed with the others.
# If this changes, the explicit mention here must be removed.
unlisted_events = ['nick', 'topic']

def main(args):
    path = "./"
    daemon = False
    (optlist, otherargs) = getopt.getopt(args[1:], "c:dh", 
                                         ['help'])
    for (option, arg) in optlist:
        if option == "-c":
            path = arg
        if option == "-d":
            daemon = True
        if option == "-h" or option == "--help":
            print ("options:\n" +
                   "  -c <path> : change config/working directory\n"+
                   "  -d        : daemonize")
            sys.exit(0)
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    os.chdir(path)

    if daemon:
        try:
            pid = os.fork()
            if pid == 0: #child
                os.setsid()
            else: #parent
                sys.exit(0)
            pid = os.fork()
            if pid > 0: #child
                print ("Starting daemon pid %d" % pid)
                pidfile = open("bot.pid", "w")
                pidfile.write(str(pid))
                pidfile.close()
                os._exit(0)
            # else grandchild
        except Exception:
            print ("Failed to daemonize.")

    bot = PlaneshiftBot(path)
    bot.start()

if __name__ == "__main__":
    main(sys.argv)
