from importlib.metadata import version as _pkg_ver, PackageNotFoundError
from .presence import RPC
from .button import button
from .exceptions import (
    RPCException, Error, DiscordNotOpened, ActivityError,
    InvalidURL, InvalidID, ButtonError, ProgressbarError,
    InvalidActivityType, ActivityTypeDisabled,
    InvalidEvent, InvalidEventType,
)
from .types import Activity, StatusDisplay, User, Application, Event
from .utils import remove_none, timestamp, date_to_timestamp, use_local_time, progress_bar, get_app_info

__title__ = "Discord RPC"
try:
    __version__ = _pkg_ver('discord-rpc')
except PackageNotFoundError:
    __version__ = "7.0"
__authors__ = "Senophyx"
__license__ = "MIT License"
__copyright__ = "Copyright 2021-2025 Senophyx"
