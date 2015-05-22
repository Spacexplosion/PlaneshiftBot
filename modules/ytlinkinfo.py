import logging
import irc
import re
import random
import modules

class IRCModule(modules.TriggerMod):
    """Recognize YouTube links and print video info"""

    _pattern_init = "http(s)?://(youtu.be/|www.youtube.com/watch\?v=)([^&?]+).*"

    def __init__(self):
        super(IRCModule, self).__init__()
        self.log = logging.getLogger("irc.ytlink")

    def on_trigger(self, connection, commander, replyto, groups):
        connection.privmsg(replyto, "That's youtube video " + groups[2])
