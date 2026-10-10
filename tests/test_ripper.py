"""Unit tests for cdparanoia extraction backend and MockRipper emulation."""

from pathlib import Path
import tempfile
import unittest
import wave
from lazycdripper.core.models import RipProgress, TrackInfo
from lazycdripper.ripper import get_default_ripper
from lazycdripper.ripper.cdparanoia import CdparanoiaRipper
from lazycdripper.ripper.mock import MockRipper
from lazycdripper.ripper.windows import WindowsCddaRipper


class TestCdparanoiaParsing(unittest.TestCase):
    def test_parse_stderr_line(self):
        progress = RipProgress(current_track=1, total_tracks=10)

        # Line with jitter '+' and retry 'e' and 45% progress
        CdparanoiaRipper._parse_cdparanoia_stderr_line("## ===> [  45%] +++ ee !", progress)

        self.assertEqual(progress.track_percent, 45.0)
        self.assertEqual(progress.jitter_corrections, 3)
        self.assertEqual(progress.read_retries, 2)
        self.assertEqual(progress.unrecoverable_errors, 1)


class TestMockRipper(unittest.TestCase):
    def setUp(self):
        self.ripper = MockRipper(sample_duration_seconds=0.2)

    def test_query_toc(self):
        toc = self.ripper.query_toc()
        self.assertIsNotNone(toc)
        self.assertEqual(toc.total_tracks, 3)
        self.assertEqual(len(toc.disc_id), 28)

    def test_rip_track_produces_valid_cd_wav(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wav_path = Path(temp_dir) / "track_01.wav"
            progress_events = []

            success = self.ripper.rip_track(
                track_number=1,
                output_wav_path=wav_path,
                total_tracks=1,
                on_progress=lambda p: progress_events.append(p.track_percent),
            )

            self.assertTrue(success)
            self.assertTrue(wav_path.exists())
            self.assertIn(100.0, progress_events)

            # Verify standard CD Red Book audio specifications: 16-bit 44.1kHz Stereo
            with wave.open(str(wav_path), "rb") as wf:
                self.assertEqual(wf.getnchannels(), 2)       # 2 channels (Stereo)
                self.assertEqual(wf.getsampwidth(), 2)      # 16-bit PCM (2 bytes per sample)
                self.assertEqual(wf.getframerate(), 44100)  # 44,100 Hz sampling rate
                self.assertGreater(wf.getnframes(), 0)

    def test_rip_disc_all_tracks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            scratch_dir = Path(temp_dir) / "scratch"
            tracks = [
                TrackInfo(track_number=1, title="Track 1", artist="Artist"),
                TrackInfo(track_number=2, title="Track 2", artist="Artist"),
            ]

            results = self.ripper.rip_disc(tracks, scratch_dir)

            self.assertEqual(len(results), 2)
            self.assertTrue(results[1].exists())
            self.assertTrue(results[2].exists())


from lazycdripper.ripper.windows import (
    TRACK_MODE_CDDA,
    TRACK_MODE_XA_FORM2,
    TRACK_MODE_YELLOW_MODE2,
    RAW_READ_INFO,
    WindowsCddaRipper,
    sector_to_lba,
)


class TestWindowsRipperAndFactory(unittest.TestCase):
    def test_windows_cdda_ripper_availability_and_attributes(self):
        ripper = WindowsCddaRipper()
        import platform
        is_win = "windows" in platform.system().lower()
        self.assertEqual(ripper.is_available, is_win)

    def test_get_default_ripper_factory(self):
        ripper = get_default_ripper()
        self.assertIsNotNone(ripper)
        self.assertTrue(hasattr(ripper, "query_toc"))
        self.assertTrue(hasattr(ripper, "rip_track"))

    def test_sector_to_lba_conversion(self):
        # Track 1 starts at MSF 00:02:00 = sector 150 -> LBA 0
        self.assertEqual(sector_to_lba(150), 0)
        # Track 2 start e.g. sector 30510 -> LBA 30360
        self.assertEqual(sector_to_lba(30510), 30360)
        # Sector 0 -> LBA 0
        self.assertEqual(sector_to_lba(0), 0)
        # Sector under 150
        self.assertEqual(sector_to_lba(75), 75)

    def test_windows_cdda_structure_and_constants(self):
        import ctypes
        self.assertEqual(TRACK_MODE_YELLOW_MODE2, 0)
        self.assertEqual(TRACK_MODE_XA_FORM2, 1)
        self.assertEqual(TRACK_MODE_CDDA, 2)

        if RAW_READ_INFO is not None:
            self.assertEqual(ctypes.sizeof(RAW_READ_INFO), 16)
            info = RAW_READ_INFO(DiskOffset=0, SectorCount=20, TrackMode=TRACK_MODE_CDDA)
            self.assertEqual(info.DiskOffset, 0)
            self.assertEqual(info.SectorCount, 20)
            self.assertEqual(info.TrackMode, 2)


if __name__ == "__main__":
    unittest.main()
