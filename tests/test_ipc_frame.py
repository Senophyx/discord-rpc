import json
import struct
import threading
import time
import unittest

from discordrpc.presence import _BasePipe, OP_CLOSE


class FakePipe(_BasePipe):
    def __init__(self, chunks):
        super().__init__(None, False, False)
        self.chunks = list(chunks)
        self.connected = True

    def _connect_pipe(self):
        return True

    def _write(self, data):
        pass

    def _close(self):
        pass

    def _read_some(self, size):
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        if len(chunk) > size:
            self.chunks.insert(0, chunk[size:])
            chunk = chunk[:size]
        return chunk


def frame_bytes(opcode, payload):
    data = json.dumps(payload).encode("UTF-8")
    return struct.pack("<ii", opcode, len(data)) + data


class ReadFrameTests(unittest.TestCase):
    def test_frame_in_one_read(self):
        payload = {"cmd": "SET_ACTIVITY", "nonce": "abc"}
        pipe = FakePipe([frame_bytes(1, payload)])
        opcode, decoded = pipe._read_frame()
        self.assertEqual(opcode, 1)
        self.assertEqual(decoded, payload)

    def test_header_split_across_reads(self):
        payload = {"cmd": "PING"}
        data = frame_bytes(4, payload)
        pipe = FakePipe([data[:3], data[3:8], data[8:]])
        opcode, decoded = pipe._read_frame()
        self.assertEqual(opcode, 4)
        self.assertEqual(decoded, payload)

    def test_payload_split_across_reads(self):
        payload = {"cmd": "DISPATCH", "evt": "READY", "data": {"x": "y"}}
        data = frame_bytes(1, payload)
        pipe = FakePipe([data[:8], data[8:10], data[10:14], data[14:]])
        opcode, decoded = pipe._read_frame()
        self.assertEqual(opcode, 1)
        self.assertEqual(decoded, payload)

    def test_empty_payload(self):
        pipe = FakePipe([struct.pack("<ii", 2, 0)])
        opcode, decoded = pipe._read_frame()
        self.assertEqual(opcode, 2)
        self.assertIsNone(decoded)

    def test_truncated_header_raises(self):
        pipe = FakePipe([b"\x01\x00"])
        with self.assertRaises(OSError):
            pipe._read_frame()

    def test_truncated_payload_raises(self):
        payload = {"cmd": "DISPATCH"}
        data = frame_bytes(1, payload)
        pipe = FakePipe([data[:8], data[8:10]])
        with self.assertRaises(OSError):
            pipe._read_frame()

    def test_invalid_json_raises(self):
        pipe = FakePipe([struct.pack("<ii", 1, 5) + b"hello"])
        with self.assertRaises(ValueError):
            pipe._read_frame()

    def test_negative_length_raises(self):
        pipe = FakePipe([struct.pack("<ii", 1, -4)])
        with self.assertRaises(ValueError):
            pipe._read_frame()

    def test_oversized_length_raises(self):
        pipe = FakePipe([struct.pack("<ii", 1, 20 * 1024 * 1024)])
        with self.assertRaises(ValueError):
            pipe._read_frame()


class ReaderDisconnectTests(unittest.TestCase):
    """Reader must mark the pipe disconnected when the peer closes."""

    def _pipe_with(self, chunks):
        pipe = FakePipe(chunks)
        pipe.connected = True
        return pipe

    def test_eof_marks_pipe_disconnected(self):
        # Peer closed the socket: _read_some returns b"" -> OSError in _read_exact.
        pipe = self._pipe_with([])
        pipe._start_reader()
        time.sleep(0.3)
        self.assertFalse(pipe.connected)
        pipe._reader_stop.set()
        pipe._close()

    def test_op_close_empty_payload_marks_pipe_disconnected(self):
        # OP_CLOSE with length 0 (no payload) must still mark disconnected.
        pipe = self._pipe_with([struct.pack("<ii", OP_CLOSE, 0)])
        pipe._start_reader()
        time.sleep(0.3)
        self.assertFalse(pipe.connected)
        pipe._reader_stop.set()
        pipe._close()

    def test_reader_stops_after_disconnect(self):
        pipe = self._pipe_with([struct.pack("<ii", OP_CLOSE, 0)])
        pipe._start_reader()
        thread = pipe._reader_thread
        time.sleep(0.3)
        thread.join(timeout=1)
        self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main(verbosity=2)
