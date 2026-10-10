"""Filesystem path and filename sanitization utilities."""

import re
from pathlib import Path
from typing import Optional
from lazycdripper.core.models import AudioFormat

# Reserved filenames on Windows (regardless of extension)
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str, fallback: str = "Unknown") -> str:
    """
    Sanitize a filename component by removing illegal filesystem characters,
    stripping leading/trailing spaces and dots, and handling Windows reserved words.
    Preserves natural hyphens in artist names, album titles, and hyphenated words.
    """
    if not name or not name.strip():
        return fallback

    # Replace directory separators (/ and \) with a hyphen
    clean = re.sub(r'[/\\]', '-', name)
    # Replace colons and pipe characters with ' - '
    clean = re.sub(r'[:|]', ' - ', clean)

    # Remove characters that are strictly forbidden on Windows/Unix (< > " ? * and control chars)
    clean = re.sub(r'[<>"?*\x00-\x1f]', '', clean)

    # Collapse multiple whitespace
    clean = re.sub(r'\s+', ' ', clean)

    # Collapse multiple consecutive hyphens (e.g. ' - - ' -> ' - ', '--' -> '-')
    clean = re.sub(r'(\s*-\s*){2,}', ' - ', clean)

    # Strip leading/trailing spaces, hyphens, and periods
    clean = clean.strip(" .-")

    if not clean:
        return fallback

    # Check for Windows reserved names
    name_upper = clean.upper()
    if name_upper in WINDOWS_RESERVED_NAMES:
        clean = f"{clean}_"

    return clean


def format_album_directory_name(
    artist: str,
    album: str,
    year: Optional[int],
    audio_format: AudioFormat,
) -> str:
    """
    Format opinionated album folder name:
    '<Artist> - <Album> (<Year>) [<FORMAT>]' or '<Artist> - <Album> [<FORMAT>]'
    """
    clean_artist = sanitize_filename(artist, fallback="Unknown Artist")
    clean_album = sanitize_filename(album, fallback="Unknown Album")
    format_tag = audio_format.value.upper()

    if year and year > 0:
        return f"{clean_artist} - {clean_album} ({year}) [{format_tag}]"
    return f"{clean_artist} - {clean_album} [{format_tag}]"


def format_track_filename(
    track_number: int,
    title: str,
    audio_format: AudioFormat,
    include_track_number: bool = True,
    include_artist: bool = False,
    artist: Optional[str] = None,
) -> str:
    """
    Format track filename based on user options:
    - Default (number=True, artist=False): '01 - <Track Title>.<ext>'
    - With artist (number=True, artist=True): '01 - <Artist> - <Track Title>.<ext>'
    - Artist only (number=False, artist=True): '<Artist> - <Track Title>.<ext>'
    - Title only (number=False, artist=False): '<Track Title>.<ext>'
    """
    clean_title = sanitize_filename(title, fallback="Track")
    ext = "flac" if audio_format == AudioFormat.FLAC else "m4a"

    parts = []
    if include_track_number:
        parts.append(f"{track_number:02d}")
    if include_artist and artist:
        clean_artist = sanitize_filename(artist, fallback="")
        if clean_artist:
            parts.append(clean_artist)
    parts.append(clean_title)

    filename = " - ".join(parts) if parts else clean_title
    return f"{filename}.{ext}"


def get_target_track_path(
    base_output_dir: Path,
    artist: str,
    album: str,
    year: Optional[int],
    audio_format: AudioFormat,
    track_number: int,
    track_title: str,
    disc_number: int = 1,
    total_discs: int = 1,
    include_track_number: bool = True,
    include_artist: bool = False,
    track_artist: Optional[str] = None,
) -> Path:
    """
    Construct the full destination path for a given track, automatically handling
    multi-disc subfolders when total_discs > 1.
    """
    album_dir_name = format_album_directory_name(artist, album, year, audio_format)
    album_path = base_output_dir / album_dir_name

    if total_discs > 1:
        album_path = album_path / f"Disc {disc_number:02d}"

    filename = format_track_filename(
        track_number=track_number,
        title=track_title,
        audio_format=audio_format,
        include_track_number=include_track_number,
        include_artist=include_artist,
        artist=track_artist or artist,
    )
    return album_path / filename


def generate_naming_preview(
    artist: str = "Pink Floyd",
    album: str = "The Dark Side of the Moon",
    year: int = 1973,
    track_number: int = 1,
    track_title: str = "Speak to Me",
    audio_format: AudioFormat = AudioFormat.FLAC,
    include_track_number: bool = True,
    include_artist: bool = False,
    track_artist: Optional[str] = None,
) -> str:
    """
    Generate a formatted preview string for the UI live-preview box:
    'Pink Floyd - The Dark Side of the Moon (1973) [FLAC] / 01 - Speak to Me.flac'
    """
    folder = format_album_directory_name(artist, album, year, audio_format)
    effective_artist = track_artist or artist
    track_file = format_track_filename(
        track_number=track_number,
        title=track_title,
        audio_format=audio_format,
        include_track_number=include_track_number,
        include_artist=include_artist,
        artist=effective_artist,
    )
    return f"{folder}/{track_file}"
