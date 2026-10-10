"""Optical disc detection and Table of Contents (TOC) reading subsystem."""

from lazycdripper.disc.drive import (
    DriveInfo,
    detect_optical_drives,
    get_default_optical_drive,
)
from lazycdripper.disc.toc import (
    DiscTOC,
    TrackTOC,
    calculate_musicbrainz_discid,
    parse_cdparanoia_toc_output,
)

__all__ = [
    "DriveInfo",
    "detect_optical_drives",
    "get_default_optical_drive",
    "DiscTOC",
    "TrackTOC",
    "calculate_musicbrainz_discid",
    "parse_cdparanoia_toc_output",
]
