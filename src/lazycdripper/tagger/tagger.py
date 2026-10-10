"""Audio tagging engine handling Vorbis comments, MP4 atoms, and artwork embedding."""

import logging
from pathlib import Path
import shutil
from typing import Optional
from lazycdripper.core.models import AlbumInfo, AudioFormat, TrackInfo

logger = logging.getLogger(__name__)


class AudioTagger:
    """Writes metadata and embeds cover art into FLAC and AAC audio files."""

    def __init__(self):
        self._has_mutagen: Optional[bool] = None

    @property
    def has_mutagen(self) -> bool:
        """Check if the mutagen library is installed and available."""
        if self._has_mutagen is None:
            try:
                import mutagen
                self._has_mutagen = True
            except ImportError:
                self._has_mutagen = False
        return self._has_mutagen

    def tag_track(
        self,
        file_path: Path,
        track: TrackInfo,
        album: AlbumInfo,
        audio_format: AudioFormat,
        cover_image_path: Optional[Path] = None,
    ) -> bool:
        """Tag an audio file with full metadata and optional embedded cover art."""
        if not file_path.exists():
            logger.error("Target file does not exist: %s", file_path)
            return False

        if not self.has_mutagen:
            logger.debug("Mutagen not installed; skipping tag injection for %s", file_path)
            return True

        if audio_format == AudioFormat.FLAC:
            return self._tag_flac(file_path, track, album, cover_image_path)
        elif audio_format == AudioFormat.AAC:
            return self._tag_m4a(file_path, track, album, cover_image_path)
        return False

    def _tag_flac(
        self,
        file_path: Path,
        track: TrackInfo,
        album: AlbumInfo,
        cover_image_path: Optional[Path] = None,
    ) -> bool:
        """Inject Vorbis comments and embedded picture block into a .flac file."""
        try:
            from mutagen.flac import FLAC, Picture

            audio = FLAC(str(file_path))
            audio["TITLE"] = track.title
            audio["ARTIST"] = track.artist
            audio["ALBUM"] = album.title
            audio["ALBUMARTIST"] = album.album_artist or album.artist
            audio["TRACKNUMBER"] = str(track.track_number)
            audio["TRACKTOTAL"] = str(album.total_tracks or len(album.tracks))
            audio["DISCNUMBER"] = str(track.disc_number)
            audio["DISCTOTAL"] = str(album.total_discs)

            if album.year:
                audio["DATE"] = str(album.year)
            if album.genre:
                audio["GENRE"] = album.genre
            if album.disc_id:
                audio["MUSICBRAINZ_DISCID"] = album.disc_id

            # Embed cover art if provided
            if cover_image_path and cover_image_path.exists():
                image_data = cover_image_path.read_bytes()
                pic = Picture()
                pic.type = 3  # Front cover
                pic.mime = "image/jpeg"
                pic.desc = "Front Cover"
                pic.data = image_data
                audio.clear_pictures()
                audio.add_picture(pic)

            audio.save()
            return True
        except Exception as err:
            logger.error("Failed to tag FLAC file %s: %s", file_path, err)
            return False

    def _tag_m4a(
        self,
        file_path: Path,
        track: TrackInfo,
        album: AlbumInfo,
        cover_image_path: Optional[Path] = None,
    ) -> bool:
        """Inject MP4 atoms and cover art into an .m4a container."""
        try:
            from mutagen.mp4 import MP4, MP4Cover

            audio = MP4(str(file_path))
            audio["\xa9nam"] = [track.title]
            audio["\xa9ART"] = [track.artist]
            audio["\xa9alb"] = [album.title]
            audio["aART"] = [album.album_artist or album.artist]
            audio["trkn"] = [(track.track_number, album.total_tracks or len(album.tracks))]
            audio["disk"] = [(track.disc_number, album.total_discs)]

            if album.year:
                audio["\xa9day"] = [str(album.year)]
            if album.genre:
                audio["\xa9gen"] = [album.genre]

            # Embed cover art
            if cover_image_path and cover_image_path.exists():
                image_data = cover_image_path.read_bytes()
                audio["covr"] = [MP4Cover(image_data, imageformat=MP4Cover.FORMAT_JPEG)]

            audio.save()
            return True
        except Exception as err:
            logger.error("Failed to tag AAC/M4A file %s: %s", file_path, err)
            return False

    def save_companion_cover(self, album_dir: Path, source_cover_path: Path) -> Optional[Path]:
        """Save companion cover.jpg in the destination album directory."""
        if not source_cover_path or not source_cover_path.exists():
            return None

        album_dir.mkdir(parents=True, exist_ok=True)
        target = album_dir / "cover.jpg"
        shutil.copyfile(source_cover_path, target)
        return target
