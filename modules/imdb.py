import httplib
import urllib
import re
import irc
import logging
import modules
import config

class IRCModule(modules.CommandMod):
    """Print IMDb movie info to the channel"""

    patternstr = "imdb\s+(.+)"
    help = "Gets basic info on this bot"

    # "PRIVMSG %s :%s" limited to 512 bytes including CR/LF
    maxPlotMsg = 400

    def __init__(self):
        self.log = logging.getLogger("irc.imdb")

    def on_command(self, connection, commander, replyto, groups):

        http = httplib.HTTPConnection("omdbapi.com")
        http.request("GET", "/?plot=full&t="
                     + urllib.quote(groups[0]))
        resp = http.getresponse()
        if (resp.status == httplib.OK):
            respstr = resp.read()
            try:
                movinfo = eval(respstr)
            except (SyntaxError):
                self.log.error("Could not parse: " + respstr)
                return

            if (movinfo['Response'] == "False"):
                connection.privmsg(replyto, "No results.")
                return
            
            movtitle = movinfo['Title']

            connection.privmsg(replyto, \
                str(movtitle) + 
                " (" + str(movinfo['Year']) + ") " +
                " Runtime: " + str(movinfo['Runtime']) +
                " Rating: " + str(movinfo['imdbRating']) +
                " Genre: " + str(movinfo['Genre']))
            i = 0
            if 'Plot' in movinfo:
                while i < len(movinfo['Plot']):
                    connection.privmsg(replyto, \
                                       movinfo['Plot'][i:i+self.maxPlotMsg])
                    i += self.maxPlotMsg
            else:
                connection.privmsg(replyto, "There is no plot")
        else:
            self.log.warning("HTTP Error " + str(resp.status) +": "+ resp.reason)
        http.close()
