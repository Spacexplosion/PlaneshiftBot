SERVER_LIST = [ 
    {"server" : "irc.quakenet.org", # host (required)
     "port" : 6667,                 # IP port (required)
     "nickname" : "planeshiftbot"}, # bot's nick (required)
    # password : IRC server password
    # username : whois username
    # ircname : whois real name
    # localaddress : bind connection to local IP address
    # localport : bind connection to local port
    # ssl : connect via ssl
    # ipv6 : use IPv6 addresses
]
MODULES = [ "rawlog"
          ]

## seconds to wait to reconnect
#RECONNECT_WAIT = 60 # (default 60, negative turns off)
