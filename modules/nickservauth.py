import logging
import re
import irc
import irc.events
import irc.strings
import config
import modules

class IRCModule(modules.IRCModule):
    """Authenticate with Nickserv and track other registered users.

    Depends on channels module to recognize online users."""

    default_ns_mask = "NickServ!*@*"
    default_ns_prompt = ".*IDENTIFY.*"

    def __init__(self):
        super(IRCModule, self).__init__()
        self.serverusers = {}
        self.chanmod = None
        self.log = logging.getLogger("irc.nsauth")
        
    def get_auth_for(self, server, nick):
        """Return the auth name for the nick or None"""
        auth = None
#        servkey = server.lower()
#        nickkey = irc.strings.lower(nick)
#        if nickkey in self.serverusers[servkey]:
#            auth = self.serverusers[servkey][nickkey]
        return auth

    def get_nicks_for(self, server, authname):
        """Return a list of nicks auth'ed with authname"""
        return [n for (n, a) in self.serverusers[server.lower()].iteritems() \
                    if a == authname]

    def on_load(self, bot):
        super(IRCModule, self).on_load(bot)
        if "channels" in bot.modules:
            self.chanmod = bot.modules["channels"]
        else:
            self.log.warn("channels module required for user tracking.")

    def on_welcome(self, connection, event):
        self.serverusers[irc.strings.FoldedCase(connection.server)] = {}
        if hasattr(connection, "AUTHDATA_MOD") \
           and connection.AUTHDATA_MOD == "nickservauth":
            if not hasattr(connection, "NICKSERV_MASK"):
                connection.NICKSERV_MASK = self.default_ns_mask
            if not hasattr(connection, "NICKSERV_PROMPT"):
                connection.NICKSERV_PROMPT = self.default_ns_prompt

    def on_privnotice(self, connection, event):
        if hasattr(connection, "NICKSERV_MASK") \
           and irc.client.mask_matches(event.source, connection.NICKSERV_MASK) \
           and hasattr(connection, "NICKSERV_PROMPT") \
           and re.match(connection.NICKSERV_PROMPT, event.arguments[0]) \
           and hasattr(connection, "NICKSERV_PASS"):
            self.log.info("Responding to Nickserv authentication request")
            connection.privmsg("Nickserv", "IDENTIFY %s" % connection.NICKSERV_PASS);
#    on_endofnames_priority = 10
#    def on_endofnames(self, connection, event):
#        nicks = [modules.trim_nick(n) for n in \
#                     self.chanmod.get_users_for(connection.server,
#                                                event.arguments[0])]
#        for nick in nicks:
#            connection.mode(nick, "")

#    def on_join(self, connection, event):
#        nick = event.source.nick
#        connection.mode(nick, "")

#    def on_umodeis(self, connection, event):
#        self.log.debug(event)
        
#    def on_quit(self, connection, event):
#        servkey = connection.server.lower()
#        nickkey = irc.strings.lower(event.source.nick)
#        if nickkey in self.serverusers[servkey]:
#            del self.serverusers[servkey][nickkey]

    def on_disconnect(self, connection, event):
        servkey = connection.server.lower()
        if servkey in self.serverusers:
            del self.serverusers[servkey]
