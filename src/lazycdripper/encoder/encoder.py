"""Audio encoding engine utilizing standalone FLAC and LAME binaries for parallel transcoding."""

from concurrent.futures import ThreadPoolExecutor
import logging
import os
from pathlib import Path
import re
import subprocess
from typing import Optional, Tuple
from lazycdripper.core.binaries import find_binary, is_binary_available

logger = logging.getLogger(__name__)


class AudioEncoder:
    """Encodes uncompressed PCM WAV audio into FLAC and MP3 via standalone binaries (FLAC and LAME)."""

    def __init__(
        self,
        flac_path: Optional[str] = None,
        lame_path: Optional[str] = None,
    ):
        self.flac_binary = find_binary("flac", custom_path=flac_path)
        self.lame_binary = find_binary("lame", custom_path=lame_path)

    @property
    def is_available(self) -> bool:
        """Check if both standalone FLAC and LAME binaries are accessible and executable."""
        if not is_binary_available(self.flac_binary):
            self.flac_binary = find_binary("flac")
        if not is_binary_available(self.lame_binary):
            self.lame_binary = find_binary("lame")

        return is_binary_available(self.flac_binary) and is_binary_available(self.lame_binary)

    def encode_flac(self, input_wav: Path, output_flac: Path) -> bool:
        """
        Transcode WAV to FLAC using maximum compression level 8 with MD5 stream verification.
        Uses the official standalone flac binary.
        """
        output_flac.parent.mkdir(parents=True, exist_ok=True)
        if not is_binary_available(self.flac_binary):
            self.flac_binary = find_binary("flac")

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
            return self._run_command(cmd, "FLAC")
        else:
            logger.error("No FLAC encoder available (flac binary not found)")
            return False

    def encode_mp3(self, input_wav: Path, output_mp3: Path) -> bool:
        """
        Transcode WAV to MP3 at CBR 320 kbps with highest quality psychoacoustic model (-q 0).
        Uses the official standalone lame binary.
        """
        output_mp3.parent.mkdir(parents=True, exist_ok=True)
        if not is_binary_available(self.lame_binary):
            self.lame_binary = find_binary("lame")

        if is_binary_available(self.lame_binary):
            cmd = [
                self.lame_binary,
                "-b", "320",
                "-q", "0",
                str(input_wav),
                str(output_mp3),
            ]
            return self._run_command(cmd, "MP3")
        else:
            logger.error("No MP3 encoder available (lame binary not found)")
            return False

    def encode_dual(
        self,
        input_wav: Path,
        output_flac: Path,
        output_mp3: Optional[Path] = None,
        output_lossy: Optional[Path] = None,
    ) -> Tuple[bool, bool]:
        """
        Transcode input WAV to BOTH FLAC and MP3 simultaneously using a thread pool
        to maximize multi-core CPU utilization.
        """
        mp3_target = output_mp3 or output_lossy
        if mp3_target is None:
            raise ValueError("output_mp3 or output_lossy must be provided")

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_flac = executor.submit(self.encode_flac, input_wav, output_flac)
            future_mp3 = executor.submit(self.encode_mp3, input_wav, mp3_target)
            flac_ok = future_flac.result()
            mp3_ok = future_mp3.result()
        return flac_ok, mp3_ok

    def get_version(self) -> Optional[str]:
        """Return version string for available standalone FLAC and LAME encoders."""
        creationflags = 0x08000000 if os.name == "nt" else 0
        versions = []

        if is_binary_available(self.flac_binary):
            try:
                res = subprocess.run(
                    [self.flac_binary, "--version"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=3,
                    creationflags=creationflags,
                )
                m = re.search(r"flac\s+([0-9]+(?:\.[0-9]+)+)", res.stdout, re.IGNORECASE)
                if m:
                    versions.append(f"FLAC {m.group(1)}")
            except Exception:
                pass

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
                    versions.append(f"LAME {m.group(1)}")
            except Exception:
                pass

        return ", ".join(versions) if versions else None

    def _run_command(self, cmd: list, format_label: str) -> bool:
        """Execute encoder subprocess with CREATE_NO_WINDOW on Windows and error logging."""
        try:
            creationflags = 0x08000000 if os.name == "nt" else 0
            bin_path = Path(cmd[0])
            env = os.environ.copy()
            if bin_path.is_file():
                bin_dir = str(bin_path.resolve().parent)
                env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")

            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                creationflags=creationflags,
                env=env,
            )
            if res.returncode == 0:
                return True
            logger.error("Encoder %s encode failed (code %d): %s", format_label, res.returncode, res.stderr)
            return False
        except Exception as err:
            logger.error("Encoder execution error for %s: %s", format_label, err)
            return False


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

    def encode_dual(
        self,
        input_wav: Path,
        output_flac: Path,
        output_mp3: Optional[Path] = None,
        output_lossy: Optional[Path] = None,
    ) -> Tuple[bool, bool]:
        mp3_target = output_mp3 or output_lossy
        if mp3_target is None:
            raise ValueError("output_mp3 or output_lossy must be provided")
        return self.encode_flac(input_wav, output_flac), self.encode_mp3(input_wav, mp3_target)
