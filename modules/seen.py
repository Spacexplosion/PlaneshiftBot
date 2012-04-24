from datetime import datetime
import shelve
import re
import irclib
import modules

class IRCModule(modules.CommandMod, modules.ModCom):
    """Stores and retrieves on command the last time a nick has been used.

    Depends on channels module to recognize nick changes, and quits."""

    pattern = re.compile("!seen (\S+)")

    def __init__(self):
        self.db = {}

    def _get_user(self, servkey, nick):
        nickkey = irclib.irc_lower(nick)
        if nickkey in self.db[servkey]:
            return self.db[servkey][nickkey]
        else:
            return User(nick)

    def on_welcome(self, connection, event):
        self.db[irclib.FoldedCase(connection.server)] = \
            shelve.open(connection.server.lower() + "-seen.db")

    def on_disconnect(self, connection, event):
        servkey = connection.server.lower()
        self.db[servkey].close()
        del self.db[servkey]

    def on_command(self, connection, commander, replyto, groups):
        servkey = connection.server.lower()
        nickkey = irclib.irc_lower(groups[0])
        if nickkey in self.db[servkey]:
            user = self.db[servkey][nickkey]
            if user.lastspoke is not None:
                response = "%s last spoke %s ago in %s" % \
                           (groups[0], 
                            tdelta_str(datetime.utcnow() - user.lastspoke),
                            user.lastchannel)
                connection.privmsg(replyto, response)

    def on_pubmsg(self, connection, event):
        super(IRCModule, self).on_pubmsg(connection, event)
        servkey = connection.server.lower()
        nick = irclib.nm_to_n(event.source())
        user = self._get_user(servkey, nick)
        user.lastspoke = datetime.utcnow()
        user.lastchannel = event.target()
        self.db[servkey][user.nick] = user


class User(object):

    def __init__(self, nick):
        self.nick = nick
        self.lastseen = None
        self.lastaction = None
        self.lastspoke = None
        self.lastchannel = None


def tdelta_str(tdelta):
    str = ""
    if tdelta.days != 0:
        str += "%d days" % tdelta.days
        if abs(tdelta.seconds) > 60:
            str += ", "
    (hours, r) = divmod(tdelta.seconds, 3600)
    (minutes, seconds) = divmod(r, 60)
    if hours != 0:
        str += "%d hours" % hours
        if abs(tdelta.seconds) > 60:
            str += ", "
    if minutes != 0:
        str += "%d minutes" % minutes
    if len(str) == 0:
        str = "%d seconds" % seconds
    return str
