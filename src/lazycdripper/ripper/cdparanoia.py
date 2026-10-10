"""Audio CD extraction backend wrapping cdparanoia with real-time error and progress parsing."""

import logging
from pathlib import Path
import re
import subprocess
from typing import Callable, Dict, List, Optional
from lazycdripper.core.binaries import find_binary, is_binary_available
from lazycdripper.core.models import RipProgress, TrackInfo
from lazycdripper.disc.toc import DiscTOC, parse_cdparanoia_toc_output

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[RipProgress], None]


class CdparanoiaRipper:
    """Wraps cdparanoia CLI to extract CD-DA audio tracks with jitter correction."""

    def __init__(self, binary_path: Optional[str] = None):
        self.binary_path = find_binary("cdparanoia", custom_path=binary_path)

    @property
    def is_available(self) -> bool:
        """Check if the cdparanoia binary is present and executable."""
        return is_binary_available(self.binary_path)

    def query_toc(self, device: Optional[str] = None) -> Optional[DiscTOC]:
        """Query Table of Contents (TOC) using native Windows detection or 'cdparanoia -Q'."""
        from lazycdripper.disc.toc import read_windows_toc
        win_toc = read_windows_toc(device)
        if win_toc:
            return win_toc

        if not self.is_available:
            return None

        cmd = [self.binary_path]
        if device:
            cmd.extend(["-d", device])
        cmd.append("-Q")

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
            )
            # cdparanoia outputs TOC information to stderr!
            combined_output = f"{res.stdout}\n{res.stderr}"
            return parse_cdparanoia_toc_output(combined_output)
        except Exception as err:
            logger.error("Failed to query TOC with cdparanoia: %s", err)
            return None

    def rip_track(
        self,
        track_number: int,
        output_wav_path: Path,
        device: Optional[str] = None,
        total_tracks: int = 1,
        on_progress: Optional[ProgressCallback] = None,
    ) -> bool:
        """
        Extract a single audio track directly to a 16-bit 44.1kHz PCM WAV file.
        Parses real-time progress and jitter/scratch correction indicators from stderr.
        """
        output_wav_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [self.binary_path]
        if device:
            cmd.extend(["-d", device])

        # cdparanoia syntax: cdparanoia <track_number> <output_file.wav>
        cmd.extend([str(track_number), str(output_wav_path)])

        progress = RipProgress(
            current_track=track_number,
            total_tracks=total_tracks,
            track_percent=0.0,
            status_message="Extracting track...",
        )

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            # cdparanoia streams dynamic status lines over stderr
            if process.stderr:
                for line in iter(process.stderr.readline, ""):
                    if not line:
                        break
                    self._parse_cdparanoia_stderr_line(line, progress)
                    if on_progress:
                        on_progress(progress)

            process.wait()
            success = process.returncode == 0 and output_wav_path.exists()
            if success and on_progress:
                progress.track_percent = 100.0
                progress.status_message = f"Track {track_number} extracted cleanly"
                on_progress(progress)
            return success

        except Exception as err:
            logger.error("Exception occurred while ripping track %d: %s", track_number, err)
            return False

    def rip_disc(
        self,
        tracks: List[TrackInfo],
        scratch_dir: Path,
        device: Optional[str] = None,
        on_progress: Optional[ProgressCallback] = None,
    ) -> Dict[int, Path]:
        """
        Extract all audio tracks in sequence into scratch WAV files.
        Returns a mapping of track_number -> Path to extracted .wav file.
        """
        scratch_dir.mkdir(parents=True, exist_ok=True)
        results: Dict[int, Path] = {}
        total = len(tracks)

        for idx, track in enumerate(tracks, start=1):
            wav_path = scratch_dir / f"track_{track.track_number:02d}_scratch.wav"

            def track_callback(p: RipProgress):
                # Calculate overall disc completion percent
                completed_tracks = idx - 1
                current_contrib = p.track_percent / 100.0
                p.overall_percent = ((completed_tracks + current_contrib) / total) * 100.0
                if on_progress:
                    on_progress(p)

            success = self.rip_track(
                track_number=track.track_number,
                output_wav_path=wav_path,
                device=device,
                total_tracks=total,
                on_progress=track_callback,
            )

            if success:
                results[track.track_number] = wav_path
            else:
                logger.error("Failed to extract track %d", track.track_number)

        return results

    @staticmethod
    def _parse_cdparanoia_stderr_line(line: str, progress: RipProgress):
        """Parse status symbols and sector progress from cdparanoia stderr."""
        # Detect jitter corrections '+'
        if "+" in line:
            progress.jitter_corrections += line.count("+")
        # Detect sector scratch / retries 'e'
        if "e" in line:
            progress.read_retries += line.count("e")
        # Detect hard errors '!'
        if "!" in line:
            progress.unrecoverable_errors += line.count("!")

        # Parse percentage or sector numbers if reported: e.g. [012345] or percentage
        pct_match = re.search(r"(\d+)%", line)
        if pct_match:
            progress.track_percent = float(pct_match.group(1))
