import sys
import os
import socket
import json
import struct
import uuid
import threading
import queue
from typing import Optional
from .exceptions import (
    RPCException, InvalidID, DiscordNotOpened,
    ButtonError, InvalidActivityType, ActivityTypeDisabled,
    InvalidEvent, InvalidEventType,
)
from .types import Activity, StatusDisplay, User, Application, Asset, AssetManager, Event
from .utils import remove_none, get_app_info, get_assets, valid_url, required_url
from functools import cached_property
import logging
import time

OP_HANDSHAKE = 0
OP_FRAME = 1
OP_CLOSE = 2
OP_PING = 3
OP_PONG = 4

### Logger ###
log = logging.getLogger("Discord RPC")
log.setLevel(logging.INFO)

# Setup specific handler for Discord RPC logger
_log_handler = logging.StreamHandler()
_log_formatter = logging.Formatter("%(asctime)s :: [%(levelname)s @ %(filename)s.%(funcName)s:%(lineno)d] :: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
_log_handler.setFormatter(_log_formatter)
log.addHandler(_log_handler)

class RPC:
    def __init__(self, app_id:int, debug:bool=False, output:bool=True, exit_if_discord_close:bool=True, exit_on_disconnect:bool=True):
        self.app_id = str(app_id)
        self.exit_if_discord_close = exit_if_discord_close
        self.exit_on_disconnect = exit_on_disconnect

        self.try_reconnecting = True

        self._user_data = None
        self._app_info = None

        if debug:
            log.setLevel(logging.DEBUG)
        
        if not output:
            log.disabled = True

        self.is_running = False
        self._event_callbacks = {}
        self._subscriptions = set()
        self._state_lock = threading.Lock()
        self._setup()

    def _setup(self):
        if sys.platform == "win32":
            self.ipc = WindowsPipe(self.app_id, self.exit_if_discord_close, self.exit_on_disconnect)
        else:
            self.ipc = UnixPipe(self.app_id, self.exit_if_discord_close, self.exit_on_disconnect)
            
        if not self.ipc.connected: return
        self._user_data = self.ipc.handshake()
        self.ipc._on_event = self._dispatch

    @property
    def connected(self): return self.ipc.connected

    @cached_property
    def User(self):
        return User(self._user_data)

    @cached_property
    def App(self):
        if not self._app_info:
            self._app_info = get_app_info(self.app_id)
        return Application(self._app_info)

    @cached_property
    def assets(self):
        return AssetManager(self.app_id, get_assets(self.app_id))

    def set_activity(
            self, name: str = None,
            state: str = None, details: str = None, act_type: Activity = Activity.Playing, status_type: StatusDisplay = StatusDisplay.Name,
            large_image: str = None, large_text: str = None, large_url: str = None,
            small_image: str = None, small_text: str = None, small_url: str = None,
            state_url: str = None, details_url: str = None,
            ts_start: int = None, ts_end: int = None,
            party_id: str = None, party_size: list = None,
            join_secret: str = None, spectate_secret: str = None,
            match_secret: str = None, buttons: list = None,
            clear = False
        ) -> Optional[bool]:
        """
        Set or update the Rich Presence.
        
        Images (`large_image`, `small_image`) can be an uploaded asset key from your Discord Developer Portal, 
        or an external direct URL (e.g., https://example.com/image.gif). Supports PNG, JPEG, WebP, GIF, and AVIF.
        """

        if type(act_type) != Activity:
            raise InvalidActivityType(type(act_type))

        # https://github.com/Senophyx/discord-rpc/issues/28#issuecomment-2301287350
        if act_type in [Activity.Streaming, Activity.Custom]:
            raise ActivityTypeDisabled()

        if buttons and len(buttons) > 2:
            raise ButtonError("Max 2 buttons allowed")

        # Validate button URLs so invalid URLs are caught client-side instead of
        # being silently rejected by Discord (or missing from the presence).
        if buttons:
            buttons = [
                {
                    "label": item.get("label") if isinstance(item, dict) else None,
                    "url": required_url(item.get("url") if isinstance(item, dict) else item),
                }
                for item in buttons
            ]

        large_image = large_image.name if isinstance(large_image, Asset) else large_image
        small_image = small_image.name if isinstance(small_image, Asset) else small_image

        activity = None
        if not clear:
            if type(party_id) == int:
                party_id = str(party_id)

            act = {
                "name": name,
                "state": state,
                "details": details,
                "type": act_type.value,
                "status_display_type": status_type.value,
                "state_url": valid_url(state_url),
                "details_url": valid_url(details_url),
                "timestamps": {
                    "start": ts_start,
                    "end": ts_end
                },
                "assets": {
                    "large_image": large_image,
                    "large_text": large_text,
                    "large_url": valid_url(large_url),
                    "small_image": small_image,
                    "small_text": small_text,
                    "small_url": valid_url(small_url)
                },
                "party": {
                    "id": party_id,
                    "size": party_size
                },
                "secrets": {
                    "join": join_secret,
                    "spectate": spectate_secret,
                    "match": match_secret
                },
                "buttons": buttons
            }
            activity = remove_none(act)

        payload = {
            'cmd': 'SET_ACTIVITY',
            'args': {
                'pid': os.getpid(),
                'activity': activity
            },
            'nonce': str(uuid.uuid4())
        }

        if not self.ipc.connected and self.try_reconnecting:
            self._setup()

        if not self.ipc.connected:
            return

        try:
            res = self.ipc._request(payload)
            if not res.get("ok"):
                self.is_running = False
                log.error("Failed to set RPC: %s", res.get("error"))
                return False
            
            self.is_running = True
            log.info("RPC set")
            return True
        except Exception:
            log.exception("Failed to set RPC")
            self.disconnect()
            return False


    def clear(self):
        self.set_activity(clear=True)

    def disconnect(self):
        self.is_running = False
        with self._state_lock:
            self._subscriptions.clear()
            self._event_callbacks.clear()

        if not self.ipc.connected:
            return

        self.ipc.disconnect()

    def _normalize_event(self, event):
        if isinstance(event, Event):
            return event.value
        if isinstance(event, str):
            values = {e.value for e in Event}
            if event in values:
                return event
            raise InvalidEvent(event)
        raise InvalidEventType(type(event).__name__)

    def subscribe(self, event) -> Optional[bool]:
        event = self._normalize_event(event)

        if not self.ipc.connected and self.try_reconnecting:
            self._setup()

        if not self.ipc.connected:
            return

        with self._state_lock:
            if event in self._subscriptions:
                log.debug(f"Event {event} already subscribed")
                return True

        payload = {"cmd": "SUBSCRIBE", "args": {}, "evt": event, "nonce": str(uuid.uuid4())}
        res = self.ipc._request(payload)
        if not res.get("ok"):
            log.error("Failed to subscribe to %s: %s", event, res.get("error"))
            return False

        with self._state_lock:
            self._subscriptions.add(event)
            self._event_callbacks.setdefault(event, [])
        log.info(f"Subscribed to {event}")
        return True

    def unsubscribe(self, event) -> Optional[bool]:
        event = self._normalize_event(event)

        if not self.ipc.connected and self.try_reconnecting:
            self._setup()

        if not self.ipc.connected:
            return

        with self._state_lock:
            if event not in self._subscriptions:
                log.error(f"Event {event} not subscribed")
                return False

        payload = {"cmd": "UNSUBSCRIBE", "args": {}, "evt": event, "nonce": str(uuid.uuid4())}
        res = self.ipc._request(payload)
        if not res.get("ok"):
            log.error("Failed to unsubscribe from %s: %s", event, res.get("error"))
            return False

        with self._state_lock:
            self._subscriptions.discard(event)
            self._event_callbacks.pop(event, [])
        log.info(f"Unsubscribed from {event}")
        self._stop_reader_if_idle()
        return True

    def on(self, event: Event):
        if type(event) != Event:
            raise InvalidEventType(type(event).__name__)

        def decorator(callback):
            result = self.subscribe(event)
            if not result:
                raise RPCException(f"Failed to subscribe to {event.value}")
            with self._state_lock:
                self._event_callbacks.setdefault(event.value, []).append(callback)
            return callback

        return decorator

    def _stop_reader_if_idle(self):
        with self._state_lock:
            idle = not self._subscriptions
        if idle and self.ipc._reader_thread and self.ipc._reader_thread.is_alive():
            self.ipc._reader_stop.set()
            try:
                self.ipc._close()
            except Exception:
                pass
            self.ipc.connected = False

    def _dispatch(self, evt: str, data: dict):
        with self._state_lock:
            callbacks = list(self._event_callbacks.get(evt, []))
        for callback in callbacks:
            try:
                callback(data)
            except Exception:
                log.exception("Error in '%s' event callback", evt)

    def run(self, update_every:int=1, ping_every:int=15):
        try:
            last_ping = time.time()
            while True:
                time.sleep(update_every)
                
                # Send a PING heartbeat every `ping_every` seconds to keep the socket alive
                if self.ipc.connected and (time.time() - last_ping >= ping_every):
                    payload = {"v": 1, "client_id": self.app_id}
                    try:
                        self.ipc._send(payload, OP_PING)
                        last_ping = time.time()
                    except Exception as e:
                        log.error(f"Heartbeat PING failed: {e}")
                        self.disconnect()
                        break
        except KeyboardInterrupt:
            self.disconnect()


class _BasePipe:
    def __init__(self, app_id, exit_if_discord_close, exit_on_disconnect):
        self.app_id = app_id
        self.exit_if_discord_close = exit_if_discord_close
        self.exit_on_disconnect = exit_on_disconnect
        self.connected = self._connect_pipe()
        self._write_lock = threading.Lock()
        self._pending_requests = {}
        self._pending_lock = threading.Lock()
        self._reader_thread = None
        self._reader_stop = threading.Event()

    def _connect_pipe(self):
        """Override in subclass to establish the pipe connection. Returns True on success."""
        raise NotImplementedError

    def _send(self, payload, op: int = OP_FRAME):
        log.debug(payload)

        payload = json.dumps(payload).encode('UTF-8')
        payload = struct.pack('<ii', op, len(payload)) + payload

        with self._write_lock:
            self._write(payload)

    def _register_request(self, nonce):
        q = queue.Queue(maxsize=1)
        with self._pending_lock:
            self._pending_requests[nonce] = q
        return q

    def _unregister_request(self, nonce):
        with self._pending_lock:
            self._pending_requests.pop(nonce, None)

    def _request(self, payload: dict, op: int = OP_FRAME, timeout: float = 10.0) -> dict:
        nonce = payload.get("nonce")
        if not nonce:
            raise ValueError("RPC request payload must include a nonce")

        wait_queue = self._register_request(nonce)
        self._start_reader()
        try:
            self._send(payload, op)
            try:
                res = wait_queue.get(timeout=timeout)
            except queue.Empty:
                return {"ok": False, "error": "RPC request timed out", "response": None}
        finally:
            self._unregister_request(nonce)

        opcode, payload_res = res
        if opcode != OP_FRAME:
            return {"ok": False, "error": f"Unexpected opcode {opcode}", "response": payload_res}
        if not isinstance(payload_res, dict):
            return {"ok": False, "error": "Expected JSON object response", "response": payload_res}
        if payload_res.get("evt") == "ERROR":
            data = payload_res.get("data") or {}
            return {
                "ok": False,
                "code": data.get("code"),
                "error": data.get("message") or payload_res.get("message"),
                "response": payload_res,
            }
        if payload_res.get("nonce") != nonce:
            return {"ok": False, "error": "RPC response nonce mismatch", "response": payload_res}
        return {"ok": True, **payload_res}

    def _start_reader(self):
        if self._reader_thread and self._reader_thread.is_alive():
            return
        self._reader_stop.clear()
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def _reader_loop(self):
        while self.connected and not self._reader_stop.is_set():
            try:
                frame = self._read_frame()
            except Exception as e:
                log.debug(f"IPC reader stopping: {e}")
                self.connected = False
                break
            if frame is None:
                continue
            opcode, payload = frame
            if opcode == OP_CLOSE:
                log.debug("Received OP_CLOSE from Discord")
                self.connected = False
                break
            if payload is None:
                continue
            if not isinstance(payload, dict):
                continue
            if opcode == OP_PING:
                self._send(payload, OP_PONG)
                continue
            if opcode == OP_FRAME:
                nonce = payload.get("nonce")
                if nonce:
                    with self._pending_lock:
                        pending = self._pending_requests.get(nonce)
                    if pending:
                        pending.put((opcode, payload))
                        continue
                if payload.get("cmd") == "DISPATCH":
                    self._on_event(payload.get("evt"), payload.get("data") or {})
                continue

    def _on_event(self, evt, data):
        """Override in subclass or by RPC to dispatch events."""

    def _write(self, data: bytes):
        """Override in subclass to write bytes to the pipe."""
        raise NotImplementedError

    def _read_some(self, size: int) -> bytes:
        """Override in subclass to read up to size bytes from the pipe."""
        raise NotImplementedError

    def _read_exact(self, size: int) -> bytes:
        chunks = []
        remaining = size
        while remaining:
            chunk = self._read_some(remaining)
            if not chunk:
                raise OSError("Connection closed while reading IPC frame")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _read_frame(self):
        header = self._read_exact(8)
        opcode, length = struct.unpack("<ii", header)
        if length < 0 or length > 16 * 1024 * 1024:
            raise ValueError(f"Invalid IPC frame length: {length}")
        if length == 0:
            return opcode, None
        payload_bytes = self._read_exact(length)
        try:
            payload = json.loads(payload_bytes.decode("UTF-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid IPC frame payload: {e}")
        return opcode, payload

    def _handle_handshake_error(self, payload):
        code = payload.get("code")
        message = payload.get("error") or "Handshake failed"
        if code == 4000 or "invalid" in str(message).lower():
            raise InvalidID()
        raise RPCException(f"Handshake failed: {message}")

    def handshake(self):
        self._send({'v': 1, 'client_id': self.app_id}, OP_HANDSHAKE)

        opcode, payload = self._read_frame()
        if payload is None:
            raise RPCException("Handshake did not receive a READY event")

        if opcode == OP_CLOSE:
            self.connected = False
            raise RPCException("Handshake closed by Discord before READY")

        if not isinstance(payload, dict):
            raise RPCException("Handshake did not receive a READY event")

        if payload.get("evt") == "ERROR":
            data = payload.get("data") or {}
            error_payload = {
                "ok": False,
                "code": data.get("code"),
                "error": data.get("message") or payload.get("message"),
                "response": payload,
            }
            self._handle_handshake_error(error_payload)

        if payload.get("cmd") == "DISPATCH" and payload.get("evt") == "READY":
            user = payload.get("data", {}).get("user")
            if user:
                log.info(f"Connected to {user.get('username')} ({user.get('id')})")
                return user

        raise RPCException("Handshake did not receive a READY event")

    def disconnect(self):
        try:
            self._send({}, OP_CLOSE)
            self._close()
        except Exception as e:
            log.debug("Socket closed before command was received: %s", e)

        self._reader_stop.set()
        self._close_pending()
        reader = self._reader_thread
        if reader and reader.is_alive() and reader is not threading.current_thread():
            reader.join(timeout=2)
        self._reader_thread = None
        self.socket = None
        self.connected = False

        log.warning("Closing RPC")
        if self.exit_on_disconnect:
            sys.exit()

    def _close_pending(self):
        with self._pending_lock:
            pending = self._pending_requests
            self._pending_requests = {}
        for queue in pending.values():
            queue.put((OP_CLOSE, None))

    def _close(self):
        """Override in subclass to close the socket."""
        raise NotImplementedError


class WindowsPipe(_BasePipe):
    def _connect_pipe(self):
        base_path = R'\\?\pipe\discord-ipc-{}'

        for i in range(10):
            path = base_path.format(i)

            try:
                self.socket = open(path, "w+b")
            except OSError as e:
                if self.exit_if_discord_close:
                    log.debug("Failed to open {!r}: {}".format(path, e))
                    raise DiscordNotOpened()
                else:
                    log.debug("Discord seems to be close.")
            else:
                break

        else:
            if self.exit_if_discord_close:
                raise DiscordNotOpened()
            else:
                log.warning("Discord is closed")
            return False

        log.debug(f"Connected to {path}")
        return True

    def _write(self, data: bytes):
        self.socket.write(data)
        self.socket.flush()

    def _close(self):
        self.socket.close()

    def _read_some(self, size: int) -> bytes:
        return self.socket.read(size) or b""


class UnixPipe(_BasePipe):
    def _connect_pipe(self):
        self.socket = socket.socket(socket.AF_UNIX)

        raw_path = (
            os.environ.get('XDG_RUNTIME_DIR')
            or os.environ.get('TMPDIR')
            or os.environ.get('TMP')
            or os.environ.get('TEMP')
            or '/tmp'
        ).rstrip('/')
        candidates = [
            f"{raw_path}/{sub}discord-ipc-{i}"
            for i in range(10)
            for sub in ("", "app/com.discordapp.Discord/")  # host first, then Flatpak sandbox
        ]

        for path in candidates:
            try:
                self.socket.connect(path)
                break
            except OSError:
                pass

        else:
            if self.exit_if_discord_close:
                raise DiscordNotOpened()
            else:
                log.warning("Discord is closed")
            return False

        log.debug(f"Connected to {path}")
        return True

    def _write(self, data: bytes):
        self.socket.sendall(data)

    def _close(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.socket.close()

    def _read_some(self, size: int) -> bytes:
        return self.socket.recv(size)
