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

    _pattern_init = "imdb\s+(?:@([0-9]{4})\s+)?(.+)"
    help = "!imdb [@<year>] <movie name>"

    # "PRIVMSG %s :%s" limited to 512 bytes including CR/LF
    maxPlotMsg = 400

    def __init__(self):
        super(IRCModule, self).__init__()
        self.log = logging.getLogger("irc.imdb")

    def on_command(self, connection, commander, replyto, groups):
        arg_year = groups[0]
        arg_title = groups[1]
        self.log.debug("Searching OMDb for \""+ arg_title +"\" ("+ str(arg_year) +")")

        # Blocking call to search OMDb API
        http = httplib.HTTPConnection("omdbapi.com")
        http.request("GET", "/?s="
                     + urllib.quote(arg_title))
        resp = http.getresponse()
        if (resp.status == httplib.OK):
            respstr = resp.read()
            try:
                searchResult = json.loads(respstr)
            except (ValueError):
                self.log.error("Could not parse: " + respstr)
                return

            if 'Response' in searchResult \
               and searchResult['Response'] == "False":
                connection.privmsg(replyto, "No results.")
                return

            # Pick from search results by year or first
            if 'Search' in searchResult:
                result_list = searchResult['Search']
                movcount = len(result_list)
                result_years = [r["Year"] for r in result_list]
                if arg_year is None:
                    movinfo = result_list[0]
                    del result_years[0]
                else:
                    movinfo = None
                    for r in result_list:
                        if r["Year"] == arg_year:
                            movinfo = r
                            break
                    if movinfo is None:
                        connection.privmsg(replyto, "No matches for that year.")
                        return
            else:
                self.log.error("Search returned invalid results")
                connection.privmsg(replyto, "No valid results.")
                return
        else: #response status not OK
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

            # Warn about more results
            if arg_year is None and len(result_years) > 0:
                yearsstr = "("+ result_years[0]
                for y in result_years[1:]:
                    yearsstr += ", "+ y
                yearsstr += ")"
                connection.privmsg(replyto, "More results for other years "
                                   + yearsstr 
                                   +". Try again starting with @<year>")
        else: #response status not OK
            self.log.warning("HTTP Error " + str(resp.status) +": "+ resp.reason)
            connection.privmsg(replyto, "Service unavailable. Try again later.")

        http.close()
