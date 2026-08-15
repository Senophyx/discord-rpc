import json
import queue
import struct
import threading
import time
import unittest

from discordrpc.exceptions import InvalidEvent, InvalidEventType
from discordrpc.presence import _BasePipe, OP_FRAME, RPC
from discordrpc.types import Event


class FakePipe(_BasePipe):
    def __init__(self):
        super().__init__(None, False, False)
        self._in = queue.Queue()
        self._out = queue.Queue()
        self._buffer = b""
        self.connected = True

    def _connect_pipe(self):
        return True

    def _write(self, data):
        self._out.put(data)
        # Auto-respond to any request carrying a nonce so subscribe()/unsubscribe()
        # can complete without a real Discord server.
        opcode, length = struct.unpack("<ii", data[:8])
        if length == 0:
            return
        try:
            payload = json.loads(data[8:8 + length].decode("UTF-8"))
        except (ValueError, UnicodeDecodeError):
            return
        nonce = payload.get("nonce")
        if nonce:
            response = {"cmd": payload.get("cmd"), "nonce": nonce, "data": {}}
            body = json.dumps(response).encode("UTF-8")
            self._in.put(struct.pack("<ii", OP_FRAME, len(body)) + body)

    def _read_some(self, size):
        if self._buffer:
            chunk = self._buffer[:size]
            self._buffer = self._buffer[size:]
            return chunk
        while True:
            try:
                data = self._in.get(timeout=0.1)
            except queue.Empty:
                if self._reader_stop.is_set():
                    return b""
                continue
            if len(data) <= size:
                return data
            self._buffer = data[size:]
            return data[:size]

    def _close(self):
        pass


def build_frame(opcode, payload):
    data = json.dumps(payload).encode("UTF-8")
    return struct.pack("<ii", opcode, len(data)) + data


def make_rpc():
    rpc = RPC.__new__(RPC)
    rpc.app_id = "1234"
    rpc.exit_if_discord_close = False
    rpc.exit_on_disconnect = False
    rpc.try_reconnecting = True
    rpc._user_data = {"id": "1", "username": "seno"}
    rpc._app_info = None
    rpc.is_running = False
    rpc._event_callbacks = {}
    rpc._subscriptions = set()
    rpc._state_lock = threading.Lock()
    rpc.ipc = FakePipe()
    rpc.ipc._on_event = rpc._dispatch
    return rpc


class EventNormalizationTests(unittest.TestCase):
    def test_invalid_event_name_raises(self):
        rpc = make_rpc()
        with self.assertRaises(InvalidEvent):
            rpc._normalize_event("NOT_AN_EVENT")

    def test_invalid_event_type_raises(self):
        rpc = make_rpc()
        with self.assertRaises(InvalidEventType):
            rpc._normalize_event(123)

    def test_enum_and_string_are_accepted(self):
        rpc = make_rpc()
        self.assertEqual(rpc._normalize_event(Event.JOIN), "ACTIVITY_JOIN")
        self.assertEqual(rpc._normalize_event("ACTIVITY_JOIN"), "ACTIVITY_JOIN")


class DispatchTests(unittest.TestCase):
    def test_callback_receives_data(self):
        rpc = make_rpc()
        seen = []

        def cb(data):
            seen.append(data)

        with rpc._state_lock:
            rpc._event_callbacks["ACTIVITY_JOIN"] = [cb]
        rpc._dispatch("ACTIVITY_JOIN", {"secret": "x"})
        self.assertEqual(seen, [{"secret": "x"}])

    def test_callback_exception_does_not_kill_reader(self):
        rpc = make_rpc()
        out = []

        def bad(data):
            raise RuntimeError("boom")

        def good(data):
            out.append(data)

        with rpc._state_lock:
            rpc._event_callbacks["ACTIVITY_SPECTATE"] = [bad, good]
        rpc._dispatch("ACTIVITY_SPECTATE", {"n": 1})
        self.assertEqual(out, [{"n": 1}])


class ReaderLifecycleTests(unittest.TestCase):
    def test_reader_keeps_running_until_stop_and_close(self):
        rpc = make_rpc()
        rpc.ipc._start_reader()
        thread = rpc.ipc._reader_thread
        self.assertTrue(thread.is_alive())
        rpc.ipc._reader_stop.set()
        rpc.ipc._close()
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())

    def test_stop_reader_when_last_subscription_removed(self):
        rpc = make_rpc()
        rpc.ipc._start_reader()
        thread = rpc.ipc._reader_thread
        # Simulate subscriptions present, then removed.
        with rpc._state_lock:
            rpc._subscriptions.add("ACTIVITY_JOIN")
        with rpc._state_lock:
            rpc._subscriptions.discard("ACTIVITY_JOIN")
        rpc._stop_reader_if_idle()
        rpc.ipc._close()
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())

    def test_stop_reader_marks_pipe_disconnected(self):
        rpc = make_rpc()
        rpc.ipc._start_reader()
        thread = rpc.ipc._reader_thread
        with rpc._state_lock:
            rpc._subscriptions.add("ACTIVITY_JOIN")
        with rpc._state_lock:
            rpc._subscriptions.discard("ACTIVITY_JOIN")
        rpc._stop_reader_if_idle()
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        # The pipe must be marked disconnected so a later set_activity() can reconnect.
        self.assertFalse(rpc.ipc.connected)


class DuplicateHandlerTests(unittest.TestCase):
    def test_two_handlers_for_same_event_both_register(self):
        rpc = make_rpc()
        calls = []

        def handler_a(data):
            calls.append(("a", data))

        def handler_b(data):
            calls.append(("b", data))

        # Register both handlers for the same event by calling subscribe() twice,
        # simulating stacked decorators: @rpc.on(Event.JOIN) twice.
        self.assertTrue(rpc.subscribe(Event.JOIN))
        self.assertTrue(rpc.subscribe(Event.JOIN))

        with rpc._state_lock:
            rpc._event_callbacks.setdefault("ACTIVITY_JOIN", []).append(handler_a)
            rpc._event_callbacks.setdefault("ACTIVITY_JOIN", []).append(handler_b)

        rpc._dispatch("ACTIVITY_JOIN", {"x": 1})
        self.assertEqual(calls, [("a", {"x": 1}), ("b", {"x": 1})])

    def test_subscribe_idempotent_returns_true(self):
        rpc = make_rpc()
        self.assertTrue(rpc.subscribe(Event.JOIN))
        # Second subscribe for the same event should be a no-op but still True,
        # so @rpc.on() can stack another handler.
        self.assertTrue(rpc.subscribe(Event.JOIN))


class ReconnectTests(unittest.TestCase):
    def test_subscribe_reconnects_when_pipe_disconnected(self):
        rpc = make_rpc()
        rpc.ipc.connected = False
        rpc._setup = lambda: setattr(rpc.ipc, "connected", True)
        self.assertTrue(rpc.subscribe(Event.JOIN))
        self.assertTrue(rpc.ipc.connected)

    def test_unsubscribe_reconnects_when_pipe_disconnected(self):
        rpc = make_rpc()
        with rpc._state_lock:
            rpc._subscriptions.add("ACTIVITY_JOIN")
            rpc._event_callbacks["ACTIVITY_JOIN"] = []
        rpc.ipc.connected = False
        rpc._setup = lambda: setattr(rpc.ipc, "connected", True)
        self.assertTrue(rpc.unsubscribe(Event.JOIN))
        # After the last unsubscribe the reader stops idle and the pipe is
        # marked disconnected again, which is expected (reconnect happens on
        # the next subscribe/set_activity).
        self.assertFalse(rpc.ipc.connected)

    def test_disconnect_clears_state_when_pipe_already_disconnected(self):
        rpc = make_rpc()
        rpc.is_running = True
        with rpc._state_lock:
            rpc._subscriptions.add("ACTIVITY_JOIN")
            rpc._event_callbacks["ACTIVITY_JOIN"] = [lambda d: None]
        rpc.ipc.connected = False
        rpc.disconnect()
        self.assertFalse(rpc.is_running)
        self.assertFalse(rpc._subscriptions)
        self.assertFalse(rpc._event_callbacks)

    def test_run_exits_after_heartbeat_failure(self):
        rpc = make_rpc()
        calls = []

        def fail_send(payload, op=1):
            raise RuntimeError("boom")

        def spy_disconnect():
            calls.append("disconnect")
            RPC.disconnect(rpc)

        rpc.ipc._send = fail_send
        rpc.disconnect = spy_disconnect

        thread = threading.Thread(
            target=rpc.run, kwargs={"update_every": 0.05, "ping_every": 0.1}, daemon=True
        )
        thread.start()
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertIn("disconnect", calls)


if __name__ == "__main__":
    unittest.main(verbosity=2)
