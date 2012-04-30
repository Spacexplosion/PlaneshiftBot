import re
import irclib
import modules
import config

class IRCModule(modules.CommandMod):

    pattern = re.compile("!info")
    help = "Gets basic info on this bot"

    def on_command(self, connection, commander, replyto, groups):
        if hasattr(config, "INFO_STRING"):
            lines = config.INFO_STRING.split('\n')
            for line in lines:
                connection.privmsg(replyto, line)
