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
]

## Set the number of seconds to wait to reconnect
#RECONNECT_WAIT = 60 # (default 60, negative turns off)

## Set the amount of log output
LOGLEVEL = "INFO" # DEBUG, INFO, WARNING, ERROR

### Module configurations ###

## channels ##

## Join these channels : channel_name, [optional list of servers]
AUTOJOIN_CHANNELS = [ 
    "#planeshiftbot-testing",
# example: ("#quakelive", ["irc.quakenet.org"]),
]

## Format file name for logs (use standard Python formatting)
CHAN_LOG_FILENAME = "%(name)s@%(server)s.log" # keywords - name, server
## Format log timestamps
CHAN_LOG_TIME_FORMAT = "%H:%M:%S" # use standard Python date format
## Format messages in channels
#CHAN_LOG_MSG_FORMAT = "<%(nick)s> %(message)s" # keywords - nick, nickmask, server
