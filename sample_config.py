SERVER_LIST = [ 
    {"server" : "irc.quakenet.org", # host (required)
     "port" : 6667,                 # IP port (required)
     "nickname" : "planeshiftbot",  # bot's nick (required)
    # password : IRC server password
    # username : whois username
    # ircname : whois real name
    # localaddress : bind connection to local IP address
    # localport : bind connection to local port
    # ssl : connect via ssl
    # ipv6 : use IPv6 addresses
    },
]
MODULES = [ 
    "channels",
    "help",
    "info",
    "seen",
]

## Set the frequency in seconds of pinging the server
#KEEP_ALIVE_FREQ = 30 # (default 30, <=0 turns off)

## Set the number of seconds to wait for ping response
#PING_TIMEOUT = 10

## Set the number of seconds to wait to reconnect
#RECONNECT_WAIT = 60 # (default 60, negative turns off)

## Set the amount of log output
LOGLEVEL = "INFO" # DEBUG, INFO, WARNING, ERROR

### Module configurations ###

## channels ##

## Join these channels : channel_name, [optional list of servers]
AUTOJOIN_CHANNELS = [ 
    "#planeshiftbot-testing", # "#channel",
# ("#channel", "password"),
# ("#channel", ["server1", "server2", ...]),
# ("#channel", ["server1", "server2", ...], ["pass1", "pass2", ...]),
]

## Set the number of seconds to wait to rejoin after kicked
#KICK_REJOIN_WAIT -1 # (default off)

## Join any channel the bot gets invited to?
# JOIN_INVITES = False

## Format file name for logs (use standard Python formatting)
CHAN_LOG_FILENAME = "%(name)s@%(server)s.log" # keywords - name, server
## Format log timestamps
CHAN_LOG_TIME_FORMAT = "%H:%M:%S" # use standard Python date format
## Format messages in channels
#CHAN_LOG_MSG_FORMAT = "<%(nick)s> %(message)s" # keywords - nick, nickmask, server

## info ##
INFO_STRING = "I'm a PlaneshiftBot!"
