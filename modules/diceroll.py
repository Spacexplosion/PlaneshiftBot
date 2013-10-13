import irc
import re
import random
import modules

class IRCModule(modules.CommandMod):
    """Roll a combination of virtual dice"""

    patternstr = "roll (\d+)d(\d+)([+-]\d+)?"

    help = "!roll <number>d<sides>[(+|-)<modifier>]"

    def __init__(self):
        self.__pattern = re.compile("^"+self.CMD_CHAR+self.patternstr,
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
                               commander.nick)
            return
        for i in range(n):
            sum += random.randint(1, s)
        sum += m
        connection.privmsg(replyto,"%s rolls %d" % \
                           (commander.nick,  sum))
