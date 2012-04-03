import logging

REAL_RAW = False

class LogBot:

    def __init__(self):
        self.log = logging.getLogger(type(self).__name__)

    def on_all_events(self, connection, event):
        if (event.eventtype() == "all_raw_messages") and REAL_RAW:
            self.log.debug(event.arguments())
        elif (event.eventtype() != "all_raw_messages") and not REAL_RAW:
            self.log.debug("%s: %s=>%s %s", event.eventtype(), event.source(), event.target(), event.arguments())

IRCModule = LogBot
