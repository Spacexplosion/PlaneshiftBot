#!/bin/bash
# A simple init script to keep the bot running
botuser="${0##*/}"
eval pidfile=~$botuser/bot.pid
if [[ -f $pidfile ]]; then
    pid=`cat $pidfile`
fi

case "$1" in
    start|restart)
	if [[ -z "$pid" || `kill -CONT $pid &> /dev/null` ]]; then
	    su $botuser -c "/opt/psbot/planeshiftbot.py -d -c ~$botuser > /dev/null"
	    echo "0,10,20,30,40,50 *	* * *	root	/etc/init.d/$botuser restart" > /etc/cron.d/$botuser
	fi
	;;
    stop)
	if [[ -n "$pid" ]]; then
	    kill $pid
	fi
	if [[ -f /etc/cron.d/$botuser ]]; then
	    rm /etc/cron.d/$botuser
	fi
	;;
esac
