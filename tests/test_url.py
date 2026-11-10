import unittest

from discordrpc import button
from discordrpc.exceptions import ActivityError, ButtonError, InvalidURL
from discordrpc.utils import required_url, valid_url


class ValidUrlTests(unittest.TestCase):
    def test_accepts_http_and_https(self):
        self.assertEqual(valid_url("http://example.com"), "http://example.com")
        self.assertEqual(valid_url("https://example.com/path"), "https://example.com/path")

    def test_accepts_query_and_fragment(self):
        self.assertEqual(valid_url("https://example.com?a=1#frag"), "https://example.com?a=1#frag")

    def test_none_is_optional(self):
        self.assertIsNone(valid_url(None))

    def test_rejects_unsupported_schemes(self):
        for url in ("ftp://example.com", "javascript:alert(1)", "file:///tmp/x"):
            with self.assertRaises(InvalidURL):
                valid_url(url)

    def test_rejects_bare_scheme_without_host(self):
        for url in ("http://", "https://", "http://?", "https://#frag"):
            with self.assertRaises(InvalidURL):
                valid_url(url)

    def test_rejects_empty_string(self):
        with self.assertRaises(InvalidURL):
            valid_url("")

    def test_rejects_non_string(self):
        with self.assertRaises(InvalidURL):
            valid_url(12345)


class RequiredUrlTests(unittest.TestCase):
    def test_none_rejected_when_required(self):
        with self.assertRaises(InvalidURL):
            required_url(None)

    def test_empty_rejected_when_required(self):
        with self.assertRaises(InvalidURL):
            required_url("")


class ButtonTests(unittest.TestCase):
    def test_valid_button(self):
        self.assertEqual(
            button("Repository", "https://github.com/Senophyx/discord-rpc"),
            {"label": "Repository", "url": "https://github.com/Senophyx/discord-rpc"},
        )

    def test_none_url_rejected(self):
        with self.assertRaises(InvalidURL):
            button("Repository", None)

    def test_empty_url_rejected(self):
        with self.assertRaises(InvalidURL):
            button("Repository", "")

    def test_unsupported_scheme_rejected(self):
        with self.assertRaises(InvalidURL):
            button("Repository", "ftp://example.com")


class SetActivityButtonsTests(unittest.TestCase):
    def setUp(self):
        import queue
        import threading

        from discordrpc.presence import _BasePipe, RPC

        class FakePipe(_BasePipe):
            def __init__(self):
                super().__init__(None, False, False)
                self.connected = True
                self.captured = None

            def _connect_pipe(self):
                return True

            def _write(self, data):
                pass

            def _read_some(self, size):
                return b""

            def _close(self):
                pass

            def _request(self, payload, op=1, timeout=1.0):
                self.captured = payload
                return {"ok": True, "cmd": payload.get("cmd"), "nonce": payload.get("nonce"), "data": {}}

        self.pipe_cls = FakePipe

    def make_rpc(self):
        import threading

        from discordrpc.presence import RPC

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
        rpc.ipc = self.pipe_cls()
        rpc.ipc._on_event = rpc._dispatch
        return rpc

    def test_buttons_with_valid_url_accepted(self):
        rpc = self.make_rpc()
        res = rpc.set_activity(buttons=[{"label": "A", "url": "https://valid.com"}])
        self.assertTrue(res)
        buttons = rpc.ipc.captured["args"]["activity"]["buttons"]
        self.assertEqual(buttons, [{"label": "A", "url": "https://valid.com"}])

    def test_buttons_with_invalid_url_rejected(self):
        rpc = self.make_rpc()
        with self.assertRaises(InvalidURL):
            rpc.set_activity(buttons=[{"label": "A", "url": "not-a-url"}])

    def test_buttons_with_empty_url_rejected(self):
        rpc = self.make_rpc()
        with self.assertRaises(InvalidURL):
            rpc.set_activity(buttons=[{"label": "A", "url": ""}])

    def test_state_and_details_length_limits(self):
        rpc = self.make_rpc()
        self.assertTrue(rpc.set_activity(state="ab", details="x" * 128))
        for kwargs in ({"state": "a"}, {"details": "x" * 129}):
            with self.assertRaises(ActivityError):
                rpc.set_activity(**kwargs)

    def test_buttons_with_secrets_rejected(self):
        rpc = self.make_rpc()
        with self.assertRaises(ButtonError):
            rpc.set_activity(buttons=[button("A", "https://valid.com")], join_secret="s")

    def test_button_label_required_and_limited(self):
        rpc = self.make_rpc()
        self.assertTrue(rpc.set_activity(buttons=[button("x" * 32, "https://valid.com")]))
        for item in ("https://valid.com", {"url": "https://valid.com"}, button("x" * 33, "https://valid.com")):
            with self.assertRaises(ButtonError):
                rpc.set_activity(buttons=[item])

    def test_button_url_length_limited(self):
        rpc = self.make_rpc()
        with self.assertRaises(ButtonError):
            rpc.set_activity(buttons=[button("A", "https://valid.com/" + "x" * 500)])

    def test_status_type_accepts_int(self):
        rpc = self.make_rpc()
        self.assertTrue(rpc.set_activity(state="ab", status_type=1))
        self.assertEqual(rpc.ipc.captured["args"]["activity"]["status_display_type"], 1)

    def test_buttons_with_none_url_rejected(self):
        rpc = self.make_rpc()
        with self.assertRaises(InvalidURL):
            rpc.set_activity(buttons=[{"label": "A", "url": None}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
