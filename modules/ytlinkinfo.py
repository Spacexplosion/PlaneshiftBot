import logging
import irc
import re
import random
import modules
import config
from apiclient.discovery import build

class IRCModule(modules.TriggerMod):
    """Recognize YouTube links and print video info"""

    _pattern_init = "http(s)?://(youtu.be/|www.youtube.com/watch\?(.+&)?v=)([^&?]+).*"

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
        ytid = groups[3]
        request = self.YTservice.videos().list(part="snippet,contentDetails,statistics",
                                               id=ytid)
        result = request.execute()
        if len(result.items()) > 0:
            title = result['items'][0]['snippet']['title']
            chan = result['items'][0]['snippet']['channelTitle']
            (dura_m, dura_s) = time_parse(result['items'][0]['contentDetails']['duration'])
            views = result['items'][0]['statistics']['viewCount']
            likes = result['items'][0]['statistics']['likeCount']
            hates = result['items'][0]['statistics']['dislikeCount']
            connection.privmsg(replyto,
                               "[YouTube video] Title: \x02%s\x0f | Duration: %s:%s | Channel: %s | Views: %s | Likes: \x0303%s\x0f | Dislikes: \x0304%s\x0f" % \
                               (title, dura_m, dura_s, chan, views, likes, hates))
        else:
            connection.privmsg(replyto, "No video found for id:" + ytid)

re_time_parse = re.compile("PT(([0-9]+)M)?([0-9]+)S")
def time_parse(ptstr):
    m = '0'
    match = re_time_parse.search(ptstr)
    if not match.groups()[1] is None:
        m = match.groups()[1]
    return (m, match.groups()[2])
