import httplib
import urllib
import re
import string
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
            start = 0
            if 'Plot' in movinfo and movinfo['Plot'] != "N/A":
                while start < len(movinfo['Plot']):
                    end = -1
                    if start+self.maxPlotMsg < len(movinfo['Plot']):
                        end = string.rfind(movinfo['Plot'], ' ', start, start+self.maxPlotMsg)
                    if (end == -1):
                        end = start+self.maxPlotMsg
                    connection.privmsg(replyto, \
                                       movinfo['Plot'][start:end])
                    start = end
            else:
                connection.privmsg(replyto, "There is no plot")
        else:
            self.log.warning("HTTP Error " + str(resp.status) +": "+ resp.reason)
        http.close()
