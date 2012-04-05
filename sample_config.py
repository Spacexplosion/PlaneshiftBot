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
