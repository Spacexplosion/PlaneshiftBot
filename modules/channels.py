import os
import logging
from logging.handlers import TimedRotatingFileHandler
import irc
import irc.strings
import config
import modules

class IRCModule(modules.IRCModule):
    """Join/administrate channels and track users in them"""

    def __init__(self):
        super(IRCModule, self).__init__()
        self.serverchans = {}
        self.log = logging.getLogger("irc.channels")

    def get_channels_for(self, server, nick):
        """Return a list of channels nick is on"""
        channels = []
        for channel in self.serverchans[server.lower()].values():
            if irc.strings.lower(nick) in channel.users:
                channels.append(channel)
        return channels

    def get_users_for(self, server, channame):
        """Return a list of users on a channel"""
        skey = server.lower()
        ckey = irc.strings.lower(channame)
        users = []
        if skey in self.serverchans and ckey in self.serverchans[skey]:
            users = self.serverchans[skey][ckey].users.keys()
        return users

    def put_userdata(self, server, channame, nick, datapair):
        """Convenience method for using Channel.put_userdata()"""
        skey = server.lower()
        ckey = irc.strings.lower(channame)
        if skey in self.serverchans and ckey in self.serverchans[skey]:
            self.serverchans[skey][ckey].put_userdata(nick, *datapair)

    def get_userdata(self, server, channame, nick, datakey):
        """Convenience method for using Channel.get_userdata()"""
        skey = server.lower()
        ckey = irc.strings.lower(channame)
        data = None
        if skey in self.serverchans and ckey in self.serverchans[skey]:
           data = self.serverchans[skey][ckey].get_userdata(nick, datakey)
        return data

    def on_welcome(self, connection, event):
        if hasattr(config, "AUTOJOIN_CHANNELS"):
            for chan in config.AUTOJOIN_CHANNELS:
                if isinstance(chan, str):
                    connection.join(chan)
                elif len(chan) > 1 and isinstance(chan[1], str):
                    connection.join(chan[0], chan[1])
                elif len(chan) > 2:
                    try:
                        i = chan[1].index(connection.server)
                        connection.join(chan[0], chan[2][i])
                    except ValueError:
                        pass
                elif len(chan) == 1 or connection.server in chan[1]:
                    connection.join(chan[0])

    def on_invite(self, connection, event):
        if not (hasattr(config, "JOIN_INVITES") and config.JOIN_INVITES):
            return
        connection.join(event.arguments[0])

    def on_join(self, connection, event):
        if event.source.nick == connection.get_nickname():
            self.log.debug("join handled: new channel %s", event.target)
            channel = Channel(event.target, connection.server)
            if channel.server not in self.serverchans:
                self.serverchans[channel.server] = {}
            self.serverchans[channel.server][channel.name] = channel
        else:
            self.log.debug("join handled: %s != %s",
                           event.source.nick,
                           connection.get_nickname())
            channel = self.serverchans[connection.server.lower()]\
                                      [irc.strings.lower(event.target)]
        channel.log.info("** %s joined %s", event.source, event.target)
        channel.add_user(event.source.nick)

    def on_namreply(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irc.strings.lower(event.arguments[1])]
        if not channel.in_namreply:
            channel.users = {}
            channel.in_namreply = True
        for nick in event.arguments[2].split(' '):
            channel.add_user(nick)

    def on_endofnames(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irc.strings.lower(event.arguments[0])]
        channel.in_namreply = False

    def on_pubmsg(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irc.strings.lower(event.target)]
        logargs = {"nick" : event.source.nick,
                   "nickmask" : event.source,
                   "server" : connection.server}
        channel.log_pubmsg(event.arguments[0], extra=logargs)

    def on_pubnotice(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irc.strings.lower(event.target)]
        channel.log.info("*%s* %s",
                         event.source.nick,
                         event.arguments[0])

    def on_action(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irc.strings.lower(event.target)]
        channel.log.info("%s %s",
                         irc.client.NickMask(event.source).nick,
                         event.arguments[0])

    def on_nick(self, connection, event):
        previous = event.source.nick
        for channel in self.get_channels_for(connection.server, previous):
            channel.change_nick(previous, event.target)
            channel.log.info("** %s is now known as %s", 
                             previous,
                             event.target)

    def on_mode(self, connection, event):
        servkey = connection.server.lower()
        chankey = irc.strings.lower(event.target)
        if chankey in self.serverchans[servkey]:
            # channel mode versus user mode
            channel = self.serverchans[servkey][chankey]
            channel.log.info("%s mode change '%s' by %s",
                             event.target,
                             " ".join(event.arguments),
                             event.source.nick)

    def on_topic(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irc.strings.lower(event.target)]
        channel.log.info("%s topic changed by %s to: %s",
                         event.target,
                         event.source.nick,
                         event.arguments[0])

    def on_currenttopic(self, connection, event):
        channel = self.serverchans[connection.server.lower()]\
                                  [irc.strings.lower(event.arguments[0])]
        channel.log.info("%s topic is: %s", *event.arguments)

    def on_part(self, connection, event):
        parter = event.source.nick
        servkey = connection.server.lower()
        chankey = irc.strings.lower(event.target)
        channel = self.serverchans[servkey][chankey]
        channel.log.info("** %s leaves %s", parter, event.target)
        channel.del_user(parter)
        if parter == connection.get_nickname():
            self.log.debug("Leaving %s", channel.name)
            del self.serverchans[servkey][chankey]

    def on_kick(self, connection, event):
        servkey = connection.server.lower()
        chankey = irc.strings.lower(event.target)
        channel = self.serverchans[servkey][chankey]
        kickee = event.arguments[0]
        reason = event.arguments[1]
        channel.log.info("** %s kicks %s: %s",
                         event.source.nick,
                         kickee,
                         reason)
        channel.del_user(kickee)
        if kickee == connection.get_nickname():
            self.log.debug("Leaving %s", channel.name)
            del self.serverchans[servkey][chankey]
            if hasattr(config, "KICK_REJOIN_WAIT") \
                    and config.KICK_REJOIN_WAIT > 0:
                connection.execute_delayed(config.KICK_REJOIN_WAIT,
                                           connection.join,
                                           (channel.name,))

    def on_quit(self, connection, event):
        quitter = event.source.nick
        self.log.debug("quit handled for %s", quitter)
        for channel in self.get_channels_for(connection.server, quitter):
            channel.del_user(quitter)
            channel.log.info("** %s has quit. (%s)", 
                             quitter, 
                             event.arguments[0])

    def on_disconnect(self, connection, event):
        servkey = connection.server.lower()
        if servkey in self.serverchans:
            for channel in self.serverchans[servkey].values():
                channel.log.info("** Disconnected from %s: %s",
                                 connection.server, 
                                 event.arguments[0])
            del self.serverchans[servkey]

    def on_inviteonlychan(self, connection, event):
        self.log.warn("Cannot join %s, invite only", event.arguments[0])

    def on_bannedfromchan(self, connection, event):
        self.log.warn("Cannot join %s, banned", event.arguments[0])

    def on_badchannelkey(self, connection, event):
        self.log.warn("Cannot join %s, wrong password", event.arguments[0])


class Channel(object):

    def __init__(self, name, server):
        self.name = irc.strings.IRCFoldedCase(name)
        if self.name.startswith('#'):
            lowername = self.name.lower()[1:]
        else:
            lowername = self.name.lower()
        self.server = irc.strings.FoldedCase(server)
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

    def __str__(self):
        return self.name

    def log_pubmsg(self, *args, **kwargs):
        """Does special formatting for pubmsgs

        */**args - all arguments to Logger.info
        """
        self._loghandler.setFormatter(self._pubmsgFormatter)
        self.log.info(*args, **kwargs)
        self._loghandler.setFormatter(self._eventmsgFormatter)

    def add_user(self, name, data=None):
        """Add name to user list"""
        if data is None:
            data = {}
        self.users[irc.strings.IRCFoldedCase(modules.trim_nick(name))] = data

    def del_user(self, name):
        """Remove name from user list"""
        del self.users[irc.strings.IRCFoldedCase(modules.trim_nick(name))]

    def change_nick(self, before, after):
        """Switch out nick in the user list"""
        userdata = self.users[irc.strings.lower(before)]
        self.del_user(before)
        self.add_user(after, userdata)

    def put_userdata(self, nick, datakey, data):
        """Store a key-value pair for a user"""
        nickkey = irc.strings.lower(nick)
        if nickkey in self.users:
            alldata = self.users[nickkey]
            alldata[datakey] = data

    def get_userdata(self, nick, datakey):
        """Retrieve data by key for a user"""
        nickkey = irc.strings.lower(nick)
        data = None
        if nickkey in self.users and datakey in self.users[nickkey]:
            data = self.users[nickkey][datakey]
        return data
