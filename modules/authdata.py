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
        self.servermods = {}
        self.dummyauth = DummyAuthMod()
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
        skey = server.lower()
        authname = self.servermods[skey].get_auth_for(server, nick)
        if authname is not None:
            self.put_authdata(server, authname, datakey, data)

    def get_userdata(self, server, nick, datakey):
        """Retrieve data by key for an IRC user if auth'ed"""
        authname = None
        data = None
        skey = server.lower()
        authname = self.servermods[skey].get_auth_for(server, nick)
        if authname is not None:
            data = self.get_authdata(server, authname, datakey)
        return data

    def get_auth_for(self, server, nick):
        """Convenience method for auth mod pass-through"""
        return self.servermods[server.lower()].get_auth_for(server, nick)

    def get_nicks_for(self, server, authname):
        """Convenience method for auth mod pass-through"""
        return self.servermods[server.lower()].get_nicks_for(server, authname)

    def on_welcome(self, connection, event):
        server = irclib.FoldedCase(connection.server)
        self.serverauths[server] = \
            shelve.open(connection.server.lower() + "-auth.db")
        if hasattr(connection, "AUTHDATA_MOD") \
                and connection.AUTHDATA_MOD in self.bot.modules:
            self.servermods[server] = self.bot.modules[connection.AUTHDATA_MOD]
        else:
            self.servermods[server] = self.dummyauth
            self.log.info("No auth module for %s", connection.server)

    def on_disconnect(self, connection, event):
        servkey = connection.server.lower()
        if servkey in self.serverauths:
            self.serverauths[servkey].close()
            del self.serverauths[servkey]


class DummyAuthMod(object):
    
    def get_auth_for(self, server, nick):
        return None

    def get_nicks_for(self, server, name):
        return []
