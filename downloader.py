import os
import requests
from api_client import MusicAPI
from lyrics import LyricsFetcher
from tagger import MetadataManager
from config import QUALITY_FALLBACK


class MusicDownloader:
    """Download music with quality fallback and embed metadata."""

    @classmethod
    def download(cls, platform: str, song_index: int, keyword: str,
                 save_dir: str = "./downloads", show_progress: bool = True,
                 song_mid: str = None) -> str:
        """
        Search, get song detail, download with quality fallback, tag metadata.
        Returns the path to the downloaded file.
        """
        os.makedirs(save_dir, exist_ok=True)

        # Step 1: Get song detail with highest quality
        detail = cls._fetch_with_quality_fallback(platform, song_index, keyword)

        # Step 2: Extract info
        song_url = MusicAPI.get_song_url(platform, detail)
        if not song_url:
            raise Exception("Failed to get music download URL")

        song_info = MusicAPI.get_song_info_for_tagging(platform, detail)
        cover_url = MusicAPI.get_cover_url(platform, detail)

        # Step 3: Fetch lyrics
        # Use song_mid from search results if available (important for QQ/Kuwo)
        song_id = song_mid or detail.get("mid") or detail.get("rid") or detail.get("n")
        lyrics = LyricsFetcher.fetch(platform, song_id=str(song_id) if song_id else None,
                                     detail=detail)

        # Step 4: Determine file extension from URL or default
        ext = cls._get_file_ext(song_url, platform, detail)

        # Step 5: Build filename
        safe_title = cls._sanitize_filename(song_info["title"])
        safe_artist = cls._sanitize_filename(song_info["artist"])
        filename = f"{safe_artist} - {safe_title}{ext}"
        file_path = os.path.join(save_dir, filename)

        # Step 6: Download the audio file
        if show_progress:
            print(f"  正在下载: {filename}")
        cls._download_file(song_url, file_path, show_progress)

        # Step 7: Add metadata via MetadataManager
        if show_progress:
            print("  正在写入元数据（歌词、封面等）...")
        metadata_mgr = MetadataManager()
        metadata_mgr.add_metadata(
            file_path=file_path,
            title=song_info["title"],
            artist=song_info["artist"],
            album=song_info["album"],
            lyrics=lyrics,
            cover_url=cover_url,
        )

        if show_progress:
            print(f"  下载完成: {file_path}")

        return file_path

    @classmethod
    def _fetch_with_quality_fallback(cls, platform: str, song_index: int,
                                     keyword: str) -> dict:
        """
        Try to get song detail with highest quality.
        If it fails, recursively try next quality level.
        """
        qualities = QUALITY_FALLBACK.get(platform, [])

        if not qualities:
            # Platform doesn't support quality selection (wy, apple)
            return MusicAPI.get_song_detail(platform, song_index, keyword)

        last_error = None
        for quality in qualities:
            try:
                detail = MusicAPI.get_song_detail(
                    platform, song_index, keyword, quality=quality
                )
                url = MusicAPI.get_song_url(platform, detail)
                if url:
                    return detail
            except Exception as e:
                last_error = e
                continue

        # All qualities failed, try without quality param
        try:
            return MusicAPI.get_song_detail(platform, song_index, keyword)
        except Exception:
            raise last_error or Exception("All quality levels failed")

    @classmethod
    def _download_file(cls, url: str, file_path: str, show_progress: bool = True):
        """Download a file with optional progress indicator."""
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()

        total_size = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(file_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if show_progress and total_size > 0:
                        percent = downloaded / total_size * 100
                        print(f"\r  进度: {percent:.1f}%", end="", flush=True)

        if show_progress:
            print()  # New line after progress

    @classmethod
    def _get_file_ext(cls, url: str, platform: str, detail: dict) -> str:
        """Determine file extension from URL or detail."""
        # Try to extract from URL
        for ext in [".flac", ".mp3", ".m4a", ".ogg", ".wav", ".aac"]:
            if ext in url.lower():
                return ext

        # Try from detail
        if platform == "kg" and detail.get("ext_name"):
            ext_name = detail["ext_name"].lower()
            if ext_name in ("flac", "mp3", "m4a"):
                return f".{ext_name}"

        if platform == "kw" and isinstance(detail.get("vipmusic"), dict):
            fmt = detail["vipmusic"].get("format", "").lower()
            if fmt in ("flac", "mp3", "m4a"):
                return f".{fmt}"

        # Default: try to detect from platform
        if platform == "apple":
            return ".m4a"
        if platform == "qq":
            return ".m4a"

        return ".mp3"

    @classmethod
    def _sanitize_filename(cls, name: str) -> str:
        """Remove characters that are invalid in filenames."""
        for ch in r'<>:"/\|?*':
            name = name.replace(ch, "")
        return name.strip()
