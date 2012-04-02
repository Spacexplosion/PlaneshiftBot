import irclib
import logging
import sys

class LogBot(irclib.SimpleIRCClient):
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
        irclib.SimpleIRCClient.__init__(self)
        for e in irclib.protocol_events:
            self.connection.add_global_handler(e, self.lograw, -20)
        self.connection.add_global_handler("welcome", self._on_welcome, -10)
        logging.debug("Logging IRC...")

    def lograw(self, connection, event):
        logging.debug("%s: %s=>%s %s", event.eventtype(), event.source(), event.target(), event.arguments())

    def _on_welcome(self, connection, event):
        self.connection.join("#bottubot-testing")

    def _connect(self):
        self.connect("irc.quakenet.org", 6667, "bottubot")

    def start(self):
        self._connect()
        irclib.SimpleIRCClient.start(self)
