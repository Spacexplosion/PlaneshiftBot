import logging
import irc
import re
import random
import modules
import config
from apiclient.discovery import build

class IRCModule(modules.TriggerMod):
    """Recognize YouTube links and print video info"""

    _pattern_init = "http(s)?://(youtu.be/|www.youtube.com/watch\?v=)([^&?]+).*"

    API_VERSION = "v3"
    
    def __init__(self):
        super(IRCModule, self).__init__()
        self.log = logging.getLogger("irc.ytlink")

    def on_load(self, bot):
        super(IRCModule, self).on_load(bot)
        if not hasattr(config, "YOUTUBE_API_KEY"):
            raise AttributeError("YOUTUBE_API_KEY required")
        self.__initYT()

    def __initYT(self):
        self.YTservice = build("youtube", IRCModule.API_VERSION,
                               developerKey=config.YOUTUBE_API_KEY)

    def on_trigger(self, connection, commander, replyto, groups):
        request = self.YTservice.videos().list(part="contentDetails,snippet",
                                               id=groups[2])
        result = request.execute()
        if len(result.items()) > 0:
            title = result['items'][0]['snippet']['title']
            connection.privmsg(replyto,
                               "[YouTube video] Title: \x02%s\x0f " % \
                               title)
        else:
            connection.privmsg(replyto, "No video found for id:" + groups[2])
