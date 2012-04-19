import irclib
import re

class ModCom(object):
    """A superclass for IRCModules that send events to each other."""

    def set_queue(self, queue):
        """Set the queue to use for outgoing events.
        
        queue - Queue.Queue object
        """
        self.com_queue = queue

    def send_to(self, mod, type="unknown", data=None, connection=None):
        """Send event to another module.

        mod - module name of recipient
        type - event type
        data - event arguments
        """
        me = self.__module__.split('.')[-1]
        self.com_queue.put((connection, irclib.Event(type, me, mod, data)))

    def dispatch(self, connection, event):
        """Find and execute a handler for event on this module."""
        handler = "on_" + event.eventtype()
        if hasattr(self, handler):
            getattr(self, handler)(connection, event)


class CommandMod(object):
    """A superclass for IRCModules that should respond to a command."""

    pattern = re.compile("^!(\S+)", re.UNICODE)
    '''Regular expression to check against each message'''
    IGNORE_PUBLIC = False
    '''When True, only respond over private query'''

    def on_privmsg(self, connection, event):
        match = self.pattern.search(event.arguments()[0])
        if match:
            self.on_command(connection, event.source(), 
                            irclib.nm_to_n(event.source()), match.groups())

    def on_pubmsg(self, connection, event):
        if not self.IGNORE_PUBLIC:
            match = self.pattern.search(event.arguments()[0])
            if match:
                self.on_command(connection, event.source(), 
                                event.target(), match.groups())

    def on_command(self, connection, commander, replyto, groups):
        """Called when self.pattern matches a message.

        connection - the corresponding irclib.ServerConnection
        commander - nickmask of the user who sent the message
        replyto - the channel where the message appeared if public, 
                  nick of commander if private
        groups - matching regex groups from pattern
        """
        connection.privmsg(replyto, "what's %s?" % groups[0])
