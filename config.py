import json
import os

_config_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(_config_path, "r", encoding="utf-8") as _f:
    API_KEY = json.load(_f)["api_key"]

BASE_URL = "https://api.yaohud.cn/api/music"

# Platform endpoints
PLATFORMS = {
    "wy": {
        "name": "网易云音乐",
        "endpoint": f"{BASE_URL}/wy",
        "default_count": 13,
        "need_key": True,
    },
    "qq": {
        "name": "QQ音乐",
        "endpoint": f"{BASE_URL}/qq",
        "default_count": 10,
        "need_key": True,
        "qualities": ["flac", "320", "128"],
    },
    "kw": {
        "name": "酷我音乐",
        "endpoint": f"{BASE_URL}/kuwo",
        "default_count": 13,
        "need_key": True,
        "qualities": ["hires", "lossless", "SQ", "exhigh", "Standard"],
    },
}

# Lyrics endpoint
LYRICS_URL = f"{BASE_URL}/lrc"

# Quality fallback order (highest to lowest)
QUALITY_FALLBACK = {
    "qq": ["flac", "320", "128"],
    "kw": ["hires", "lossless", "SQ", "exhigh", "Standard"],
}

# Platform type mapping for lyrics API
LYRICS_TYPE_MAP = {
    "wy": "wy",
    "qq": "qq",
    "kw": "kw",
}
