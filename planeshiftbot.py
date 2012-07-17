#!/usr/bin/python2.7

from __future__ import with_statement
import sys
import os
import signal
import traceback
import logging
import threading
import Queue
import getopt
import irclib
import modules

logging.basicConfig(format="%(name)s %(levelname)s: %(message)s",
                    level=logging.DEBUG,
                    stream=sys.stdout)

class PlaneshiftBot:

    def __init__(self, config_path="./"):
        self.modules = {}
        self.connections = {}
        self.dccs = []
        self.irc = irclib.IRC()
        self._timers = set()
        self._timers_lock = threading.Lock()
        self.log = logging.getLogger("irc")
        self.daemonized = False

        self.__load_config(config_path)

        if not os.path.isdir("logs"):
            os.mkdir("logs")
        logformat = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s",
                                      "%Y-%m-%d %H:%M:%S")
        loghandler = logging.FileHandler("logs/bot.log")
        loghandler.setFormatter(logformat)
        if hasattr(config, "LOGLEVEL"):
            self.log.setLevel(getattr(logging, config.LOGLEVEL))
            loghandler.setLevel(self.log.level)
        self.log.addHandler(loghandler)

        self.irc.add_global_handler("all_events", self._local_dispatcher)
        self.__load_modules(config.MODULES)

    def __load_config(self, path):
        global config
        self.log.info("Loading config from %s", path)
        try:
            os.chdir(path)
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

        # set defaults
        if not hasattr(config, "SERVER_PROPS"):
            config.SERVER_PROPS = []
        if not hasattr(config, "KEEP_ALIVE_FREQ"):
            config.KEEP_ALIVE_FREQ = 30
        if not (hasattr(config, "PING_TIMEOUT") and config.PING_TIMEOUT > 0):
            config.PING_TIMEOUT = 10
        if not hasattr(config, "RECONNECT_WAIT"):
            config.RECONNECT_WAIT = 60

    def __load_modules(self, mod_list):
        for name in mod_list:
            self.log.info("Loading module %s", name)
            try:
                __import__("modules." + name)
            except ImportError:
                self.log.error("Couldn't import module %s", name)
                return
            mod = getattr(modules, name)
            if hasattr(mod, "IRCModule") and \
                    issubclass(mod.IRCModule, modules.IRCModule):
                self.add_module(name, mod.IRCModule())
            else:
                self.log.warn("No IRCModule to load in %s", name)

    def _local_dispatcher(self, connection, event):
        handler = "on_" + event.eventtype()
        if hasattr(self, handler):
            getattr(self, handler)(connection, event)

    def _add_timer(self, secs, function, args=tuple()):
        #self.log.debug("Scheduling timeout for %d seconds", secs)
        t = threading.Timer(secs, self._timer_callback, (function, args))
        with self._timers_lock:
            self._timers.add(t)
            t.start()

    def _timer_callback(self, function, args):
        #self.log.debug("Timeout triggered")
        function(*args)
        if self._timers_lock.acquire(False):
            for t in list(self._timers):
                if not t.isAlive():
                    self._timers.remove(t)
            self._timers_lock.release()

    def _keep_alive(self, connection):
        if not connection.is_connected():
            return # timed out already
        self._add_timer(config.KEEP_ALIVE_FREQ, 
                        self._keep_alive, (connection,))
        if hasattr(connection, "pingtimer") and connection.pingtimer.isAlive():
            self.log.debug("keep alive overlapped ping timer. %d > %d",
                           config.PING_TIMEOUT, config.KEEP_ALIVE_FREQ)
            return # if PING_TIMEOUT > KEEP_ALIVE_FREQ
        self.log.debug("keep alive for %s", connection.server)
        connection.pingtimer = threading.Timer(config.PING_TIMEOUT,
                                               connection.disconnect,
                                               ("Ping Timeout",))
        connection.pingtimer.start()
        connection.ping(connection.server)

    def add_module(self, name, ircmod):
        """Register event handlers for a new module.

        name - string name for the module
        ircmod - a modules.IRCModule containing irclib event handler methods
        """
        if isinstance(ircmod, modules.IRCModule):
            ircmod.on_load(self)
        else:
            raise ValueError("ircmod must be subclass of modules.IRCModule")
        for evname in irclib.all_events + ['all_events']:
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
        for evname in irclib.all_events + ['all_events']:
            handler = "on_" + evname
            if hasattr(ircmod, handler):
                self.irc.remove_global_handler(evname, getattr(ircmod, handler))
        ircmod.on_unload()
        del self.modules[name]

    def connect(self, server_list):
        """Connect to a list of servers.

        server_list - a list of dictionaries containing keyword arguments for
                      irclib.ServerConnection.connect()
        """
        i = 0
        for serverargs in server_list:
            connection = self.irc.server()
            try:
                self.log.info("Connecting to %s", serverargs['server'])
                self.connections[serverargs['server']] = connection
                connection.connect(**serverargs)
                if i < len(config.SERVER_PROPS):
                    for (prop, val) in config.SERVER_PROPS[i].iteritems():
                        setattr(connection, prop, val)
                if config.KEEP_ALIVE_FREQ > 0:
                    self._add_timer(config.KEEP_ALIVE_FREQ,
                                    self._keep_alive, (connection,))
            except irclib.ServerConnectionError:
                e = irclib.Event("disconnect", "", "", ["Failed to connect"])
                self.on_disconnect(connection, e)
            except Exception:
                self.log.error("Configuration failure on %s", serverargs['server'])
                self.log.debug("".join(traceback.format_exception(*sys.exc_info())))
            i += 1

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
        try:
            connection.reconnect()
            if config.KEEP_ALIVE_FREQ > 0:
                self._add_timer(config.KEEP_ALIVE_FREQ,
                                self._keep_alive, (connection,))
        except irclib.ServerConnectionError:
            e = irclib.Event("disconnect", "", "", ["Failed to reconnect"])
            self.on_disconnect(connection, e)

    def on_disconnect(self, connection, event):
        """Handle disconnect events by scheduling reconnect."""
        self.log.warn("Disconnected from %s: %s", 
                      connection.server, event.arguments()[0])
        if config.RECONNECT_WAIT >= 0:
            self._add_timer(config.RECONNECT_WAIT, 
                            self.reconnect, (connection,))

    def on_pong(self, connection, event):
        """Handle answers to ping for keep-alives."""
        if hasattr(connection, "pingtimer"):
            connection.pingtimer.cancel()

    def daemonize(self):
        """Fork and background process, exiting the parent"""
        try:
            pid = os.fork()
            if pid == 0: #child
                os.setsid()
            else: #parent
                os._exit(0)
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
        self.daemonized = True

    def start(self, daemon=False):
        """Run the bot. Blocks forever."""
        if daemon:
            self.daemonize()
        self.connect(config.SERVER_LIST)
        self._halting = threading.Event()
        while not self._halting.isSet():
            #self.irc.process_timeout() called by process_once
            self.irc.process_once(0.1)

    def stop(self):
        """Halt execution of start() and clean up threads"""
        if not hasattr(self, "_halting"):
            return # not started
        elif self._halting.isSet():
            return # already stopped
        for c in self.connections.values():
            if hasattr(c, "pingtimer"):
                c.pingtimer.cancel()
            c.disconnect("Halting")
        for t in self._timers:
            t.cancel()
        self._halting.set()


def main(args):
    global bot
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
    signal.signal(signal.SIGTERM, signalhandler)

    bot = PlaneshiftBot(path)
    if daemon:
        logging.root.removeHandler(logging.root.handlers[0])
    else:
        logging.root.handlers[0].setLevel(bot.log.level)
    try:
        bot.start(daemon)
    except (KeyboardInterrupt, SystemExit):
        pass
    except:
        bot.log.error("".join(traceback.format_exception(*sys.exc_info())))
    finally:
        exit()

def signalhandler(signum, frame):
    sys.exit(0)

def exit():
    global bot
    bot.stop()
    bot.log.info("EXITING")
    for mod in bot.modules.values():
        mod.on_unload()
    logging.shutdown()
    if bot.daemonized:
        os.remove("bot.pid")
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
