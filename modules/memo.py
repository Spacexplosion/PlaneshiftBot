import logging
import re
import irc
import config
import modules

class MemoMod(modules.CommandMod):
    """Send offline memos to authenticated users.

    Depends on authdata."""

    patternstr = "memo\s+(.+)"
    IGNORE_PUBLIC = True

    JOIN_DELAY = 3

    def __init__(self):
        modules.IRCModule.__init__(self)
        self.log = logging.getLogger("irc.memo")
        self.__pattern = re.compile("^"+self.patternstr, re.UNICODE)

    def on_load(self, bot):
        super(IRCModule, self).on_load(bot)
        if "authdata" not in bot.modules:
            raise RuntimeError("Memo service requires authdata module")
        self.datamod = bot.modules["authdata"]
        if hasattr(config, "MEMO_JOIN_DELAY"):
            MemoMod.JOIN_DELAY = config.MEMO_JOIN_DELAY

    def on_join(self, connection, event):
        def join_notice():
            memos = self.datamod.get_userdata(connection.server, nick, "memos")
            if memos is not None:
                connection.notice(nick, "You have unread memos; msg me \"memo read\"")
        nick = event.source.nick
        if MemoMod.JOIN_DELAY > 0:
            self.bot.irc.execute_delayed(MemoMod.JOIN_DELAY, join_notice)

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
                for (sender, msgs) in memos.iteritems():
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
        response = "private message only. subcommands are: on, off, read, send"
        if cmdstr is not None:
            cmd = cmdstr.split(' ')
            if cmd[0] == "on" or cmd[0] == "off":
                response = "memo [on|off] : controls whether others can send you memos"
            elif cmd[0] == "read":
                response = "memo read : view all unread memos"
            elif cmd[0] == "send":
                response = "memo send <username> <message> : write a memo to the specified authentication service username"
        return response


IRCModule = MemoMod
