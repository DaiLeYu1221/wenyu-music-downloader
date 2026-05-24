import os
import requests
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, APIC, USLT
from mutagen.mp3 import MP3
from mutagen import File


class MetadataManager:
    """Manage metadata writing for audio files (FLAC, MP3, M4A)."""

    def add_metadata(self, file_path: str, title: str, artist: str, album: str,
                     lyrics: str = "", cover_url: str = ""):
        """
        Add metadata to an audio file. Dispatches based on extension.
        """
        ext = os.path.splitext(file_path)[1].lower()
        cover_data = self._download_cover(cover_url) if cover_url else None

        if ext == ".flac":
            self._add_metadata_to_flac(file_path, title, artist, album, lyrics, cover_data)
        elif ext == ".mp3":
            self._add_metadata_to_mp3(file_path, title, artist, album, lyrics, cover_data)
        elif ext in (".m4a", ".mp4", ".aac"):
            self._add_metadata_to_m4a(file_path, title, artist, album, lyrics, cover_data)
        else:
            self._add_metadata_generic(file_path, title, artist, album, lyrics)

    # ---- FLAC ----

    def _add_metadata_to_flac(self, file_path, title, artist, album, lyrics, cover_data):
        audio = FLAC(file_path)

        # Clear old tags to avoid duplicates
        audio.delete()

        # Basic metadata
        audio["title"] = title
        audio["artist"] = artist
        audio["album"] = album

        # Lyrics
        if lyrics:
            audio["lyrics"] = lyrics

        # Cover
        if cover_data:
            image = Picture()
            image.type = 3  # Front cover
            image.mime = self._detect_mime_type(cover_data)
            image.desc = "Cover"
            image.data = cover_data
            audio.add_picture(image)

        audio.save()

    # ---- MP3 ----

    def _add_metadata_to_mp3(self, file_path, title, artist, album, lyrics, cover_data):
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()

        # Clear old tags
        audio.delete(file_path)

        # Basic metadata (encoding=3 means UTF-8)
        audio.add(TIT2(encoding=3, text=title))
        audio.add(TPE1(encoding=3, text=artist))
        audio.add(TALB(encoding=3, text=album))

        # Lyrics
        if lyrics:
            audio.add(USLT(encoding=3, lang="chi", desc="Lyrics", text=lyrics))

        # Cover
        if cover_data:
            audio.add(APIC(
                encoding=3,
                mime=self._detect_mime_type(cover_data),
                type=3,
                desc="Cover",
                data=cover_data
            ))

        # Save as ID3v2.3 for maximum player compatibility
        audio.save(file_path, v2_version=3)

    # ---- M4A / MP4 ----

    def _add_metadata_to_m4a(self, file_path, title, artist, album, lyrics, cover_data):
        audio = MP4(file_path)

        # Basic metadata
        audio["\xa9nam"] = [title]
        audio["\xa9ART"] = [artist]
        audio["\xa9alb"] = [album]

        # Lyrics
        if lyrics:
            audio["\xa9lyr"] = [lyrics]

        # Cover
        if cover_data:
            audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]

        audio.save()

    # ---- Generic fallback ----

    def _add_metadata_generic(self, file_path, title, artist, album, lyrics):
        try:
            audio = File(file_path, easy=True)
            if audio is not None:
                audio["title"] = [title]
                audio["artist"] = [artist]
                audio["album"] = [album]
                if lyrics:
                    audio["lyrics"] = [lyrics]
                audio.save()
        except Exception:
            pass

    # ---- Helpers ----

    def _download_cover(self, url: str) -> bytes:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return resp.content
        except Exception:
            return None

    @staticmethod
    def _detect_mime_type(data: bytes) -> str:
        """Detect image MIME type from magic bytes."""
        if data[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "image/webp"
        return "image/jpeg"  # default
