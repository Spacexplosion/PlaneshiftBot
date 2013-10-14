import httplib
import urllib
import re
import irc
import logging
import modules
import config

class IRCModule(modules.CommandMod):
    """Display a custom message"""

    patternstr = "imdb\s+(.+)"
    help = "Gets basic info on this bot"

    # "PRIVMSG %s :%s" limited to 512 bytes including CR/LF
    maxPlotMsg = 400

    def __init__(self):
        self.log = logging.getLogger("irc.imdb")

    def on_command(self, connection, commander, replyto, groups):

        http = httplib.HTTPConnection("mymovieapi.com")
        http.request("GET", "/?type=json&plot=full&title="
                     + urllib.quote(groups[0]))
        resp = http.getresponse()
        if (resp.status == httplib.OK):
            respstr = resp.read()
            try:
                movinfo = eval(respstr)
            except (SyntaxError):
                self.log.error("Could not parse: " + respstr)
                return

            movtitle = movinfo[0]['title'].split("\n")

            connection.privmsg(replyto, \
                str(movtitle) + 
                " (" + str(movinfo[0]['year']) + ") " +
                " Runtime: " + str(movinfo[0]['runtime']) +
                " Rating: " + str(movinfo[0]['rating']) +
                " Genre: " + str(movinfo[0]['genres']))
            i = 0
            if 'plot' in movinfo[0]:
                while i < len(movinfo[0]['plot']):
                    connection.privmsg(replyto, \
                                       movinfo[0]['plot'][i:i+self.maxPlotMsg])
                    i += self.maxPlotMsg
            else:
                connection.privmsg(replyto, "There is no plot")
        else:
            self.log.warning("HTTP Error: " + resp.status + resp.reason)
        http.close()
