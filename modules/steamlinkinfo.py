import httplib
import string
import json
import logging
import irc
import re
import modules
import config

class IRCModule(modules.TriggerMod):
    """Follow Steam Store links with game info"""

    _pattern_init = "http://store.steampowered.com/app/([0-9]+)/?"

    # "PRIVMSG %s :%s" limited to 512 bytes including CR/LF
    maxAboutMsg = 400

    def __init__(self):
        super(IRCModule, self).__init__()
        self.log = logging.getLogger("irc.steamlink")

    def on_trigger(self, connection, commander, replyto, groups):
        app_id = groups[0]
        self.log.debug("Retrieving data for Steam app id " + app_id)

        #Blocking HTTP call to Steam API
        http = httplib.HTTPConnection("store.steampowered.com")
        querystr = "/api/appdetails?appids=" + app_id
        http.request("GET", querystr)
        resp = http.getresponse()
        
        if resp.status != httplib.OK:
            self.log.warning("HTTP Error " + str(resp.status) +": "+ resp.reason)
            connection.privmsg(replyto, "Service unavailable. Try again later.")
            return
        
        respstr = resp.read()
        try:
            appdetails = json.loads(respstr)
        except (ValueError):
            self.log.error("Could not parse: " + respstr)
            return
        
        if app_id not in appdetails:
            self._invalidResult(connection, replyto, 
                                "Different AppId returned:" + app_id)
            return
        if not appdetails[app_id]['success']:
            self._invalidResult(connection, replyto, 
                                "Failed request for " + app_id)
            return

        data = appdetails[app_id]['data']
        answer = "[Steam] "+ data['name'] + \
                 " (" + data['release_date']['date'] +"); "
        if 'price_overview' in data:
            answer += str(data['price_overview']['final']/100.0) \
                      +" "+ data['price_overview']['currency']
        answer += "; Platforms: [" + \
                 ",".join([p[0] if p[1] else "" \
                           for p in data['platforms'].iteritems()]) + \
                 "] Genres: " + \
                 ",".join([g['description'] for g in data['genres']])
        if 'metacritic' in data:
            answer += " Metacritic: "+ str(data['metacritic']['score']) +"/100"
        connection.privmsg(replyto, answer)
        about = re.sub("(<[^>]*>)|\r", "", data['about_the_game'])
        if len(data['about_the_game']) > self.maxAboutMsg:
            end = string.rfind(data['about_the_game'], ' ', 0, self.maxAboutMsg)
            about = about[:end] + "..."
        connection.privmsg(replyto, about)

    def _invalidResult(self, connection, replyto, logmsg):
        self.log.error(logmsg)
        connection.privmsg(replyto, "No valid results.")
