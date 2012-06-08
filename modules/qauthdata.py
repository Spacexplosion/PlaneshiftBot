import logging
import shelve
import irclib
import config
import modules

class IRCModule(modules.IRCModule):
    """Persist data for authenticated users.

    Depends on qauth (or maybe others later)."""

    def __init__(self):
        self.serverauths = {}
        self.authmod = None
        self.log = logging.getLogger("irc.authdata")

    def put_authdata(self, server, name, datakey, data):
        """Store a key-value pair for a auth user"""
        skey = server.lower()
        nkey = irclib.irc_lower(name)
        if nkey not in self.serverauths[skey]:
            self.serverauths[skey][irclib.IRCFoldedCase(name)] = {}
        self.serverauths[skey][nkey][datakey] = data

    def get_authdata(self, server, name, datakey):
        """Retrieve data by key for an auth user"""
        skey = server.lower()
        nkey = irclib.irc_lower(name)
        data = None
        if nkey in self.serverauths[skey] \
                and datakey in self.serverauths[skey][nkey]:
            data = self.serverauths[skey][nkey][datakey]
        return data

    def put_userdata(self, server, nick, datakey, data):
        """Store a key-value pair for an IRC user if auth'ed"""
        authname = None
        if self.authmod is not None:
            authname = self.authmod.get_auth_for(server, nick)
        if authname is not None:
            self.put_authdata(server, authname, datakey, data)

    def get_userdata(self, server, nick, datakey):
        """Retrieve data by key for an IRC user if auth'ed"""
        authname = None
        data = None
        if self.authmod is not None:
            authname = self.authmod.get_auth_for(server, nick)
        if authname is not None:
            data = self.get_authdata(server, authname, datakey)
        return data

    def on_load(self, bot):
        super(IRCModule, self).on_load(bot)
        if "qauth" in bot.modules:
            self.authmod = bot.modules["qauth"]
        else:
            self.log.warn("No auth module found.")

    def on_welcome(self, connection, event):
        self.serverauths[irclib.FoldedCase(connection.server)] = \
            shelve.open(connection.server.lower() + "-auth.db")

    def on_disconnect(self, connection, event):
        servkey = connection.server.lower()
        if servkey in self.serverauths:
            self.serverauths[servkey].close()
            del self.serverauths[servkey]
