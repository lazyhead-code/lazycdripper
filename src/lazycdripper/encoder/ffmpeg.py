"""Audio encoding engine utilizing standalone FLAC/LAME binaries or FFmpeg fallback for parallel transcoding."""

from concurrent.futures import ThreadPoolExecutor
import logging
import os
from pathlib import Path
import re
import subprocess
from typing import Optional, Tuple
from lazycdripper.core.binaries import find_binary, is_binary_available

logger = logging.getLogger(__name__)


class FFmpegEncoder:
    """Encodes uncompressed PCM WAV audio into FLAC and MP3 via standalone binaries (FLAC/LAME) or FFmpeg fallback."""

    def __init__(
        self,
        binary_path: Optional[str] = None,
        flac_path: Optional[str] = None,
        lame_path: Optional[str] = None,
    ):
        self.flac_binary = find_binary("flac", custom_path=flac_path)
        self.lame_binary = find_binary("lame", custom_path=lame_path)
        self.ffmpeg_binary = find_binary("ffmpeg", custom_path=binary_path)
        # Retain self.binary_path as backward-compatible alias to ffmpeg_binary
        self.binary_path = self.ffmpeg_binary
        self._has_fdk_aac: Optional[bool] = None

    @property
    def has_standalone_encoders(self) -> bool:
        """Check if official standalone FLAC and LAME binaries are present and executable."""
        return is_binary_available(self.flac_binary) and is_binary_available(self.lame_binary)

    @property
    def is_available(self) -> bool:
        """Check if standalone encoders or FFmpeg binary are accessible and executable."""
        if not is_binary_available(self.flac_binary):
            self.flac_binary = find_binary("flac")
        if not is_binary_available(self.lame_binary):
            self.lame_binary = find_binary("lame")
        if not is_binary_available(self.ffmpeg_binary):
            self.ffmpeg_binary = find_binary("ffmpeg")
            self.binary_path = self.ffmpeg_binary

        return self.has_standalone_encoders or is_binary_available(self.ffmpeg_binary)

    def encode_flac(self, input_wav: Path, output_flac: Path) -> bool:
        """
        Transcode WAV to FLAC using maximum compression level 8 with MD5 stream verification.
        Uses standalone flac binary if available, otherwise falls back to FFmpeg.
        """
        output_flac.parent.mkdir(parents=True, exist_ok=True)
        if is_binary_available(self.flac_binary):
            cmd = [
                self.flac_binary,
                "-8",
                "--verify",
                "-f",
                str(input_wav),
                "-o",
                str(output_flac),
            ]
            return self._run_command(cmd, "FLAC (flac)")
        elif is_binary_available(self.ffmpeg_binary):
            cmd = [
                self.ffmpeg_binary,
                "-y",
                "-i", str(input_wav),
                "-c:a", "flac",
                "-compression_level", "8",
                str(output_flac),
            ]
            return self._run_command(cmd, "FLAC (ffmpeg)")
        else:
            logger.error("No FLAC encoder available (neither flac nor ffmpeg found)")
            return False

    def encode_mp3(self, input_wav: Path, output_mp3: Path) -> bool:
        """
        Transcode WAV to MP3 at CBR 320 kbps with highest quality psychoacoustic model (-q 0).
        Uses standalone lame binary if available, otherwise falls back to FFmpeg libmp3lame.
        """
        output_mp3.parent.mkdir(parents=True, exist_ok=True)
        if is_binary_available(self.lame_binary):
            cmd = [
                self.lame_binary,
                "-b", "320",
                "-q", "0",
                str(input_wav),
                str(output_mp3),
            ]
            return self._run_command(cmd, "MP3 (lame)")
        elif is_binary_available(self.ffmpeg_binary):
            cmd = [
                self.ffmpeg_binary,
                "-y",
                "-i", str(input_wav),
                "-c:a", "libmp3lame",
                "-b:a", "320k",
                "-q:a", "0",
                str(output_mp3),
            ]
            return self._run_command(cmd, "MP3 (ffmpeg)")
        else:
            logger.error("No MP3 encoder available (neither lame nor ffmpeg found)")
            return False

    def encode_aac(self, input_wav: Path, output_aac: Path) -> bool:
        """
        Transcode WAV to AAC-LC (.m4a) at 256kbps / VBR 5 (legacy fallback via FFmpeg).
        """
        output_aac.parent.mkdir(parents=True, exist_ok=True)

        codec_args = (
            ["-c:a", "libfdk_aac", "-vbr", "5"]
            if self.supports_fdk_aac()
            else ["-c:a", "aac", "-b:a", "256k"]
        )

        cmd = [
            self.ffmpeg_binary,
            "-y",
            "-i", str(input_wav),
            *codec_args,
            str(output_aac),
        ]
        return self._run_command(cmd, "AAC")

    def encode_dual(self, input_wav: Path, output_flac: Path, output_lossy: Path) -> Tuple[bool, bool]:
        """
        Transcode input WAV to BOTH FLAC and MP3 (or AAC) simultaneously using a thread pool
        to maximize multi-core CPU utilization.
        """
        lossy_func = self.encode_aac if output_lossy.suffix.lower() == ".m4a" else self.encode_mp3
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_flac = executor.submit(self.encode_flac, input_wav, output_flac)
            future_lossy = executor.submit(lossy_func, input_wav, output_lossy)
            flac_ok = future_flac.result()
            lossy_ok = future_lossy.result()
        return flac_ok, lossy_ok

    def supports_fdk_aac(self) -> bool:
        """Test if the installed FFmpeg build includes libfdk_aac."""
        if self._has_fdk_aac is not None:
            return self._has_fdk_aac

        try:
            creationflags = 0x08000000 if os.name == "nt" else 0
            res = subprocess.run(
                [self.ffmpeg_binary, "-encoders"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                creationflags=creationflags,
            )
            self._has_fdk_aac = "libfdk_aac" in res.stdout
        except Exception:
            self._has_fdk_aac = False

        return self._has_fdk_aac

    def get_version(self) -> Optional[str]:
        """Return version string for available encoders."""
        creationflags = 0x08000000 if os.name == "nt" else 0
        if is_binary_available(self.lame_binary):
            try:
                res = subprocess.run(
                    [self.lame_binary, "--version"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=3,
                    creationflags=creationflags,
                )
                m = re.search(r"LAME(?: 64bits)? version\s+([0-9]+(?:\.[0-9]+)+)", res.stdout)
                if m:
                    return f"LAME {m.group(1)}"
            except Exception:
                pass

        if is_binary_available(self.ffmpeg_binary):
            try:
                res = subprocess.run(
                    [self.ffmpeg_binary, "-version"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=3,
                    creationflags=creationflags,
                )
                m = re.search(r"ffmpeg version\s+([0-9]+(?:\.[0-9]+)+)", res.stdout)
                if m:
                    return f"FFmpeg {m.group(1)}"
            except Exception:
                pass
        return None

    def _run_command(self, cmd: list, format_label: str) -> bool:
        """Execute encoder subprocess with CREATE_NO_WINDOW on Windows and error logging."""
        try:
            creationflags = 0x08000000 if os.name == "nt" else 0
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                creationflags=creationflags,
            )
            if res.returncode == 0:
                return True
            logger.error("Encoder %s encode failed (code %d): %s", format_label, res.returncode, res.stderr)
            return False
        except Exception as err:
            logger.error("Encoder execution error for %s: %s", format_label, err)
            return False


AudioEncoder = FFmpegEncoder


class MockEncoder:
    """Mock encoder for automated testing and CI where external binaries are not installed."""

    def __init__(self):
        self.is_available = True

    def encode_flac(self, input_wav: Path, output_flac: Path) -> bool:
        output_flac.parent.mkdir(parents=True, exist_ok=True)
        with open(output_flac, "wb") as f:
            f.write(b"fLaC" + b"\x00" * 8192)
        return True

    def encode_mp3(self, input_wav: Path, output_mp3: Path) -> bool:
        output_mp3.parent.mkdir(parents=True, exist_ok=True)
        with open(output_mp3, "wb") as f:
            f.write(b"ID3\x03\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x00" + b"\x00" * 8192)
        return True

    def encode_aac(self, input_wav: Path, output_aac: Path) -> bool:
        output_aac.parent.mkdir(parents=True, exist_ok=True)
        with open(output_aac, "wb") as f:
            f.write(b"\x00\x00\x00 ftypM4A \x00\x00\x00\x00M4A mp42isom" + b"\x00" * 8192)
        return True

    def encode_dual(self, input_wav: Path, output_flac: Path, output_lossy: Path) -> Tuple[bool, bool]:
        if output_lossy.suffix.lower() == ".m4a":
            return self.encode_flac(input_wav, output_flac), self.encode_aac(input_wav, output_lossy)
        return self.encode_flac(input_wav, output_flac), self.encode_mp3(input_wav, output_lossy)
