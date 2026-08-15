# Discord RPC

A Python wrapper for the Discord RPC API that allows you to create your own custom Rich Presence.

---

## Installation

```bash
pip install discord-rpc
```

> Discord desktop app must be running on the same machine.

---

## Getting Application ID

1. Go to https://discord.com/developers/applications
2. Click "New Application" if you don't have application
3. Insert the name of your application
4. Copy `APPLICATION ID`

---

## Quick Start

Step-by-step making simple rich presence using discord-rpc.

1. Make sure discord-rpc is installed.
2. Import discord-rpc
   ```py
   import discordrpc
   ```

3. Make `rpc` variable from `discordrpc.RPC` with your unique [Application ID](#getting-application-id).
   ```py
   rpc = discordrpc.RPC(app_id=1234)
   ```

4. Customizing activity using `rpc.set_activity()`.
   ```py
   rpc.set_activity(
      state="A super simple rpc",
      details="simple RPC"
   )
   ```

5. Creating loop for `rpc` so that it can keep running.
   ```py
   rpc.run()
   ```

6. Done! Run your file.

---

## API Reference

### `RPC`

```python
class RPC:
    def __init__(...): -> None
```

#### `RPC.__init__`

Creates an IPC client and attempts to connect to the local Discord instance.

Parameters:
- **app_id** *(int)* — Your Discord Application (Client) ID.
- **debug** *(bool, default: `False`)* — If `True`, enables verbose logging (DEBUG).
- **output** *(bool, default: `True`)* — If `False`, silences logger output.
- **exit_if_discord_close** *(bool, default: `True`)* — If `True`, raises when Discord is not found or closed.
- **exit_on_disconnect** *(bool, default: `True`)* — If `True`, exits the process when the socket disconnects.

Variables:
- **is_running** *(bool)* — Whether the RPC successfully set an activity.
- **try_reconnecting** *(bool, default: `True`)* — Whether to attempt reconnecting on disconnect.
- **connected** *(bool, property)* — Whether the IPC connection to Discord is alive. Read-only alias for `self.ipc.connected`.
- **User** *(cached_property)* — Returns a `User` object populated after handshake (see [User](#user)).
- **App** *(cached_property)* — Returns an `Application` object fetched from Discord API (see [App](#app)).
- **assets** *(cached_property)* — Returns an `AssetManager` containing all uploaded Rich Presence assets (see [AssetManager](#assetmanager)).

#### `RPC.set_activity`

```python
def set_activity(...): -> Optional[bool]
```

Sets or updates the current Rich Presence. Returns `True` on success.

Parameters (all optional unless stated):

- **name** *(str)* — Name of the activity. If not provided, Discord uses the application name by default.
- **details** *(str)* — Upper line of the activity.
- **state** *(str)* — Lower line of the activity.
- **act_type** *(Activity, default: `Activity.Playing`)* — See [Activity Types](#activity-types).
- **status_type** *(StatusDisplay, default: `StatusDisplay.Name`)* — Which field is considered the status name for some clients.
- **large_image** *(str)* — Key of an uploaded Rich Presence Asset, or an external direct URL.
- **large_text** *(str)* — Tooltip when hovering the large image.
- **large_url** *(str)* — Optional URL for the large image.
- **small_image** *(str)* — Key of a small asset, or an external direct URL.
- **small_text** *(str)* — Tooltip for the small image.
- **small_url** *(str)* — Optional URL for the small image.
- **state_url**, **details_url** *(str)* — Optional link targets when clicking the text.
- **ts_start**, **ts_end** *(int)* — Unix timestamps (seconds). See [Utils](#utils) for helpers.
- **party_id** *(str)* — ID to identify a party or session.
- **party_size** *(list[int, int])* — Current and max size, e.g. `[2, 5]`.
- **join_secret**, **spectate_secret**, **match_secret** *(str)* — Secrets for join/spectate/match.
- **buttons** *(list[dict])* — Up to 2 buttons created by [`button()`](#buttons).
- **clear** *(bool)* — If `True`, clears the activity.

Notes:
- `act_type` must be a `types.Activity` member; otherwise `InvalidActivityType` is raised.
- `Activity.Streaming` and `Activity.Custom` are disabled for Rich Presence updates and will raise `ActivityTypeDisabled`.
- Images can be an uploaded asset key or an external direct URL (PNG, JPEG, WebP, GIF, AVIF).

#### `RPC.run()`

```python
def run(update_every: int = 1, ping_every: int = 15): -> None
```

Keeps the RPC alive. Not required if another task is running on the same file.

Parameters:
- **update_every** *(int, default: `1`)* — Loop sleep interval.
- **ping_every** *(int, default: `15`)* — OP_PING heartbeat interval to prevent socket timeout.

#### `RPC.clear()`

```python
def clear(): -> None
```

Clears the current activity without disconnecting.

#### `RPC.disconnect()`

```python
def disconnect(): -> None
```

Closes the IPC socket and marks the client as disconnected.

---

### User

```python
rpc.User  # cached_property, populated after handshake
```

A lightweight `User` model.

Attributes:
- **id** *(int)* — Discord user ID.
- **username** *(str)* — Username.
- **name** *(str)* — Global display name.
- **avatar** *(str)* — CDN URL (animated GIF detection supported).
- **avatar_decoration** *(str)* — CDN URL to the avatar decoration preset, or `""` when not set.
- **bot** *(bool)* — Whether the user is a bot.
- **premium_type** *(int)* — Discord Nitro tier.

#### Example
```py
import discordrpc
rpc = discordrpc.RPC(app_id=123456789)
print(rpc.User.name)
print(f"@{rpc.User.username}")
rpc.run()
```

---

### App

```python
rpc.App  # cached_property, lazy-loaded from Discord API
```

An `Application` model. The HTTP request is lazy-loaded on first access.

Attributes:
- **id** *(int)* — Application ID.
- **name** *(str)* — Application name.
- **description** *(str)* — Application description.
- **icon** *(str)* — CDN URL to the application icon.
- **cover** *(str)* — CDN URL to the application cover image (keeps aspect ratio), or `""` when not set.
- **verified** *(bool)* — Whether the application is verified.
- **public** *(bool)* — Whether the bot is public.

---

## Buttons

```python
from discordrpc import button
button(text: str, url: str) -> dict
```

Creates a Discord-compatible button payload (max 2 buttons).

Parameters:
- **text** *(str)* — Button label.
- **url** *(str)* — Must start with `http://` or `https://`. Raises `InvalidURL` otherwise.

#### Example
```py
import discordrpc
from discordrpc import button

rpc = discordrpc.RPC(app_id=123456789)
rpc.set_activity(
    state="Made by Senophyx",
    details="Discord-RPC",
    buttons=[
        button("Repository", "https://github.com/Senophyx/discord-rpc"),
        button("Discord", "https://discord.gg/qpT2AeYZRN"),
    ]
)
rpc.run()
```

---

## Utils

```python
from discordrpc import utils
```

### `utils.timestamp`
```python
def timestamp() -> int
```
Returns the current time in epoch timestamp.

### `utils.date_to_timestamp`
```python
def date_to_timestamp(date: str) -> int
```
Converts `%d/%m/%Y-%H:%M:%S` format to epoch timestamp.

### `utils.use_local_time`
```python
def use_local_time() -> dict
```
Returns a `ts_start` payload starting from midnight today.

### `utils.progress_bar`
```python
def progress_bar(current: int, duration: int) -> dict
```
Returns `ts_start` and `ts_end` based on progress. Raises `ProgressbarError` if `current` is negative, `duration` is zero or negative, or `current > duration`.

### `utils.get_app_info`
```python
def get_app_info(app_id: int) -> dict
```
Fetch application info from Discord API without initializing `RPC`.

### `utils.get_assets`
```python
def get_assets(app_id: int) -> list
```
Fetch all uploaded Rich Presence assets from Discord API without initializing `RPC`. Returns a list of asset dicts with `id`, `name`, and `type` keys.

### `utils.valid_url`
```python
def valid_url(url) -> str
```
Validates an optional URL. Returns the URL unchanged if valid, or `None` if not provided. Raises `InvalidURL` if the URL is not a valid `http://` or `https://` URL.

### `utils.required_url`
```python
def required_url(url) -> str
```
Validates a required URL. Raises `InvalidURL` if missing or not a valid `http://` or `https://` URL. Used by `set_activity()` to validate button URLs.

### `utils.remove_none`
```python
def remove_none(d: dict) -> dict
```
Recursively removes `None` values and empty dicts from a dict.

---

## Activity Types

```python
from discordrpc import Activity
```

- `Activity.Playing` (0)
- `Activity.Streaming` (1) — disabled for RPC
- `Activity.Listening` (2)
- `Activity.Watching` (3)
- `Activity.Custom` (4) — disabled for RPC
- `Activity.Competing` (5)

---

## Status Display Types

```python
from discordrpc import StatusDisplay
```

- `StatusDisplay.Name` (0)
- `StatusDisplay.State` (1)
- `StatusDisplay.Details` (2)

---

## Events

You can subscribe to Rich Presence events and receive callbacks when they fire.

```python
import discordrpc
from discordrpc import Event

rpc = discordrpc.RPC(app_id=123456789)

@rpc.on(Event.JOIN_REQUEST)
def on_join_request(data):
    print("Ask to Join:", data)

rpc.run()
```

Supported events (from `discordrpc.Event`):

- `Event.JOIN` (`ACTIVITY_JOIN`)
- `Event.JOIN_REQUEST` (`ACTIVITY_JOIN_REQUEST`)
- `Event.SPECTATE` (`ACTIVITY_SPECTATE`)
- `Event.INVITE` (`ACTIVITY_INVITE`)

Only these activity events are currently exposed. Other Discord RPC events are not supported yet.

### Enabling JOIN and SPECTATE events

- `party_id` is **required** for the "Ask to Join" button and the `ACTIVITY_JOIN_REQUEST` event to work. Without it, Discord cannot resolve the party, the event is never delivered, and the requester gets "Your message could not be delivered."
- `join_secret` and `spectate_secret` must have **different values**. Discord rejects the activity with `secrets must be unique` when they match.

A minimal working setup:

```python
rpc.set_activity(
    name="VALORANT",
    details="Valorant Ranked",
    party_id=1234,
    join_secret="anything",
    spectate_secret="idk",
)
```

### Direct subscribe and unsubscribe

```python
rpc.subscribe("ACTIVITY_JOIN")        # string form accepted
rpc.subscribe(Event.JOIN)             # enum form accepted
rpc.unsubscribe(Event.JOIN)
```

- `subscribe()` / `unsubscribe()` accept either an `Event` member or a valid event string.
- An unknown event name raises `InvalidEvent`.
- A non-string, non-enum value raises `InvalidEventType`.
- The `@rpc.on()` decorator raises `RPCException` if the subscription is rejected by Discord.

### Callback behavior

- Callbacks run on the internal IPC reader thread. Keep them short and non-blocking.
- A slow callback delays processing of other events and responses.
- An exception raised inside a callback is logged and does not stop the reader.
- Use locks or queues if your callback touches shared state.

### Disconnect and reconnect

- `disconnect()` clears all subscriptions and callbacks.
- After a reconnect, call `subscribe()` again if you want events.
- `subscribe()` and `unsubscribe()` automatically attempt to reconnect when the pipe is disconnected (e.g. after the reader stops idle following the last unsubscribe).

---

## Exceptions

All exceptions extend `RPCException`.

| Exception | Description |
|-----------|-------------|
| `RPCException` | Base exception |
| `Error(message)` | Generic user error |
| `DiscordNotOpened()` | Discord not found/running |
| `ActivityError()` | Invalid activity payload |
| `InvalidURL(message)` | URL is not a valid http/https URL |
| `InvalidID()` | Invalid Application ID |
| `ButtonError(message)` | Button limit exceeded |
| `ProgressbarError(message)` | Invalid progress values |
| `InvalidActivityType(message)` | act_type not a valid Activity |
| `ActivityTypeDisabled()` | Streaming/Custom blocked by Discord |
| `InvalidEvent(message)` | Event name is not subscribable |
| `InvalidEventType(message)` | Event input is not a string or Event |

---

## Troubleshooting

- **"Discord is closed"** — Ensure desktop app is running. On Linux, check `$XDG_RUNTIME_DIR` / `tmp/discord-ipc-*`.
- **`ActivityTypeDisabled`** — Use `Playing`, `Listening`, `Watching`, or `Competing` instead.
- **Buttons don't show** — Max 2 buttons, URLs must start with `http://` or `https://`.
- **No images appear** — Upload assets to Discord Developer Portal Art Assets section.
- **App exits on disconnect** — Set `exit_on_disconnect=False`.
- **Silence logs** — Pass `output=False`.

---

## FAQ

**Q: Do I need a bot token?**  
A: No. Only an Application ID.

**Q: Can I update presence from a server?**  
A: No. This is client-side IPC, Discord must run on the same machine.

**Q: Can I use Streaming or Custom activity?**  
A: No, those types are disabled and raise `ActivityTypeDisabled`.

---

## AssetManager

```python
rpc.assets  # cached_property, lazy-loaded from Discord API
```

An `AssetManager` (subclass of `list`) containing all uploaded Rich Presence art assets. Fetched once on first access using `utils.get_assets()`.

### Methods

- **`assets.get(name: str) -> Asset | None`** — Returns an `Asset` object by its asset key name, or `None` if not found.
- **`assets.names`** *(property)* — Returns a list of all asset names.

### Asset Object

Each `Asset` in the manager has these attributes:
- **id** *(int)* — Asset ID.
- **name** *(str)* — Asset key name (used as `large_image` / `small_image` value).
- **type** *(int)* — Asset type from Discord.
- **url** *(str)* — Full CDN URL to the asset image (PNG, 1024px).

### Example

Discovery and usage:

```py
import discordrpc

rpc = discordrpc.RPC(app_id=123456789)

# List all available asset names
print(rpc.assets.names)

# Loop through all assets with their CDN URLs
for asset in rpc.assets:
  print(f"{asset.name}: {asset.url}")

# Set activity using an asset by name
rpc.set_activity(
  state="Assets example",
  large_image=rpc.assets.get("cat")
)

rpc.run()
```

> **Note:** For basic usage, you can still pass asset key strings directly (e.g. `large_image="cat"`) without using the AssetManager. The manager is useful when you need to discover assets dynamically or access their CDN URLs.

---

## Links
- [GitHub](https://github.com/Senophyx/discord-rpc)
- [PyPI](https://pypi.org/project/discord-rpc/)
- [TestPyPI](https://test.pypi.org/project/discord-rpc/)
- [Discord](https://discord.gg/qpT2AeYZRN)

## Licence
```
MIT License
Copyright (c) 2021-2025 Senophyx
```