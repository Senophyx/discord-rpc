import json
import struct
import sys
import threading
import time
import unittest
import uuid

from discordrpc.presence import OP_FRAME, OP_HANDSHAKE, WindowsPipe

windows_only = unittest.skipUnless(sys.platform == "win32", "Windows named pipes only")


def frame(op, payload):
    data = json.dumps(payload).encode("UTF-8")
    return struct.pack("<ii", op, len(data)) + data


@windows_only
class WindowsNamedPipeTests(unittest.TestCase):
    """Real named pipe with a fake Discord server on the other end."""

    def setUp(self):
        from multiprocessing.connection import Listener

        self.listener = Listener(r"\\.\pipe\discord-ipc-0", family="AF_PIPE")
        self.accepted = threading.Event()
        threading.Thread(target=self._serve, daemon=True).start()

    def tearDown(self):
        self.listener.close()

    def _serve(self):
        self.conn = self.listener.accept()
        self.accepted.set()
        try:
            while True:
                msg = self.conn.recv_bytes()
                op, length = struct.unpack("<ii", msg[:8])
                payload = json.loads(msg[8:8 + length]) if length else {}
                if op == OP_HANDSHAKE:
                    user = {"id": "1", "username": "ci"}
                    self.conn.send_bytes(frame(OP_FRAME, {"cmd": "DISPATCH", "evt": "READY", "data": {"user": user}}))
                elif payload.get("nonce"):
                    self.conn.send_bytes(frame(OP_FRAME, {"cmd": payload["cmd"], "nonce": payload["nonce"], "data": {}}))
        except (EOFError, OSError):
            pass

    def _connected_pipe(self):
        pipe = WindowsPipe("1", True, False)
        self.assertEqual(pipe.handshake()["username"], "ci")
        self.addCleanup(pipe._close)
        self.addCleanup(pipe._reader_stop.set)
        return pipe

    def _request(self, pipe):
        payload = {"cmd": "SET_ACTIVITY", "args": {}, "nonce": str(uuid.uuid4())}
        return pipe._request(payload, timeout=5)["ok"]

    def test_second_request_is_not_blocked_by_reader(self):
        pipe = self._connected_pipe()
        results = []
        worker = threading.Thread(target=lambda: results.extend(self._request(pipe) for _ in range(2)), daemon=True)
        worker.start()
        worker.join(15)
        self.assertFalse(worker.is_alive(), "write blocked while the reader waited for data")
        self.assertEqual(results, [True, True])

    def test_server_close_marks_closed_by_discord(self):
        pipe = self._connected_pipe()
        self.assertTrue(self._request(pipe))  # starts the reader
        self.accepted.wait(5)
        self.conn.close()
        deadline = time.time() + 5
        while pipe.connected and time.time() < deadline:
            time.sleep(0.05)
        self.assertFalse(pipe.connected)
        self.assertTrue(pipe.closed_by_discord)


if __name__ == "__main__":
    unittest.main(verbosity=2)
