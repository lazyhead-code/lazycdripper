"""Audio encoding subsystem handling FLAC and MP3 transcoding via standalone FLAC/LAME binaries or FFmpeg fallback."""

from lazycdripper.encoder.ffmpeg import AudioEncoder, FFmpegEncoder, MockEncoder

__all__ = [
    "AudioEncoder",
    "FFmpegEncoder",
    "MockEncoder",
]
