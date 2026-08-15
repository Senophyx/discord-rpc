# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Unreleased

### Fixed
- `run()` now exits its loop when the heartbeat PING fails, instead of hanging forever when `exit_on_disconnect=False`
- `subscribe()` and `unsubscribe()` now attempt to reconnect when the pipe is disconnected, instead of silently returning `None` (this happened after the reader stopped idle following the last unsubscribe)
- `progress_bar()` now raises `ProgressbarError` when `current` is negative or `duration` is zero/negative
- `AssetManager()` no longer raises `TypeError` when constructed without an asset list
- IPC reader now marks the pipe as disconnected when the socket is closed by Discord (EOF) or an `OP_CLOSE` frame with an empty payload is received, instead of stopping silently while `connected` stays `True`

### Changed
- **BREAKING**: `utils.timestamp` is now a function, not a variable. Update `timestamp` to `timestamp()` in your code.

## [6.5] - 2026-08-05

### Added
- Cross-platform event subscriptions with `Event` enum and `@rpc.on()` decorator (PR [#66](https://github.com/Senophyx/discord-rpc/pull/66) by @SuperZombi)
- `AssetManager` with `RPC.assets` property and `.get()` / `.names` for fetching Discord application assets (PR [#60](https://github.com/Senophyx/discord-rpc/pull/60) by @SuperZombi)
- `Asset` object support in `set_activity()` — pass `rpc.assets.get("key")` directly as `large_image` / `small_image`
- `utils.get_assets(app_id)` function to fetch assets without initializing `RPC`
- `RPC.connected` read-only property as alias for `self.ipc.connected` (PR [#63](https://github.com/Senophyx/discord-rpc/pull/63) by @SuperZombi)
- `InvalidEvent` and `InvalidEventType` exceptions exported from the package root
- `utils.required_url()` for validating required button URLs
- `examples/rpc-events.py` showing event subscription usage
- `User.avatar_decoration` and `Application.cover` CDN URLs (PR [#67](https://github.com/Senophyx/discord-rpc/pull/67) by @SuperZombi)

### Changed
- IPC reads now preserve the opcode and route responses by nonce through a single background reader
- Windows imports are now loaded only on Windows; the blocking reader no longer needs `msvcrt` or `win32pipe`
- URL validation now checks the scheme and host instead of only a prefix
- `set_activity()` now validates button URLs client-side
- Bumped GitHub Actions versions: `checkout@v4→v6`, `setup-python@v4→v6` (PR [#62](https://github.com/Senophyx/discord-rpc/pull/62) by @SuperZombi)
- Link badges in `README.md` now point to local `CHANGELOG.md` and `DOCS.md` instead of `senophyx.id`
- `DOCS.md` documentation URL in `pyproject.toml` updated to point to GitHub

### Fixed
- Invalid method annotations in `_send()` and `_request()` that prevented importing the package
- Unread `PONG` responses no longer corrupt subsequent RPC requests
- Incoming `PING` packets are answered with `PONG`
- Handshake no longer requires a nonce and reads the READY frame directly
- Event subscription state no longer mixes callback storage with subscription state
- Failed subscriptions no longer register callbacks locally
- Reader thread stops after the last unsubscribe and is cleaned up during disconnect
- `subscribe()` returns `True` for already-subscribed events so stacked handlers work
- Pipe is marked disconnected when the reader stops idle, allowing reconnect
- `pyproject.toml` license uses the PEP 621 table so wheel builds succeed
- Indentation in `examples/assets.py` corrected to 4 spaces
- `User.__str__`, `Application.__str__`, `Asset.__str__`, and `Asset.__repr__` reformatted to multi-line for codebase consistency

### Documentation
- Added `avatar_decoration`, `cover`, URL validation helpers, and `remove_none` to `DOCS.md`

## [6.0] - 2026-07-21

### Added
- `name` parameter to `RPC.set_activity()` (optional, falls back to Discord application name if not provided) (PR [#58](https://github.com/Senophyx/discord-rpc/pull/58) by @SuperZombi)
- `ping_every` parameter to `RPC.run()` for configurable OP_PING heartbeat interval
- External URL image support for `large_image` and `small_image` (direct HTTP URLs now supported alongside asset keys)

### Changed
- `User` and `App` refactored from instance attributes to `@cached_property` -- lazy-loaded and read-only after first access (PR [#58](https://github.com/Senophyx/discord-rpc/pull/58) by @SuperZombi)
- `RPC.get_app_info()` method removed; access application info via `rpc.App` property directly
- Activity payload building inlined from `_build_activity()` back into `set_activity()` for simplicity
- Shared pipe connection logic extracted into `_BasePipe` class, eliminating DRY violations between `WindowsPipe` and `UnixPipe`
- `Button()` function renamed to `button()` for PEP8 compliance
- `TRY_RECONNECTING` global converted to instance attribute `self.try_reconnecting`
- Internal logging variables renamed for specificity
- `urllib.request` and `json` imports in `utils.py` moved to top level

### Fixed
- Socket timeout prevention: OP_PING heartbeat now sent every 15 seconds by default in `RPC.run()`
- Log handler duplication across multiple RPC instances
- `logging.basicConfig()` removed to avoid polluting user's logging configuration
- Global variable declaration order causing `SyntaxError` on some Python versions
- Overly broad `except KeyError` in `handshake()` methods
- `UnixPipe._recv()` data truncation on large payloads
- `set_activity()` return type annotation corrected from `bool` to `Optional[bool]`
- `self.connected` now properly set from `_connect_pipe()` return value instead of defaulting to `True`
- Broken button arguments in `print-rpc-output.py` example

### Documentation
- Rewrote `DOCS.md` with updated API reference and corrected codebase changes
- Added `CHANGELOGS.md` with full release history from v2.0
- Added clear activity and all-in-one complex RPC examples
- Added external URL image support information to docstrings and examples

## [5.6] - 2026-06-14

### Added
- `Application` info fetching via `rpc.get_app_info()` and `utils.get_app_info()` (PR [#57](https://github.com/Senophyx/discord-rpc/pull/57) by @SuperZombi & @Senophyx)
- `pyproject.toml` licensing metadata

### Changed
- Renamed `ProgressBar` to `progress_bar` for consistent naming convention
- Replaced all-contributors with contrib.rocks for contributor display
- Cleaned up unused parameter comments across codebase
- Removed License classifiers in favor of PEP 639 compliant metadata
- Updated documentation links and styling across the project

### Fixed
- `importlib.metadata.PackageNotFoundError` when package is not installed (PR [#56](https://github.com/Senophyx/discord-rpc/pull/56) by @deeffest)
- Typing and license metadata in `pyproject.toml`

## [5.5] - 2025-10-23

### Added
- New `ActivityType` class and type system enhancements (PR [#49](https://github.com/Senophyx/discord-rpc/pull/49) by @SuperZombi)
- New parameters and types for `set_activity()` (PR [#50](https://github.com/Senophyx/discord-rpc/pull/50) by @SuperZombi)
- Additional missing types (PR [#53](https://github.com/Senophyx/discord-rpc/pull/53) by @jannuary)

### Changed
- Migrated from `setup.py` to PEP 621 compliant `pyproject.toml` ([0ffaca5](https://github.com/Senophyx/discord-rpc/commit/0ffaca5bbf941a1435defac789c966a8d7d3ad5c))
- Button class rewritten with improved implementation

### Fixed
- Minor issues in activity handling and button functionality

## [5.1] - 2024-09-18

### Added
- Activity Types support (`Activity.Playing`, `Activity.Listening`, `Activity.Watching`, `Activity.Competing`, etc.)
- More detailed output information for debugging

## [5.0] - 2024-03-13

### Changed (Breaking)
- **Inputting Application ID is no longer in `RPC.set_id()`.** Replaced with direct input in the `RPC` class.

  Before:
  ```py
  rpc = discordrpc.RPC.set_id(app_id=1234567890)
  ```

  After:
  ```py
  rpc = discordrpc.RPC(app_id=1234567890)
  ```

### Removed
- Multiple internal functions removed:
  - `RPC.set_id`
  - `RPC._connect`, `RPC._write`, `RPC._recv`, `RPC._recv_exact`
  - And many more internal methods

### Changed
- Package `logging` reintroduced for output
- `timestamp` argument in `set_activity()` replaced with `ts_start` and `ts_end`
- `timestamp` variable moved to `discordrpc.utils`:
  ```py
  from discordrpc.utils import timestamp
  ```
- `button` in `discordrpc.button` renamed to `Button`
- Added `debug` parameter to `RPC` class for verbose logging

### Added
- `date_to_timestamp()` function in `discordrpc.utils` (format: `%d/%m/%Y-%H:%M:%S`)

## [4.0] - 2023-09-11

### Changed (Breaking)
- **Package folder renamed from `DiscordRPC` to `discordrpc`.**

  Before:
  ```py
  import DiscordRPC
  ```

  After:
  ```py
  import discordrpc
  ```

### Removed
- `GCAR` (`get_current_application_running`) - removed because it cannot be cross-platform
- `setLoggerEnabled()` function

### Changed
- `Set_ID` renamed to `set_id`
- `output()` function replaced with `show_output` variable
- No longer using the `logging` package
- Code in `presence.py` shortened and simplified

## [3.5] - 2022-05-31

### Added
- Initial `get_app_info()` function for fetching application details from Discord API

### Fixed
- Various bug fixes and stability improvements

## [3.0] - 2022-01-22

### Added
- `GCAR` (Get Current Application Running) method - automatically switches RPC status to the application currently running

## [2.0] - 2021-12-14

### Added
- Button support (up to 2 buttons per activity)
- RPC output logging (success and error messages)

### Fixed
- RPC now runs correctly even when `large_text` and `small_text` are not set
- Success message now displays properly on RPC set
- Error appears if RPC is not set correctly
