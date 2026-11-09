from enum import Enum


# https://docs.discord.com/developers/events/gateway-events#activity-object-activity-types
class Activity(Enum):
    Playing = 0
    Streaming = 1
    Listening = 2
    Watching = 3
    Custom = 4
    Competing = 5

# https://docs.discord.com/developers/events/gateway-events#activity-object-status-display-types
class StatusDisplay(Enum):
    Name = 0
    State = 1
    Details = 2

# https://docs.discord.com/developers/topics/rpc#commands-and-events-rpc-events
class Event(Enum):
    JOIN = "ACTIVITY_JOIN"                 # https://docs.discord.com/developers/topics/rpc#activity_join
    JOIN_REQUEST = "ACTIVITY_JOIN_REQUEST" # https://docs.discord.com/developers/topics/rpc#activity_join_request
    SPECTATE = "ACTIVITY_SPECTATE"         # https://docs.discord.com/developers/topics/rpc#activity_spectate
    INVITE = "ACTIVITY_INVITE"             # https://docs.discord.com/developers/topics/rpc#activity_invite

# https://docs.discord.com/developers/topics/rpc#current_user_update
class User():
    def __init__(self, data:dict=None):
        data = data or {}
        self.id: int = int(data.get('id', 0))
        self.username: str = data.get('username')
        self.name: str = data.get('global_name')
        self.avatar: str = self._parse_avatar(data)
        self.bot: bool = data.get('bot', False)
        self.premium_type: int = int(data.get('premium_type', 0))
        self.avatar_decoration: str = self._parse_decoration((data.get("avatar_decoration_data") or {}))

    def _parse_avatar(self, data:dict, size:int=1024) -> str:
        if data.get('avatar'):
            ext = "gif" if data.get('avatar').startswith("a_") else "png"
            return f"https://cdn.discordapp.com/avatars/{self.id}/{data.get('avatar')}.{ext}?size={size}"
        return f"https://cdn.discordapp.com/embed/avatars/0.png"

    def _parse_decoration(self, data:dict, size:int=1024) -> str:
        if data.get("asset"):
            return f"https://cdn.discordapp.com/avatar-decoration-presets/{data.get('asset')}.png?size={size}"
        return ""

    def __str__(self):
        return f"User({self.name})"

class Application():
    def __init__(self, data:dict=None):
        data = data or {}
        self.id: int = int(data.get("id", 0))
        self.name: str = data.get("name")
        self.description: str = data.get("description")
        self.icon: str = self._parse_icon(data.get("icon"))
        self.cover: str = self._parse_cover(data.get("cover_image"))
        self.verified: bool = data.get("is_verified", False)
        self.public: bool = data.get("bot_public", False)

    def _parse_icon(self, icon_id:str, size:int=1024) -> str:
        if icon_id:
            return f"https://cdn.discordapp.com/app-icons/{self.id}/{icon_id}.png?size={size}"
        return "https://cdn.discordapp.com/embed/avatars/1.png"

    def _parse_cover(self, icon_id:str, size:int=1024) -> str:
        if icon_id:
            return f"https://cdn.discordapp.com/app-icons/{self.id}/{icon_id}.png?size={size}&keep_aspect_ratio=true"
        return ""

    def __str__(self):
        return f"Application({self.name})"

class Asset():
    def __init__(self, app_id:int, data:dict=None, size:int=1024):
        data = data or {}
        self.app_id: int = app_id
        self.id: int = int(data.get("id", 0))
        self.name: str = data.get("name")
        self.type: int = int(data.get("type", 0))
        self.url: str = f"https://cdn.discordapp.com/app-assets/{self.app_id}/{self.id}.png?size={size}"

    def __str__(self):
        return f"Asset({self.name})"
    def __repr__(self):
        return str(self)

class AssetManager(list):
    def __init__(self, app_id:int, assets_list:list=None):
        super().__init__(
            Asset(app_id, asset)
            for asset in (assets_list or [])
        )
    def get(self, name: str) -> Asset:
        return next((asset for asset in self if asset.name == name), None)

    @property
    def names(self) -> list:
        return list(map(lambda asset: asset.name, self))
