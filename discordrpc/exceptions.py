class RPCException(Exception):
    def __init__(self, message: str= None):
        if message is None:
            message = 'An error has occurred within DiscordRPC'
        super().__init__(message)

class Error(RPCException):
    def __init__(self, message:str):
        super().__init__(message)

class DiscordNotOpened(RPCException):
    def __init__(self):
        super().__init__("Error, could not find Discord. is Discord running?")

class ActivityError(RPCException):
    def __init__(self):
        super().__init__("An error has occurred in activity payload, do you have set your activity correctly?")

class InvalidURL(RPCException):
    def __init__(self, message: str = None):
        if message is None:
            message = "URL must be a valid http:// or https:// URL"
        super().__init__(message)

class InvalidID(RPCException):
    def __init__(self):
        super().__init__("Invalid ID, is the ID correct? Get Application ID on https://discord.com/developers/applications")

class ButtonError(RPCException):
    pass

class ProgressbarError(RPCException):
    pass

class InvalidActivityType(RPCException):
    def __init__(self, message):
        super().__init__(f"Activity type must be <Activity>, not {message}")

class InvalidEvent(RPCException):
    def __init__(self, message):
        super().__init__(f"'{message}' is not a subscribable event.")

class InvalidEventType(RPCException):
    def __init__(self, message):
        super().__init__(f"Event type must be <Event>, not {message}")

# https://github.com/Senophyx/discord-rpc/issues/28#issuecomment-2301287350
class ActivityTypeDisabled(RPCException):
    def __init__(self):
        super().__init__(f"Activity type `Streaming` and `Custom` currently disabled. See https://github.com/Senophyx/discord-rpc/issues/28#issuecomment-2301287350")
