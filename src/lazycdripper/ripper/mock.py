"""Mock CD ripper for offline automated testing and CI pipelines."""

import math
from pathlib import Path
import struct
from typing import Callable, Dict, List, Optional
import wave
from lazycdripper.core.models import RipProgress, TrackInfo
from lazycdripper.disc.toc import DiscTOC, TrackTOC, calculate_musicbrainz_discid

ProgressCallback = Callable[[RipProgress], None]


class MockRipper:
    """Emulates optical drive extraction by generating synthetic 16-bit 44.1kHz WAV files."""

    def __init__(self, sample_duration_seconds: float = 0.5):
        self.sample_duration_seconds = sample_duration_seconds

    @property
    def is_available(self) -> bool:
        return True

    def query_toc(self, device: Optional[str] = None) -> Optional[DiscTOC]:
        """Return a simulated 3-track DiscTOC with known DiscID."""
        tracks = [
            TrackTOC(track_number=1, start_sector=150, end_sector=15150, length_sectors=15000),
            TrackTOC(track_number=2, start_sector=15150, end_sector=30150, length_sectors=15000),
            TrackTOC(track_number=3, start_sector=30150, end_sector=45150, length_sectors=15000),
        ]
        leadout = 45150
        offsets = [t.start_sector for t in tracks]
        disc_id = calculate_musicbrainz_discid(1, 3, leadout, offsets)

        return DiscTOC(
            first_track=1,
            last_track=3,
            leadout_sector=leadout,
            tracks=tracks,
            disc_id=disc_id,
        )

    def rip_track(
        self,
        track_number: int,
        output_wav_path: Path,
        device: Optional[str] = None,
        total_tracks: int = 1,
        on_progress: Optional[ProgressCallback] = None,
    ) -> bool:
        """Generate a valid 16-bit 44.1kHz Stereo PCM WAV file with a pure sine wave tone."""
        output_wav_path.parent.mkdir(parents=True, exist_ok=True)

        sample_rate = 44100
        num_channels = 2  # Stereo
        sample_width = 2   # 16-bit
        num_frames = int(sample_rate * self.sample_duration_seconds)
        frequency = 440.0 + (track_number * 50.0)  # Different pitch per track

        progress = RipProgress(
            current_track=track_number,
            total_tracks=total_tracks,
            track_percent=0.0,
            status_message="Extracting track...",
        )
        if on_progress:
            on_progress(progress)

        with wave.open(str(output_wav_path), "wb") as wav_file:
            wav_file.setnchannels(num_channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)

            # Generate stereo sine wave samples
            frames = bytearray()
            for i in range(num_frames):
                t = float(i) / sample_rate
                val = int(math.sin(2.0 * math.pi * frequency * t) * 16000.0)
                # Pack 16-bit signed stereo frame (L, R)
                frames.extend(struct.pack("<hh", val, val))

            wav_file.writeframes(frames)

        if on_progress:
            progress.track_percent = 100.0
            progress.status_message = f"Track {track_number} synthesized cleanly"
            on_progress(progress)

        return True

    def rip_disc(
        self,
        tracks: List[TrackInfo],
        scratch_dir: Path,
        device: Optional[str] = None,
        on_progress: Optional[ProgressCallback] = None,
    ) -> Dict[int, Path]:
        """Simulate extracting all tracks on a disc."""
        scratch_dir.mkdir(parents=True, exist_ok=True)
        results: Dict[int, Path] = {}
        total = len(tracks)

        for idx, track in enumerate(tracks, start=1):
            wav_path = scratch_dir / f"track_{track.track_number:02d}_scratch.wav"

            def callback(p: RipProgress):
                p.overall_percent = ((idx - 1 + (p.track_percent / 100.0)) / total) * 100.0
                if on_progress:
                    on_progress(p)

            self.rip_track(
                track_number=track.track_number,
                output_wav_path=wav_path,
                device=device,
                total_tracks=total,
                on_progress=callback,
            )
            results[track.track_number] = wav_path

        return results
