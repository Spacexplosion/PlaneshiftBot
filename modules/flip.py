import upsidedown
import re
import irc
import logging
import modules
import config

class IRCModule(modules.CommandMod):
    """Flip text upside down

    Requires upsidedown package. (https://pypi.python.org/pypi/upsidedown)"""

    patternstr = "flip\s+(.+)"
    help = "Gets basic info on this bot"

    def __init__(self):
        self.log = logging.getLogger("irc.flip")

    def on_command(self, connection, commander, replyto, groups):
        response = u"(\u256F\u00B0\u25A1\u00B0)\u256F \uFE35 " + upsidedown.transform(groups[0])
        connection.privmsg(replyto, response)
