import os
import logging
from logging.handlers import TimedRotatingFileHandler
import irclib
import config

class IRCModule:

    def __init__(self):
        self.serverchans = {}
        self.log = logging.getLogger("ircbot.channels")

    def on_welcome(self, connection, event):
        if hasattr(config, "AUTOJOIN_CHANNELS"):
            for chan in config.AUTOJOIN_CHANNELS:
                if isinstance(chan, str):
                    connection.join(chan)
                else:
                    if len(chan) == 1 or connection.server in chan[1]:
                        connection.join(chan[0])

    def on_invite(self, connection, event):
        if not (hasattr(config, "JOIN_INVITES") and config.JOIN_INVITES):
            return
        connection.join(event.arguments()[0])

    def on_join(self, connection, event):
        if irclib.nm_to_n(event.source()) == connection.get_nickname():
            self.log.debug("join handled: new channel %s", event.target())
            channel = Channel(event.target(), connection.server)
            if channel.server not in self.serverchans:
                self.serverchans[channel.server] = {}
            self.serverchans[channel.server][channel.name] = channel
        else:
            self.log.debug("join handled: %s != %s",
                           irclib.nm_to_n(event.source()),
                           connection.get_nickname())
            channel = self.serverchans[connection.server.lower()]\
                                      [irclib.irc_lower(event.target())]
        channel.log.info("** %s joined %s", event.source(), event.target())
        channel.add_user(irclib.nm_to_n(event.source()))

    def on_namreply(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irclib.irc_lower(event.arguments()[1])]
        if not channel.in_namreply:
            channel.users = {}
            channel.in_namreply = True
        for nick in event.arguments()[2].split(' '):
            channel.add_user(nick)

    def on_endofnames(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irclib.irc_lower(event.arguments()[0])]
        channel.in_namreply = False

    def on_pubmsg(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irclib.irc_lower(event.target())]
        logargs = {"nick" : irclib.nm_to_n(event.source()),
                   "nickmask" : event.source(),
                   "server" : connection.server}
        channel.log_pubmsg(event.arguments()[0], extra=logargs)

    def on_action(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irclib.irc_lower(event.target())]
        channel.log.info("%s %s",
                         irclib.nm_to_n(event.source()),
                         event.arguments()[0])

    def on_nick(self, connection, event):
        previous = irclib.nm_to_n(event.source())
        for channel in self.serverchans[connection.server.lower()].values():
            if irclib.irc_lower(previous) in channel.users:
                channel.change_nick(previous, event.target())
                channel.log.info("** %s is now known as %s", 
                                 previous,
                                 event.target())

    def on_mode(self, connection, event):
        servkey = connection.server.lower()
        chankey = irclib.irc_lower(event.target())
        if chankey in self.serverchans[servkey]:
            # channel mode versus user mode
            channel = self.serverchans[servkey][chankey]
            channel.log.info("%s mode change '%s' by %s",
                             event.target(),
                             " ".join(event.arguments()),
                             irclib.nm_to_n(event.source()))

    def on_topic(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irclib.irc_lower(event.target())]
        channel.log.info("%s topic changed by %s to: %s",
                         event.target(),
                         irclib.nm_to_n(event.source()),
                         event.arguments()[0])

    def on_currenttopic(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irclib.irc_lower(event.arguments()[0])]
        channel.log.info("%s topic is: %s", *event.arguments())

    def on_part(self, connection, event):
        parter = irclib.nm_to_n(event.source())
        servkey = connection.server.lower()
        chankey = irclib.irc_lower(event.target())
        channel = self.serverchans[servkey][chankey]
        channel.log.info("** %s leaves %s", parter, event.target())
        channel.del_user(parter)
        if parter == connection.get_nickname():
            self.log.debug("Leaving %s", channel.name)
            del self.serverchans[servkey][chankey]

    def on_kick(self, connection, event):
        servkey = connection.server.lower()
        chankey = irclib.irc_lower(event.target())
        channel = self.serverchans[servkey][chankey]
        kickee = event.arguments()[0]
        reason = event.arguments()[1]
        channel.log.info("** %s kicks %s: %s",
                         irclib.nm_to_n(event.source()),
                         kickee,
                         reason)
        channel.del_user(kickee)
        if kickee == connection.get_nickname():
            self.log.debug("Leaving %s", channel.name)
            del self.serverchans[servkey][chankey]
            if hasattr(config, "KICK_REJOIN_WAIT") \
                    and config.KICK_REJOIN_WAIT > 0:
                connection.irclibobj.execute_delayed(config.KICK_REJOIN_WAIT,
                                                     connection.join,
                                                     (channel.name,))

    def on_quit(self, connection, event):
        quitter = irclib.nm_to_n(event.source())
        self.log.debug("quit handled for %s", quitter)
        for channel in self.serverchans[connection.server.lower()].values():
            if irclib.irc_lower(quitter) in channel.users:
                channel.del_user(quitter)
                channel.log.info("** %s has quit. (%s)", 
                                 quitter, 
                                 event.arguments()[0])

    def on_disconnect(self, connection, event):
        servkey = connection.server.lower()
        for channel in self.serverchans[servkey].values():
            channel.log.info("** Disconnected from %s: %s",
                             connection.server, 
                             event.arguments()[0])
        del self.serverchans[servkey]


class Channel(object):

    def __init__(self, name, server):
        self.name = irclib.IRCFoldedCase(name)
        if self.name.startswith('#'):
            lowername = self.name.lower()[1:]
        else:
            lowername = self.name.lower()
        self.server = irclib.FoldedCase(server)
        self.users = {}
        self.in_namreply = False
        self.log = logging.getLogger(lowername +"@"+ self.server.lower())

        logfilename = "logs/"
        if hasattr(config, "CHAN_LOG_FILENAME"):
            logfilename += config.CHAN_LOG_FILENAME % \
                             {"name":lowername, "server":self.server.lower()}
        else:
            logfilename += lowername +"@"+ self.server.lower()
        self._loghandler = TimedRotatingFileHandler(logfilename,
                                                    when="midnight")
        logdatefmt = None
        if hasattr(config, "CHAN_LOG_TIME_FORMAT"):
            logdatefmt = config.CHAN_LOG_TIME_FORMAT
        if hasattr(config, "CHAN_LOG_MSG_FORMAT"):
            pubmsgfmt = config.CHAN_LOG_MSG_FORMAT
        else:
            pubmsgfmt = "<%(nick)s> %(message)s"

        self._pubmsgFormatter = logging.Formatter("%(asctime)s "+ pubmsgfmt, 
                                                  logdatefmt)
        self._eventmsgFormatter = logging.Formatter("%(asctime)s %(message)s",
                                                    logdatefmt)
        self._loghandler.setFormatter(self._eventmsgFormatter)
        self.log.addHandler(self._loghandler)
        self.log.setLevel(logging.INFO)
        self.log.propagate = False

    def __del__(self):
        self.log.removeHandler(self._loghandler)

    def log_pubmsg(self, *args, **kwargs):
        """Does special formatting for pubmsgs

        */**args - all arguments to Logger.info
        """
        self._loghandler.setFormatter(self._pubmsgFormatter)
        self.log.info(*args, **kwargs)
        self._loghandler.setFormatter(self._eventmsgFormatter)

    def add_user(self, name):
        """Add name to user list"""
        self.users[irclib.IRCFoldedCase(Channel.trim_nick(name))] = None

    def del_user(self, name):
        """Remove name from user list"""
        del self.users[irclib.IRCFoldedCase(Channel.trim_nick(name))]

    def change_nick(self, before, after):
        """Switch out nick in the user list"""
        self.del_user(before)
        self.add_user(after)

    @classmethod
    def trim_nick(clas, nick):
        """Return the nick minus op/voice decorators"""
        if nick.startswith(('@','+')):
            return nick[1:]
        else:
            return nick
