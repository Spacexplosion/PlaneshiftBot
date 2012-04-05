import os
import logging
import irclib
import config

class IRCModule:

    def on_welcome(self, connection, event):
        if hasattr(config, "AUTOJOIN_CHANNELS"):
            for chan in config.AUTOJOIN_CHANNELS:
                if isinstance(chan, str):
                    connection.join(chan)
                else:
                    if len(chan) == 1 or connection.server in chan[1]:
                        connection.join(chan[0])

#class ChannelName(irclib.IRCFoldedCase):
