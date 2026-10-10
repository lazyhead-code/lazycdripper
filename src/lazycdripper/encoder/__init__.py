"""Audio encoding subsystem handling FLAC and AAC transcoding via FFmpeg."""

from lazycdripper.encoder.ffmpeg import FFmpegEncoder, MockEncoder

__all__ = [
    "FFmpegEncoder",
    "MockEncoder",
]
