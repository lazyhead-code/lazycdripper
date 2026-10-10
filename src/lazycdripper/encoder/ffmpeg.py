"""Audio encoding engine utilizing FFmpeg for parallel FLAC and AAC transcoding."""

from concurrent.futures import ThreadPoolExecutor
import logging
from pathlib import Path
import subprocess
from typing import Optional, Tuple
from lazycdripper.core.binaries import find_binary, is_binary_available

logger = logging.getLogger(__name__)


class FFmpegEncoder:
    """Encodes uncompressed PCM WAV audio into FLAC and AAC via FFmpeg."""

    def __init__(self, binary_path: Optional[str] = None):
        self.binary_path = find_binary("ffmpeg", custom_path=binary_path)
        self._has_fdk_aac: Optional[bool] = None

    @property
    def is_available(self) -> bool:
        """Check if FFmpeg binary is accessible and executable."""
        if not is_binary_available(self.binary_path):
            self.binary_path = find_binary("ffmpeg")
        return is_binary_available(self.binary_path)

    def encode_flac(self, input_wav: Path, output_flac: Path) -> bool:
        """
        Transcode WAV to FLAC using maximum compression level 8.
        Command: ffmpeg -y -i <input> -c:a flac -compression_level 8 <output>
        """
        output_flac.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.binary_path,
            "-y",  # Overwrite
            "-i", str(input_wav),
            "-c:a", "flac",
            "-compression_level", "8",
            str(output_flac),
        ]
        return self._run_command(cmd, "FLAC")

    def encode_aac(self, input_wav: Path, output_aac: Path) -> bool:
        """
        Transcode WAV to AAC-LC (.m4a) at 256kbps / VBR 5.
        Prefers Fraunhofer FDK-AAC (libfdk_aac) if compiled into FFmpeg,
        with seamless fallback to FFmpeg's native high-quality AAC encoder.
        """
        output_aac.parent.mkdir(parents=True, exist_ok=True)

        codec_args = (
            ["-c:a", "libfdk_aac", "-vbr", "5"]
            if self.supports_fdk_aac()
            else ["-c:a", "aac", "-b:a", "256k"]
        )

        cmd = [
            self.binary_path,
            "-y",
            "-i", str(input_wav),
            *codec_args,
            str(output_aac),
        ]
        return self._run_command(cmd, "AAC")

    def encode_dual(self, input_wav: Path, output_flac: Path, output_aac: Path) -> Tuple[bool, bool]:
        """
        Transcode input WAV to BOTH FLAC and AAC simultaneously using a thread pool
        to maximize multi-core CPU utilization.
        """
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_flac = executor.submit(self.encode_flac, input_wav, output_flac)
            future_aac = executor.submit(self.encode_aac, input_wav, output_aac)
            flac_ok = future_flac.result()
            aac_ok = future_aac.result()
        return flac_ok, aac_ok

    def supports_fdk_aac(self) -> bool:
        """Test if the installed FFmpeg build includes libfdk_aac."""
        if self._has_fdk_aac is not None:
            return self._has_fdk_aac

        try:
            res = subprocess.run(
                [self.binary_path, "-encoders"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            self._has_fdk_aac = "libfdk_aac" in res.stdout
        except Exception:
            self._has_fdk_aac = False

        return self._has_fdk_aac

    def get_version(self) -> Optional[str]:
        """Return the FFmpeg version string if available (e.g., '7.1')."""
        if not self.is_available:
            return None
        try:
            res = subprocess.run(
                [self.binary_path, "-version"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            import re
            m = re.search(r"ffmpeg version\s+([0-9]+(?:\.[0-9]+)+)", res.stdout)
            if m:
                return m.group(1)
        except Exception:
            pass
        return None

    def _run_command(self, cmd: list, format_label: str) -> bool:
        """Execute ffmpeg subprocess with error logging."""
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if res.returncode == 0:
                return True
            logger.error("FFmpeg %s encode failed: %s", format_label, res.stderr)
            return False
        except Exception as err:
            logger.error("FFmpeg execution error for %s: %s", format_label, err)
            return False


def os_executable(path: Path) -> bool:
    """Check if file has executable permissions."""
    import os
    return os.access(path, os.X_OK)


class MockEncoder:
    """Mock encoder for automated testing and CI where FFmpeg is not installed."""

    def __init__(self):
        self.is_available = True

    def encode_flac(self, input_wav: Path, output_flac: Path) -> bool:
        output_flac.parent.mkdir(parents=True, exist_ok=True)
        # Create mock FLAC container file
        with open(output_flac, "wb") as f:
            f.write(b"fLaC" + b"\x00" * 8192)
        return True

    def encode_aac(self, input_wav: Path, output_aac: Path) -> bool:
        output_aac.parent.mkdir(parents=True, exist_ok=True)
        # Create mock M4A / MP4 container file
        with open(output_aac, "wb") as f:
            f.write(b"\x00\x00\x00 ftypM4A \x00\x00\x00\x00M4A mp42isom" + b"\x00" * 8192)
        return True

    def encode_dual(self, input_wav: Path, output_flac: Path, output_aac: Path) -> Tuple[bool, bool]:
        return self.encode_flac(input_wav, output_flac), self.encode_aac(input_wav, output_aac)
