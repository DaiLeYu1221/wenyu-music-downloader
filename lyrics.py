import re
import requests
from config import API_KEY, LYRICS_URL, LYRICS_TYPE_MAP
from api_client import MusicAPI


class LyricsFetcher:
    """Fetch lyrics from API or extract from song detail."""

    @classmethod
    def fetch(cls, platform: str, song_id: str = None, detail: dict = None) -> str:
        """
        Fetch lyrics for a song.
        Priority:
        1. lrctxt field in detail (NetEase direct text)
        2. lrc/viplrc URL in detail -> fetch it
        3. Dedicated lyrics API with real song ID
        """
        # Try lrctxt (direct text in detail)
        if detail:
            lrc = cls._extract_from_detail(platform, detail)
            if lrc:
                return lrc

            # Try lrc URL from detail (NetEase: lrc URL, QQ: viplrc URL)
            lrc_url = cls._extract_lrc_url(platform, detail)
            if lrc_url:
                lrc = cls._fetch_from_url(lrc_url)
                if lrc:
                    return lrc

        # Try dedicated lyrics API with real song ID
        if song_id:
            lrc = cls._fetch_from_api(platform, song_id)
            if lrc:
                return lrc

        return ""

    @classmethod
    def _extract_from_detail(cls, platform: str, detail: dict) -> str:
        """Extract lyrics text directly from song detail."""
        if platform == "wy":
            lrctxt = detail.get("lrctxt")
            if lrctxt and isinstance(lrctxt, str) and len(lrctxt) > 10:
                return cls._normalize(lrctxt)
        elif platform == "kw":
            # Kuwo: lyric is an object with 'lrc' field
            lyric_obj = detail.get("lyric")
            if lyric_obj and isinstance(lyric_obj, dict):
                lrc = lyric_obj.get("lrc")
                if lrc and isinstance(lrc, str) and len(lrc) > 10:
                    return cls._normalize(lrc)
        return ""

    @classmethod
    def _extract_lrc_url(cls, platform: str, detail: dict) -> str:
        """Extract lyrics URL from detail response."""
        if platform == "wy":
            # NetEase: lrc field is a URL
            lrc = detail.get("lrc")
            if lrc and isinstance(lrc, str) and lrc.startswith("http"):
                return lrc
        elif platform == "qq":
            # QQ: viplrc field is a lyrics URL
            viplrc = detail.get("viplrc")
            if viplrc and isinstance(viplrc, str) and viplrc.startswith("http"):
                return viplrc
        return ""

    @classmethod
    def _fetch_from_url(cls, url: str) -> str:
        """Fetch lyrics from a URL endpoint."""
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()

            # Check if response is JSON or plain text
            content_type = resp.headers.get("Content-Type", "")
            if "json" in content_type:
                data = resp.json()
                if data.get("code") == 200 and data.get("data"):
                    # API may return 'lyric' or 'lrc'
                    lrc = data["data"].get("lyric") or data["data"].get("lrc", "")
                    if lrc and isinstance(lrc, str):
                        return cls._normalize(lrc)
            else:
                # Plain text lyrics (like QQ viplrc endpoint)
                text = resp.text.strip()
                if text and len(text) > 10:
                    return cls._normalize(text)
        except Exception:
            pass
        return ""

    @classmethod
    def _fetch_from_api(cls, platform: str, song_id: str) -> str:
        """Fetch lyrics from the dedicated lyrics API."""
        lrc_type = LYRICS_TYPE_MAP.get(platform)
        if not lrc_type:
            return ""

        params = {
            "key": API_KEY,
            "mid": song_id,
            "type": lrc_type,
        }

        try:
            resp = requests.get(LYRICS_URL, params=params,
                                headers=MusicAPI.HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") == 200 and data.get("data"):
                # API may return 'lyric' or 'lrc'
                lrc = data["data"].get("lyric") or data["data"].get("lrc", "")
                if lrc and isinstance(lrc, str):
                    return cls._normalize(lrc)
        except Exception:
            pass

        return ""

    @classmethod
    def _normalize(cls, text: str) -> str:
        """Normalize line endings."""
        return text.replace("\r\n", "\n").replace("\r", "\n")
