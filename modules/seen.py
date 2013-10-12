from datetime import datetime
import shelve
import re
import logging
import irc
import irc.strings
import modules

class IRCModule(modules.CommandMod):
    """Stores and retrieves on command the last time a nick has been used.

    Depends on the channels module to recognize online users."""

    pattern = re.compile("!seen (\S+)")
    help = "!seen <nick>"

    def __init__(self):
        self.db = {}
        self.log = logging.getLogger("irc.seen")

    def _get_user(self, servkey, nick):
        nickkey = irc.strings.lower(nick)
        if nickkey in self.db[servkey]:
            return self.db[servkey][nickkey]
        else:
            return User(nick)

    def _nick_exit(self, servkey, nick, reason, chan=None):
        user = self._get_user(servkey, nick)
        user.lastseen = datetime.utcnow()
        user.lastaction = reason
        if chan is not None:
            user.lastchannel = chan
        self.db[servkey][user.nick.lower()] = user

    def on_welcome(self, connection, event):
        self.db[irc.strings.FoldedCase(connection.server)] = \
            shelve.open(connection.server.lower() + "-seen.db")

    def on_disconnect(self, connection, event):
        servkey = connection.server.lower()
        if servkey in self.db:
            self.db[servkey].close()
            del self.db[servkey]

    def on_command(self, connection, commander, replyto, groups):
        servkey = connection.server.lower()
        nickkey = irc.strings.lower(groups[0])
        user = None
        if nickkey in self.db[servkey]:
            user = self.db[servkey][nickkey]
        if "channels" in self.bot.modules:
            channels = self.bot.modules["channels"].get_channels_for(servkey,
                                                                     nickkey)
        else:
            channels = []
            self.log.warn("seen requires channels module to see online users")
        if not (user is None or channels):
            response = "%s was last seen %s ago: " % \
                       (groups[0],
                        tdelta_str(datetime.utcnow() - user.lastseen))
            if user.lastaction in ['part', 'kick']:
                response += "%sed from %s" % (user.lastaction,
                                              user.lastchannel)
            else:
                response += user.lastaction
            connection.privmsg(replyto, response)
        elif channels:
            channames = [c.name for c in channels]
            if replyto in channames:
                response = groups[0] + " is here"
            else:
                response = groups[0] + " is on " + ','.join(channames)
            if not (user is None or user.lastspoke is None):
                response += " and last spoke %s ago in %s" % \
                            (tdelta_str(datetime.utcnow() - user.lastspoke),
                             user.lastchannel)
            connection.privmsg(replyto, response)
        else:
            connection.privmsg(replyto, "who?")

    def on_pubmsg(self, connection, event):
        super(IRCModule, self).on_pubmsg(connection, event)
        servkey = connection.server.lower()
        nick = event.source.nick
        user = self._get_user(servkey, nick)
        user.lastspoke = datetime.utcnow()
        user.lastchannel = event.target
        self.db[servkey][user.nick.lower()] = user

    def on_part(self, connection, event):
        servkey = connection.server.lower()
        nick = event.source.nick
        self._nick_exit(servkey, nick, "part", event.target)

    def on_kick(self, connection, event):
        servkey = connection.server.lower()
        self._nick_exit(servkey, event.arguments[0], "kick", event.target)

    def on_nick(self, connection, event):
        servkey = connection.server.lower()
        nick = event.source.nick
        self._nick_exit(servkey, nick, "nick change")

    def on_quit(self, connection, event):
        servkey = connection.server.lower()
        nick = event.source.nick
        self._nick_exit(servkey, nick, "quit")


class User(object):

    def __init__(self, nick):
        self.nick = irc.strings.IRCFoldedCase(nick)
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
