import re
import irc
import modules

class IRCModule(modules.CommandMod):
    """Display help messages from other modules"""

    pattern = re.compile("!(triggers|help)\s?(\S+)?\s?(.+)?")

    def on_command(self, connection, commander, replyto, groups):
        response = "No help available for " + str(groups[1])
        if groups[0] == "help" and \
                groups[1] is not None and groups[1] in self.bot.modules:
            mod = self.bot.modules[groups[1]]
            if hasattr(mod, "help"):
                if callable(mod.help):
                    response = mod.help(groups[2])
                else:
                    response = mod.help
        else:
            response = "Loaded commands are " + \
                ', '.join([k for (k,v) in self.bot.modules.items() \
                               if isinstance(v, modules.CommandMod)])
        connection.privmsg(replyto, response)
