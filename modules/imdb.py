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
        querystr = "/?plot=full&t=" + urllib.quote(arg_title)
        if arg_year is not None:
            querystr += "&y=" + arg_year
        http.request("GET", querystr)
        resp = http.getresponse()
        if resp.status == httplib.OK:
            respstr = resp.read()
            try:
                movinfo = json.loads(respstr)
            except (ValueError):
                self.log.error("Could not parse: " + respstr)
                return

            if 'Response' in movinfo and movinfo['Response'] == "False":
                self.log.error("Failed to lookup movie info")
                connection.privmsg(replyto, "No valid results.")
                return

            movtitle = movinfo['Title']

            connection.privmsg(replyto, \
                movtitle + 

                " (" + movinfo['Year'] + ") " +
                " Runtime: " + movinfo['Runtime'] +
                " Rating: " + movinfo['imdbRating'] +
                " Genre: " + movinfo['Genre'])

            start = 0
            if 'Plot' in movinfo and movinfo['Plot'] != "N/A":
                plot = movinfo['Plot']
                while start < len(plot):
                    end = -1
                    if start+self.maxPlotMsg < len(plot):
                        end = string.rfind(plot, ' ', start, start+self.maxPlotMsg)
                    if end == -1:
                        end = start+self.maxPlotMsg
                    connection.privmsg(replyto, \
                                       plot[start:end])
                    start = end
            else:
                connection.privmsg(replyto, "There is no plot")

        else: #response status not OK
            self.log.warning("HTTP Error " + str(resp.status) +": "+ resp.reason)
            connection.privmsg(replyto, "Service unavailable. Try again later.")
            return

        # Second request for multiple results for no specific year
        if arg_year is None:
            http.request("GET", "/?s="
                         + urllib.quote(arg_title))
            resp = http.getresponse()
            if resp.status == httplib.OK:
                respstr = resp.read()
                try:
                    searchResult = json.loads(respstr)
                except (ValueError):
                    self.log.error("Could not parse: " + respstr)
                    return

                if 'Response' in searchResult \
                   and searchResult['Response'] == "False":
                    self.log.error("Failed to get movie search")
                    return

                if 'Search' in searchResult:
                    result_list = searchResult['Search']
                    movcount = len(result_list)
                    result_years = [r["Year"] for r in result_list]
                    #first result should always be same as title query but isn't
                    for i in xrange(len(result_years)):
                        if movinfo["Year"] == result_years[i]:
                            del result_years[i]
                            break
                    
                    if len(result_years) > 0:
                        yearsstr = "("+ result_years[0]
                        for y in result_years[1:]:
                            yearsstr += ", "+ y
                        yearsstr += ")"
                        connection.privmsg(replyto, "More results for other years "
                                           + yearsstr 
                                           +". Try again starting with @<year>")

                else:
                    self.log.error("Search returned invalid results")
                    return
            else: #response status not OK
                self.log.warning("HTTP Error " + str(resp.status) +": "+ resp.reason)
                return
        
        http.close()
