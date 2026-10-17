"""Core domain data models for Lazy CD Ripper."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class AudioFormat(str, Enum):
    """Supported target audio encoding formats."""
    FLAC = "flac"
    AAC = "aac"


@dataclass
class ArtworkCandidate:
    """Represents an album artwork image candidate retrieved from Cover Art Archive."""
    image_id: str
    url: str
    thumbnail_url: str = ""
    is_front: bool = True
    width: Optional[int] = None
    height: Optional[int] = None
    comment: str = ""
    local_cache_path: Optional[Path] = None
    types: List[str] = field(default_factory=list)
    source: str = "release"  # "release_group" or "release"


@dataclass
class TrackInfo:
    """Metadata and timing information for an individual audio CD track."""
    track_number: int
    title: str
    artist: str
    duration_seconds: float = 0.0
    disc_number: int = 1
    genre: Optional[str] = None


@dataclass
class AlbumInfo:
    """Complete metadata for an audio CD release."""
    title: str
    artist: str
    album_artist: str = ""
    year: Optional[int] = None
    total_tracks: int = 0
    disc_number: int = 1
    total_discs: int = 1
    disc_id: str = ""
    musicbrainz_release_id: str = ""
    musicbrainz_release_group_id: Optional[str] = None
    genre: Optional[str] = None
    tracks: List[TrackInfo] = field(default_factory=list)
    artwork_candidates: List[ArtworkCandidate] = field(default_factory=list)
    selected_artwork: Optional[ArtworkCandidate] = None

    def __post_init__(self) -> None:
        if not self.album_artist and self.artist:
            self.album_artist = self.artist


@dataclass
class RipProgress:
    """Real-time progress reporting during ripping and encoding."""
    current_track: int
    total_tracks: int
    track_percent: float = 0.0
    overall_percent: float = 0.0
    status_message: str = ""
    current_speed: str = ""
    jitter_corrections: int = 0
    read_retries: int = 0
    unrecoverable_errors: int = 0
    track_title: str = ""


@dataclass
class TrackRipReport:
    """Audit report for an individual ripped track."""
    track_number: int
    title: str
    status: str = "pristine"  # "pristine", "recovered", "damaged", "failed"
    jitter_corrections: int = 0
    read_retries: int = 0
    unrecoverable_errors: int = 0
    flac_path: Optional[Path] = None
    aac_path: Optional[Path] = None
    read_errors: Optional[int] = None

    def __post_init__(self) -> None:
        if self.read_errors is not None and self.unrecoverable_errors == 0:
            self.unrecoverable_errors = self.read_errors
        elif self.read_errors is None:
            self.read_errors = self.unrecoverable_errors


@dataclass
class AlbumRipReport:
    """
    Comprehensive post-rip audit and integrity report presented to the user
    confirming bit-perfection or identifying surface defects.
    """
    album_title: str
    artist: str
    year: Optional[int] = None
    total_tracks: int = 0
    overall_status: str = "pristine"  # "pristine", "recovered", "damaged", "failed"
    total_jitter: int = 0
    total_retries: int = 0
    total_errors: int = 0
    duration_seconds: float = 0.0
    destination_directory: Optional[Path] = None
    flac_directory: Optional[Path] = None
    aac_directory: Optional[Path] = None
    flac_size_bytes: int = 0
    aac_size_bytes: int = 0
    track_reports: List[TrackRipReport] = field(default_factory=list)

    @property
    def rip_folder(self) -> Optional[Path]:
        """Parent directory containing the ripped FLAC and AAC libraries."""
        if self.destination_directory and self.destination_directory.exists():
            return self.destination_directory
        if self.flac_directory and self.flac_directory.parent.exists():
            return self.flac_directory.parent
        if self.aac_directory and self.aac_directory.parent.exists():
            return self.aac_directory.parent
        return None

    @property
    def successful_tracks_count(self) -> int:
        """Count of tracks that were successfully extracted and encoded to FLAC."""
        if not self.track_reports:
            return 0 if self.overall_status == "failed" else self.total_tracks
        return sum(
            1 for t in self.track_reports
            if t.status != "failed" and (t.flac_path is None or t.flac_path.exists())
        )

    @property
    def is_perfect(self) -> bool:
        """True if every track was extracted on the first pass with zero retries or errors."""
        if self.total_errors > 0 or self.total_retries > 0:
            return False
        if self.overall_status != "pristine":
            return False
        if self.total_tracks > 0 and self.track_reports:
            return (
                len(self.track_reports) == self.total_tracks
                and self.successful_tracks_count == self.total_tracks
            )
        return self.total_errors == 0 and self.total_retries == 0

    @property
    def summary_headline(self) -> str:
        """User-facing headline badge for the post-rip completion popup."""
        if self.overall_status == "failed" or (self.track_reports and self.successful_tracks_count == 0):
            return "🔴 Extraction Failed — Drive Read Error"
        elif self.is_perfect:
            return "🟢 Rip Complete"
        elif self.total_errors == 0:
            return "🟡 Recovered With Multi-Pass Correction"
        else:
            return "🔴 Surface Damage Detected"

    @property
    def clean_headline(self) -> str:
        """Headline status title text without emoji prefix."""
        headline = self.summary_headline
        for prefix in ("🔴 ", "🟢 ", "🟡 "):
            if headline.startswith(prefix):
                return headline[len(prefix):]
        return headline

    @property
    def human_readable_summary(self) -> str:
        """Formatted human-readable explanation of rip results as concise bullet points."""
        mins = int(self.duration_seconds // 60)
        secs = int(self.duration_seconds % 60)
        time_part = f" ({mins}m {secs}s)" if self.duration_seconds > 0 else ""

        if self.overall_status == "failed" or (self.track_reports and self.successful_tracks_count == 0):
            err_count = self.total_errors if self.total_errors > 0 else "hardware"
            return (
                f"•  Failed to extract audio tracks from optical disc\n"
                f"•  Drive encountered {err_count} unrecoverable read error(s)"
            )
        elif self.is_perfect:
            return (
                f"•  Tracks Extracted: {self.successful_tracks_count}/{self.total_tracks}{time_part}\n"
                f"•  100% bit-perfect accuracy (0 read errors)"
            )
        elif self.total_errors == 0:
            return (
                f"•  Tracks Extracted: {self.successful_tracks_count}/{self.total_tracks}{time_part}\n"
                f"•  Sector Retries: {self.total_retries} recovered with zero data loss"
            )
        else:
            bullets = [f"•  Tracks Extracted: {self.successful_tracks_count}/{self.total_tracks}{time_part}"]
            if self.total_retries > 0:
                bullets.append(f"•  Sector Retries: {self.total_retries} recovered")
            bullets.append(f"•  Unrecoverable Skips: {self.total_errors} sector(s)")
            return "\n".join(bullets)
