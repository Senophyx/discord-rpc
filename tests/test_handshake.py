import json
import struct
import unittest

from discordrpc.exceptions import InvalidID, RPCException
from discordrpc.presence import _BasePipe, OP_CLOSE, OP_FRAME, OP_HANDSHAKE


def build_frame(opcode, payload):
    data = json.dumps(payload).encode("UTF-8")
    return struct.pack("<ii", opcode, len(data)) + data


class FakePipe(_BasePipe):
    def __init__(self):
        super().__init__(None, False, False)
        self.responses = []
        self.sent = []
        self.connected = True

    def _connect_pipe(self):
        return True

    def _write(self, data):
        self.sent.append(data)

    def _read_some(self, size):
        if not self.responses:
            return b""
        data = self.responses.pop(0)
        if len(data) > size:
            self.responses.insert(0, data[size:])
            data = data[:size]
        return data

    def _close(self):
        pass


class HandshakeTests(unittest.TestCase):
    def _pipe_with(self, frames):
        pipe = FakePipe()
        pipe.responses = [build_frame(*frame) for frame in frames]
        return pipe

    def test_ready_event_succeeds(self):
        pipe = self._pipe_with([
            (OP_FRAME, {"cmd": "DISPATCH", "evt": "READY", "data": {"user": {"id": "1", "username": "seno"}}})
        ])
        user = pipe.handshake()
        self.assertEqual(user.get("username"), "seno")
        # Handshake frame must be sent with opcode 0 and no nonce.
        raw = pipe.sent[0]
        opcode, length = struct.unpack("<ii", raw[:8])
        self.assertEqual(opcode, OP_HANDSHAKE)
        payload = json.loads(raw[8:8 + length])
        self.assertEqual(payload, {"v": 1, "client_id": None})
        self.assertNotIn("nonce", payload)

    def test_error_with_invalid_client_id_raises_invalid_id(self):
        pipe = self._pipe_with([
            (OP_FRAME, {"cmd": "DISPATCH", "evt": "ERROR", "data": {"code": 4000, "message": "Invalid Client ID"}})
        ])
        with self.assertRaises(InvalidID):
            pipe.handshake()

    def test_close_with_invalid_client_id_raises_invalid_id(self):
        # Real Discord answers a bad client ID with OP_CLOSE, not an ERROR frame
        pipe = self._pipe_with([
            (OP_CLOSE, {"code": 4000, "message": "Invalid Client ID"})
        ])
        with self.assertRaises(InvalidID):
            pipe.handshake()
        self.assertFalse(pipe.connected)

    def test_unknown_error_raises_rpc_exception(self):
        pipe = self._pipe_with([
            (OP_FRAME, {"cmd": "DISPATCH", "evt": "ERROR", "data": {"code": 1002, "message": "Something else"}})
        ])
        with self.assertRaises(RPCException):
            pipe.handshake()

    def test_close_before_ready_raises(self):
        pipe = self._pipe_with([
            (OP_CLOSE, {})
        ])
        with self.assertRaises(RPCException):
            pipe.handshake()

    def test_missing_ready_raises(self):
        pipe = self._pipe_with([
            (OP_FRAME, {"cmd": "DISPATCH", "evt": "SOMETHING_ELSE", "data": {}})
        ])
        with self.assertRaises(RPCException):
            pipe.handshake()


if __name__ == "__main__":
    unittest.main(verbosity=2)
