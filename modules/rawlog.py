import logging
import modules

REAL_RAW = False

class LogBot(modules.IRCModule):
    """Log all events supported by irclib"""

    def __init__(self):
        super(IRCModule, self).__init__()
        self.log = logging.getLogger("irc.raw")

    def on_all_events(self, connection, event):
        if (event.type == "all_raw_messages") and REAL_RAW:
            self.log.debug(event.arguments)
        elif (event.type != "all_raw_messages") and not REAL_RAW:
            self.log.debug("%s: %s=>%s %s", event.type, event.source, event.target, event.arguments)

IRCModule = LogBot
