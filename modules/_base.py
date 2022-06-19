import irc
import re
import logging
import config

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

    _pattern_init = "(\S+)"
    '''Regular expression capturing groups after command character'''
    IGNORE_PUBLIC = False
    '''When True, only respond over private query'''

    @property
    def pattern(self):
        '''Regular expression to check against each message'''
        return self.__pattern
    @pattern.setter
    def pattern(self, val):
        if isinstance(val, str):
            self.__pattern = re.compile("^"+self.CMD_CHAR+val, re.UNICODE)
        elif isinstance(val, re._pattern_type):
            self.__pattern = val

    def __new__(clazz):
        inst = IRCModule.__new__(clazz)
        if hasattr(config, "COMMAND_CHAR"):
            inst.CMD_CHAR = config.COMMAND_CHAR
        else:
            inst.CMD_CHAR = '!'
        return inst

    def __init__(self):
        super(CommandMod, self).__init__()
        self.log = logging.getLogger("irc.modules")
        self.__pattern = re.compile("^"+self.CMD_CHAR+self._pattern_init, re.UNICODE)
        
    def on_privmsg(self, connection, event):
        try:
            match = self.pattern.search(event.arguments[0])
            if match:
                self.log.debug("command match detected in privmsg: %s", self.pattern)
                self.on_command(connection, event.source, 
                                event.source.nick, match.groups())
        except Exception as e:
            self.log.exception("Command error: %s", e)

    def on_pubmsg(self, connection, event):
        if not self.IGNORE_PUBLIC:
            try:
                match = self.pattern.search(event.arguments[0])
                if match:
                    self.log.debug("command match detected in pubmsg: %s", self.pattern)
                    self.on_command(connection, event.source, 
                                    event.target, match.groups())
            except Exception as e:
                self.log.exception("Command error: %s", e)

    def on_command(self, connection, commander, replyto, groups):
        """Called when self.pattern matches a message.

        connection - the corresponding irc.ServerConnection
        commander - nickmask of the user who sent the message
        replyto - the channel where the message appeared if public, 
                  nick of commander if private
        groups - matching regex groups from pattern
        """
        connection.privmsg(replyto, "what's %s?" % groups[0])

class TriggerMod(CommandMod):
    """A superclass for IRCModules that should trigger on content in a message"""
    
    def __new__(clazz):
        inst = CommandMod.__new__(clazz)
        inst.CMD_CHAR = ".*"
        return inst

    def on_command(self, connection, commander, replyto, groups):
        """Equivalent to on_trigger, from superclass"""
        self.on_trigger(connection, commander, replyto, groups)
        
    def on_trigger(self, connection, commander, replyto, groups):
        """Called when self.pattern matches a message.

        connection - the corresponding irc.ServerConnection
        commander - nickmask of the user who sent the message
        replyto - the channel where the message appeared if public, 
                  nick of commander if private
        groups - matching regex groups from pattern

        (Alias for on_command)
        """
        connection.privmsg(replyto, "\"%s\" matches trigger for %s" % (groups[0], type(self).__name__))

def trim_nick(nick):
    """Return the nick minus op/voice decorators"""
    if nick.startswith(('@','+')):
        return nick[1:]
    else:
        return nick
