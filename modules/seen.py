from datetime import datetime
import shelve
import irclib
import modules

class IRCModule(modules.CommandMod, modules.ModCom):
    """Stores and retrieves on command the last time a nick has been used.

    Depends on channels module to recognize nick changes, and quits."""

    def __init__(self):
        self.db = {}

    def _get_user(self, servkey, nick):
        if nick in self.db[servkey]:
            return self.db[servkey][nick]
        else:
            return User(nick)

    def on_welcome(self, connection, event):
        db[irclib.FoldedCase(connection.server)] = \
            shelve.open(connection.server.lower() + "-seen.db")

    def on_disconnect(self, connection, event):
        servkey = connection.server.lower()
        db[servkey].close()
        del db[servkey]

    def on_pubmsg(self, connection, event):
        super(IRCModule, self).on_pubmsg(connection, event)
        servkey = connection.server.lower()
        nick = irclib.nm_to_n(event.source())
        user = self._get_user(servkey, nick)
        user.lastspoke = datetime.utcnow()
        self.db[servkey][nick] = user


class User(object):

    def __init__(self, nick):
        self.nick = nick
        self.lastchannel = None
        self.lastseen = None
        self.lastspoke = None
