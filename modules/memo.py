import logging
import re
import irclib
import config
import modules

class IRCModule(modules.CommandMod):
    """Send offline memos to authenticated users.

    Depends on authdata."""

    pattern = re.compile("memo\s+(.+)")
    IGNORE_PUBLIC = True

    def __init__(self):
        self.log = logging.getLogger("irc.memo")

    def on_load(self, bot):
        super(IRCModule, self).on_load(bot)
        if "authdata" not in bot.modules:
            raise RuntimeError("Memo service requires authdata module")
        self.datamod = bot.modules["authdata"]

    def on_command(self, connection, nickmask, nick, groups):
        cmd = groups[0].split(' ')
        if cmd[0] == "on":
            self.datamod.put_userdata(connection.server, nick,
                                      "memos_enable", True)
            memos = self.datamod.get_userdata(connection.server, nick,
                                              "memos")
            if memos is None:
                self.datamod.put_userdata(connection.server, nick,
                                          "memos", {})
        elif cmd[0] == "off":
            self.datamod.put_userdata(connection.server, nick,
                                      "memos_enable", False)
            self.datamod.put_userdata(connection.server, nick,
                                      "memos", {})
        elif cmd[0] == "read":
            memos = self.datamod.get_userdata(connection.server, nick, "memos")
            if memos is not None:
                for (sender, msgs) in memos:
                    for msg in msgs:
                        connection.privmsg(nick, "[%s] %s" % (sender, msg))
            self.datamod.put_userdata(connection.server, nick, "memos", {})
        elif cmd[0] == "send" and len(cmd) > 2:
            from_auth = self.datamod.get_auth_for(connection.server, nick)
            to_enabled = self.datamod.get_authdata(connection.server,
                                                   cmd[1], "memos_enable")
            to_memos = self.datamod.get_authdata(connection.server, 
                                                 cmd[1], "memos")

            if from_auth is None:
                connection.privmsg(nick, "You must authenticate and join a channel")
                return
            if to_enabled is False:
                connection.privmsg(nick, "User has disabled memos")
                return
            
            memo_q = []
            msg = ' '.join(cmd[2:])
            if to_memos is None:
                to_memos = {}
            if from_auth in to_memos:
                memo_q = to_memos[from_auth]
            self.log.debug("Storing message from %s: %s", from_auth, msg)
            memo_q.append(msg)
            to_memos[from_auth] = memo_q
            self.datamod.put_authdata(connection.server, cmd[1],
                                      "memos", to_memos)

    def help(self, cmdstr):
        response = "private message only. subcommands are: read, send"
        if cmdstr is not None:
            cmd = cmdstr.split(' ')
