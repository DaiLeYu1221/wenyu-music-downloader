import requests
from config import API_KEY, PLATFORMS


class MusicAPI:
    """Client for all music platform APIs."""

    HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }

    @classmethod
    def search(cls, platform: str, keyword: str, count: int = None) -> dict:
        """
        Search for music on a given platform.
        Returns a list of songs.
        """
        cfg = PLATFORMS[platform]
        params = {"msg": keyword}

        if cfg["need_key"]:
            params["key"] = API_KEY

        if count is None:
            count = cfg["default_count"]
        params["g"] = count

        resp = requests.get(cfg["endpoint"], params=params, headers=cls.HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 200:
            raise Exception(f"API error: {data.get('msg', 'Unknown error')}")

        return data["data"]

    @classmethod
    def get_song_detail(cls, platform: str, index: int, keyword: str = None,
                        quality: str = None, song_id: str = None) -> dict:
        """
        Get detail of a single song including download URL.
        """
        cfg = PLATFORMS[platform]

        if platform == "kw" and song_id:
            # Kuwo supports fetching by RID directly
            params = {"action": "song", "id": song_id, "key": API_KEY}
            if quality:
                params["size"] = quality
        else:
            params = {"n": index}
            if cfg["need_key"]:
                params["key"] = API_KEY
            if keyword:
                params["msg"] = keyword
            if quality:
                if platform == "qq":
                    params["size"] = quality
                elif platform == "kg":
                    params["quality"] = quality
                elif platform == "kw":
                    params["size"] = quality

        resp = requests.get(cfg["endpoint"], params=params, headers=cls.HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 200:
            raise Exception(f"API error: {data.get('msg', 'Unknown error')}")

        return data["data"]

    @classmethod
    def get_song_url(cls, platform: str, detail: dict) -> str:
        """Extract the music download URL from song detail."""
        url_keys = {
            "wy": ["musicurl", "url"],
            "qq": ["musicurl"],
            "kg": ["play_url"],
            "kw": ["vipmusic", "url"],
            "apple": ["url", "music_url"],
        }

        keys = url_keys.get(platform, [])
        for key in keys:
            if key == "vipmusic" and platform == "kw":
                if isinstance(detail.get("vipmusic"), dict):
                    return detail["vipmusic"].get("url", "")
            elif detail.get(key):
                return detail[key]

        return ""

    @classmethod
    def get_cover_url(cls, platform: str, detail: dict) -> str:
        """Extract the cover image URL from song detail."""
        cover_keys = {
            "wy": ["picture"],
            "qq": ["picture"],
            "kg": ["cover"],
            "kw": ["picture"],
            "apple": ["cover"],
        }

        keys = cover_keys.get(platform, [])
        for key in keys:
            if detail.get(key):
                return detail[key]

        return ""

    @classmethod
    def get_song_info_for_tagging(cls, platform: str, detail: dict) -> dict:
        """Extract song info (title, artist, album) for metadata tagging."""
        info = {}

        if platform == "wy":
            info["title"] = detail.get("name", "")
            info["artist"] = detail.get("songname", "")
            info["album"] = detail.get("album", "")
        elif platform == "qq":
            info["title"] = detail.get("name", "")
            info["artist"] = detail.get("songname", "")
            info["album"] = detail.get("album", "")
        elif platform == "kg":
            info["title"] = detail.get("name", "")
            info["artist"] = detail.get("singer", "")
            info["album"] = detail.get("album", "")
        elif platform == "kw":
            info["title"] = detail.get("name", "")
            info["artist"] = detail.get("songname", "")
            info["album"] = detail.get("album", "")
        elif platform == "apple":
            info["title"] = detail.get("trackName") or detail.get("songname", "")
            info["artist"] = detail.get("artistName") or detail.get("singername", "")
            info["album"] = detail.get("collectionName") or detail.get("album", "")

        return info
