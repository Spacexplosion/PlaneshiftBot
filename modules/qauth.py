import logging
import irclib
import config
import modules

class IRCModule(modules.IRCModule):
    """Authenticate on QuakeNet and track other Q users.

    Depends on channels module to recognize online users."""

    def __init__(self):
        self.serverusers = {}
        self.chanmod = None
        self.log = logging.getLogger("irc.qauth")

    def get_auth_for(self, server, nick):
        """Return the auth name for the nick or None"""
        auth = None
        servkey = server.lower()
        nickkey = irclib.irc_lower(nick)
        if nickkey in self.serverusers[servkey]:
            auth = self.serverusers[servkey][nickkey]
        return auth

    def get_nicks_for(self, server, authname):
        """Return a list of nicks auth'ed with authname"""
        return [n for (n, a) in self.serverusers[server.lower()].iteritems() \
                    if a == authname]

    def on_load(self, bot):
        super(IRCModule, self).on_load(bot)
        irclib.numeric_events["330"] = "whoisauth"
        irclib.all_events.append("whoisauth")
        if "channels" in bot.modules:
            self.chanmod = bot.modules["channels"]
        else:
            self.log.warn("channels module required for user tracking.")

    def on_welcome(self, connection, event):
        if hasattr(connection, "QAUTH_USER") and \
           hasattr(connection, "QAUTH_PASS"):
            connection.send_raw(" ".join(["AUTH", 
                                         connection.QAUTH_USER, 
                                         connection.QAUTH_PASS]))
        else:
            self.log.warn("No credentials. Not authenticating...")
        self.serverusers[irclib.FoldedCase(connection.server)] = {}

    on_endofnames_priority = 10
    def on_endofnames(self, connection, event):
        if not hasattr(connection, "QAUTH_USER"):
            return
        nicks = [modules.trim_nick(n) for n in \
                     self.chanmod.get_users_for(connection.server,
                                                event.arguments()[0])]
        connection.whois(nicks)

    def on_join(self, connection, event):
        if not hasattr(connection, "QAUTH_USER"):
            return
        nick = irclib.nm_to_n(event.source())
        connection.whois([nick])

    def on_whoisauth(self, connection, event):
        self.log.debug("%s is authed as %s", *event.arguments()[:2])
        servkey = connection.server.lower()
        nick = irclib.IRCFoldedCase(event.arguments()[0])
        auth = irclib.IRCFoldedCase(event.arguments()[1])
        self.serverusers[servkey][nick] = auth

    def on_quit(self, connection, event):
        servkey = connection.server.lower()
        nickkey = irclib.irc_lower(irclib.nm_to_n(event.source()))
        if nickkey in self.serverusers[servkey]:
            del self.serverusers[servkey][nickkey]

    def on_disconnect(self, connection, event):
        servkey = connection.server.lower()
        if servkey in self.serverusers:
            del self.serverusers[servkey]
