import socket
import unittest
from unittest import mock

from discordrpc.presence import UnixPipe


class UnixPipeConnectTests(unittest.TestCase):
    def test_connection_refused_falls_back_cleanly(self):
        # Discord socket exists but refuses the connection (e.g. shutting down).
        with mock.patch.object(socket.socket, "connect", side_effect=ConnectionRefusedError("refused")):
            pipe = UnixPipe("1", False, False)
            self.assertFalse(pipe._connect_pipe())

    def test_permission_error_falls_back_cleanly(self):
        with mock.patch.object(socket.socket, "connect", side_effect=PermissionError("denied")):
            pipe = UnixPipe("1", False, False)
            self.assertFalse(pipe._connect_pipe())


if __name__ == "__main__":
    unittest.main(verbosity=2)
