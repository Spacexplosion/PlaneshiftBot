import logging
import irclib
import config
import modules

class IRCModule(modules.IRCModule):

    def __init__(self):
        self.serverusers = {}
        self.log = logging.getLogger("irc.qauth")

    def on_welcome(self, connection, event):
        if hasattr(connection, "QAUTH_USER") and \
           hasattr(connection, "QAUTH_PASS"):
            connection.send_raw(" ".join(["AUTH", 
                                         connection.QAUTH_USER, 
                                         connection.QAUTH_PASS]))
        else:
            self.log.warn("No credentials. Not authenticating...")
