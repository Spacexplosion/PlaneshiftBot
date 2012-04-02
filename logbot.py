import irclib
import logging
import sys

class LogBot(irclib.SimpleIRCClient):
    def __init__(self):
        logging.basicConfig(format="%(message)s", level=logging.DEBUG, stream=sys.stdout)
        irclib.SimpleIRCClient.__init__(self)
        self.connection.add_global_handler(all_events, self._lograw, 0)
        logging.debug("Logging IRC...")

    def _lograw(self, connection, event):
        logging.debug("%s: %s=>%s %s", event.eventtype(), event.source(), event.target(), event.arguments())

    def on_welcome(self, connection, event):
        self.connection.join("#bottubot-testing")

    def start(self):
        self.connect("irc.quakenet.org", 6667, "bottubot")
        irclib.SimpleIRCClient.start(self)
