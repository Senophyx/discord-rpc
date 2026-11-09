import os
import socket
import unittest
from unittest import mock

from discordrpc.presence import UnixPipe

unix_only = unittest.skipUnless(hasattr(socket, "AF_UNIX"), "Unix sockets not available")


@unix_only
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

    def test_falls_back_to_flatpak_socket(self):
        flatpak = "/run/user/1000/app/com.discordapp.Discord/discord-ipc-0"
        tried = []

        def connect(path):
            tried.append(path)
            if path != flatpak:
                raise FileNotFoundError(path)

        with mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": "/run/user/1000"}), \
                mock.patch.object(socket.socket, "connect", side_effect=connect):
            pipe = UnixPipe("1", False, False)

        self.assertTrue(pipe.connected)
        self.assertEqual(tried, ["/run/user/1000/discord-ipc-0", flatpak])


@unix_only
class UnixPipeCloseTests(unittest.TestCase):
    def test_close_with_peer_already_closed_does_not_raise(self):
        a, b = socket.socketpair()
        b.close()  # peer (Discord) closed first
        pipe = UnixPipe("1", False, False)
        pipe.socket = a
        pipe._close()  # must not raise


if __name__ == "__main__":
    unittest.main(verbosity=2)
