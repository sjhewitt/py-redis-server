"""
Provides the codecs for parsing/sending messages.

See http://redis.io/topics/protocol for more info.
"""

import redis.connection


class FakeBuffer(object):
    def __init__(self, lines):
        self.lines = lines
        self.pos = 0

    def readline(self, length=None):
        """Override; read from memory instead of a socket."""
        self.pos += 1
        return self.lines[self.pos - 1]

    read = readline


class InputParser(redis.connection.PythonParser):
    """Subclasses the client PythonParser to spoof the internals of reading off a socket."""
    def __init__(self, lines):
        super(InputParser, self).__init__(65536)
        self._buffer = FakeBuffer(lines)


class Response(object):
    """Writes data to callback as dictated by the Redis Protocol."""
    def __init__(self, write_callback):
        self.callback = write_callback
        self.dirty = False

    def encode(self, value):
        """Respond with data."""
        if isinstance(value, (list, tuple)):
            self._write('*%d\r\n' % len(value))
            for v in value:
                self._bulk(v)
        elif isinstance(value, (int, long)):
            self._write(':%d\r\n' % value)
        elif isinstance(value, bool):
            self._write(':%d\r\n' % (1 if value else 0))
        else:
            self._bulk(v)

    def status(self, msg="OK"):
        """Send a status."""
        self._write("+%s\r\n" % msg)

    def error(self, msg):
        """Send an error."""
        data = ['-', unicode(msg), "\r\n"]
        self._write("".join(data))

    def _bulk(self, value):
        """Send part of a multiline reply."""
        data = ["$", str(len(value)), "\r\n", unicode(value), "\r\n"]
        self._write("".join(data))

    def _write(self, data):
        if not self.dirty:
            self.dirty = True
        self.callback(data)
