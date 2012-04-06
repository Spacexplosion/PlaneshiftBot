import os
import logging
import logging.handlers
import irclib
import config

class IRCModule:

    def __init__(self):
        self.serverchans = {}

    def on_welcome(self, connection, event):
        if hasattr(config, "AUTOJOIN_CHANNELS"):
            for chan in config.AUTOJOIN_CHANNELS:
                if isinstance(chan, str):
                    connection.join(chan)
                else:
                    if len(chan) == 1 or connection.server in chan[1]:
                        connection.join(chan[0])

    def on_join(self, connection, event):
        channel = Channel(event.target(), connection.server)
        if channel.server not in self.serverchans:
            self.serverchans[channel.server] = {}
        self.serverchans[channel.server][channel.name] = channel

    def on_pubmsg(self, connection, event):
        channel = self.serverchans[connection.server][event.target()]
        logargs = {"nick" : irclib.nm_to_n(event.source()),
                   "nickmask" : event.source(),
                   "server" : connection.server}
        channel.log.info(event.arguments()[0], extra=logargs)

class Channel:

    def __init__(self, name, server):
        self.name = irclib.IRCFoldedCase(name)
        self.server = irclib.FoldedCase(server)
        self.log = logging.getLogger(self.name.lower() +"@"+ self.server.lower())

        if self.name.startswith('#'):
            lowername = self.name.lower()[1:]
        else:
            lowername = self.name.lower()
        logfilename = "logs/"
        if hasattr(config, "CHAN_LOG_FILENAME"):
            logfilename += config.CHAN_LOG_FILENAME % \
                             {"name":lowername, "server":self.server.lower()}
        else:
            logfilename += lowername +"@"+ self.server.lower()
        loghandler = logging.handlers.TimedRotatingFileHandler(logfilename,
                                                               when="midnight")
        logdatefmt = None
        if hasattr(config, "CHAN_LOG_TIME_FORMAT"):
            logdatefmt = config.CHAN_LOG_TIME_FORMAT
        if hasattr(config, "CHAN_LOG_MSG_FORMAT"):
            logmsgfmt = config.CHAN_LOG_MSG_FORMAT
        else:
            logmsgfmt = "<%(nick)s> %(message)s"

        format = logging.Formatter("%(asctime)s "+ logmsgfmt, logdatefmt)
        loghandler.setFormatter(format)
        self.log.addHandler(loghandler)
        self.log.setLevel(logging.INFO)
