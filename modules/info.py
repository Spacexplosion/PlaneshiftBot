import re
import irc
import modules
import config

class IRCModule(modules.CommandMod):
    """Display a custom message"""

    patternstr = "info"
    help = "Gets basic info on this bot"

    def on_command(self, connection, commander, replyto, groups):
        if hasattr(config, "INFO_STRING"):
            lines = config.INFO_STRING.split('\n')
            for line in lines:
                connection.privmsg(replyto, line)
