import httplib
import urllib
import json
import re
import string
import irc
import logging
import modules
import config

class IRCModule(modules.CommandMod):
    """Print IMDb movie info to the channel"""

    _pattern_init = "imdb\s+(.+)"
    help = "!imdb <movie name>"

    # "PRIVMSG %s :%s" limited to 512 bytes including CR/LF
    maxPlotMsg = 400

    def __init__(self):
        super(IRCModule, self).__init__()
        self.log = logging.getLogger("irc.imdb")

    def on_command(self, connection, commander, replyto, groups):
        self.log.debug("Searching OMDb for \""+ groups[0] +"\"")

        # Blocking call to search OMDb API
        http = httplib.HTTPConnection("omdbapi.com")
        http.request("GET", "/?s="
                     + urllib.quote(groups[0]))
        resp = http.getresponse()
        if (resp.status == httplib.OK):
            respstr = resp.read()
            try:
                results = json.loads(respstr)
            except (ValueError):
                self.log.error("Could not parse: " + respstr)
                return

            if 'Response' in results and results['Response'] == "False":
                connection.privmsg(replyto, "No results.")
                return

            #Pick from search results by year or first
            if 'Search' in results:
                movinfo = results['Search'][0]
            else:
                self.log.error("Search returned invalid results")
                connection.privmsg(replyto, "No valid results.")
                return
        else:
            self.log.warning("HTTP Error " + str(resp.status) +": "+ resp.reason)
            connection.privmsg(replyto, "Service unavailable. Try again later.")
            return
            
        # Second request for movie details
        http.request("GET", "/?plot=full&i=" + movinfo['imdbID'])
        resp = http.getresponse()
        if (resp.status == httplib.OK):
            respstr = resp.read()
            try:
                movinfo = json.loads(respstr)
            except (ValueError):
                self.log.error("Could not parse: " + respstr)
                return

            if 'Response' in movinfo and movinfo['Response'] == "False":
                self.log.error("Failed to lookup ID for search result")
                connection.privmsg(replyto, "No valid results.")
                return

            movtitle = movinfo['Title'].decode('utf-8', 'ignore')

            connection.privmsg(replyto, \
                movtitle + 
                " (" + movinfo['Year'].decode('utf-8', 'ignore') + ") " +
                " Runtime: " + movinfo['Runtime'].decode('utf-8', 'ignore') +
                " Rating: " + movinfo['imdbRating'].decode('utf-8', 'ignore') +
                " Genre: " + movinfo['Genre'].decode('utf-8', 'ignore'))

            start = 0
            if 'Plot' in movinfo and movinfo['Plot'] != "N/A":
                plot = movinfo['Plot'].decode('utf-8', 'ignore')
                while start < len(plot):
                    end = -1
                    if start+self.maxPlotMsg < len(plot):
                        end = string.rfind(plot, ' ', start, start+self.maxPlotMsg)
                    if (end == -1):
                        end = start+self.maxPlotMsg
                    connection.privmsg(replyto, \
                                       plot[start:end])
                    start = end
            else:
                connection.privmsg(replyto, "There is no plot")
        else:
            self.log.warning("HTTP Error " + str(resp.status) +": "+ resp.reason)
            connection.privmsg(replyto, "Service unavailable. Try again later.")

        http.close()
