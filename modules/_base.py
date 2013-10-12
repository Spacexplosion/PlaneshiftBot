import irc
import re

class IRCModule(object):
    """Base class for all Planeshiftbot modules."""

    def on_load(self, bot):
        """Called just before modules' event handlers start"""
        self.bot = bot

    def on_unload(self):
        """Called just before the module is deleted"""
        pass


class CommandMod(IRCModule):
    """A superclass for IRCModules that should respond to a command."""

    pattern = re.compile("^!(\S+)", re.UNICODE)
    '''Regular expression to check against each message'''
    IGNORE_PUBLIC = False
    '''When True, only respond over private query'''

    def on_privmsg(self, connection, event):
        match = self.pattern.search(event.arguments[0])
        if match:
            self.on_command(connection, event.source, 
                            event.source.nick, match.groups())

    def on_pubmsg(self, connection, event):
        if not self.IGNORE_PUBLIC:
            match = self.pattern.search(event.arguments[0])
            if match:
                self.on_command(connection, event.source, 
                                event.target, match.groups())

    def on_command(self, connection, commander, replyto, groups):
        """Called when self.pattern matches a message.

        connection - the corresponding irc.ServerConnection
        commander - nickmask of the user who sent the message
        replyto - the channel where the message appeared if public, 
                  nick of commander if private
        groups - matching regex groups from pattern
        """
        connection.privmsg(replyto, "what's %s?" % groups[0])


def trim_nick(nick):
    """Return the nick minus op/voice decorators"""
    if nick.startswith(('@','+')):
        return nick[1:]
    else:
        return nick
