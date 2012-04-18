import irclib
import re
import random
import modules

class IRCModule(modules.CommandMod):

    pattern = re.compile("^!roll (\d+)d(\d+)([+-]\d+)?", 
                         re.UNICODE | re.IGNORECASE)

    def on_command(self, connection, commander, replyto, groups):
        n = s = m = sum = 0
        try:
            n = int(groups[0])
            s = int(groups[1])
            if groups[2] is not None:
                m = int(groups[2])
        except ValueError:
            return
        if n > 100000: # arbitrary iteration limit
            connection.privmsg(replyto, "%s is trying to break me. :(" % \
                                   irclib.nm_to_n(commander))
            return
        for i in range(n):
            sum += random.randint(1, s)
        sum += m
        connection.privmsg(replyto,"%s rolls %d" % \
                               (irclib.nm_to_n(commander),  sum))