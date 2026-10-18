"""Audio encoding subsystem handling FLAC and MP3 transcoding via standalone FLAC and LAME binaries."""

from lazycdripper.encoder.encoder import AudioEncoder, MockEncoder

__all__ = [
    "AudioEncoder",
    "MockEncoder",
]
