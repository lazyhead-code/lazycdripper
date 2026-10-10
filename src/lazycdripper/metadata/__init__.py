"""MusicBrainz and Cover Art Archive metadata fetching subsystem."""

from lazycdripper.metadata.coverart import CoverArtClient
from lazycdripper.metadata.musicbrainz import MusicBrainzClient
from lazycdripper.metadata.service import MetadataService

__all__ = [
    "CoverArtClient",
    "MusicBrainzClient",
    "MetadataService",
]
