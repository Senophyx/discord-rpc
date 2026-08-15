import time
import json
import urllib.request
import urllib.parse
from datetime import datetime
import logging
from .exceptions import ProgressbarError, InvalidURL

log = logging.getLogger("Discord RPC")

# Credits to qwertyquerty
# https://github.com/qwertyquerty/pypresence/blob/master/pypresence/utils.py#L12C1-L21C13

def remove_none(d: dict):
    for item in d.copy():
        if isinstance(d[item], dict):
            if len(d[item]):
                d[item] = remove_none(d[item])
            if not len(d[item]):
                del d[item]
        elif d[item] is None:
            del d[item]
    return d


timestamp = int(time.mktime(time.localtime()))


def date_to_timestamp(date:str):
    return int(time.mktime(
        datetime.strptime(date, "%d/%m/%Y-%H:%M:%S").timetuple()
    ))

def _validate_url(url, required: bool):
    if url is None:
        if required:
            raise InvalidURL("URL must be a valid http:// or https:// URL")
        return url
    if not isinstance(url, str) or not url:
        raise InvalidURL("URL must be a valid http:// or https:// URL")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InvalidURL("URL must be a valid http:// or https:// URL")
    return url

def valid_url(url):
    return _validate_url(url, required=False)

def required_url(url):
    return _validate_url(url, required=True)

def use_local_time():
    now = datetime.now()
    seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
    return {
        "ts_start": int(time.time()) - seconds_since_midnight
    }

def progress_bar(current:int, duration:int) -> dict:
    current, duration = int(current), int(duration)
    if current < 0:
        raise ProgressbarError("Current cannot be negative")
    if duration <= 0:
        raise ProgressbarError("Duration must be greater than zero")
    if current > duration:
        raise ProgressbarError("Current cannot exceed Duration")
    
    current_time = int(time.time()) - current
    finish_time = current_time + duration

    return {
        "ts_start": current_time, "ts_end": finish_time
    }

def get_app_info(app_id:int) -> dict:
    try:
        req = urllib.request.Request(f"https://discord.com/api/v10/applications/{app_id}/rpc")
        req.add_header('User-Agent', 'discord-rpc/1.0')
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        log.error(f"Failed to fetch application info: {e}")
    return {}

def get_assets(app_id:int) -> list:
    try:
        req = urllib.request.Request(f"https://discord.com/api/v10/oauth2/applications/{app_id}/assets")
        req.add_header('User-Agent', 'discord-rpc/1.0')
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        log.error(f"Failed to fetch application assets: {e}")
    return []
