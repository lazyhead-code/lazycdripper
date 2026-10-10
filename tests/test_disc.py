"""Unit tests for optical drive detection, TOC parsing, and MusicBrainz DiscID computation."""

from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from lazycdripper.disc.drive import (
    DriveInfo,
    _detect_windows_drives,
    get_default_optical_drive,
)
from lazycdripper.disc.toc import (
    calculate_musicbrainz_discid,
    parse_cdparanoia_toc_output,
    read_cda_file,
    read_windows_cda_toc,
)

SAMPLE_CDPARANOIA_TOC_OUTPUT = """
cdparanoia III release 10.2 (October 22, 2008)

Table of contents (audio tracks only):
track        length               begin        copy pre ch
===========================================================
  1.     3900 [00:52.00]          150 [00:02.00]    no   no  2
  2.    16875 [03:45.00]         4050 [00:54.00]    no   no  2
TOTAL   20775 [04:37.00] (lead-out at sector 20925)
"""


class TestDiscTOC(unittest.TestCase):
    def test_calculate_musicbrainz_discid(self):
        # 3 tracks: 150, 50000, 100000, leadout: 150000
        disc_id = calculate_musicbrainz_discid(
            first_track=1,
            last_track=3,
            leadout_sector=150000,
            track_offsets=[150, 50000, 100000],
        )
        self.assertEqual(len(disc_id), 28)
        self.assertEqual(disc_id, "gRPeB3HB_qVr.TcdavPTyRkCXqY-")

    def test_libdiscid_official_test_vector(self):
        # Official libdiscid C library test vector from test_put.c
        leadout = 303602
        tracks = [
            150, 9700, 25887, 39297, 53795, 63735, 77517, 94877, 107270,
            123552, 135522, 148422, 161197, 174790, 192022, 205545,
            218010, 228700, 239590, 255470, 266932, 288750,
        ]
        disc_id = calculate_musicbrainz_discid(1, 22, leadout, tracks)
        self.assertEqual(disc_id, "xUp1F2NkfP8s8jaeFn_Av3jNEI4-")

        from lazycdripper.disc.toc import calculate_freedb_discid
        freedb_id = calculate_freedb_discid(1, 22, leadout, tracks)
        self.assertEqual(freedb_id, "370fce16")

    def test_parse_cdparanoia_toc_output(self):
        toc = parse_cdparanoia_toc_output(SAMPLE_CDPARANOIA_TOC_OUTPUT)
        self.assertIsNotNone(toc)
        self.assertEqual(toc.first_track, 1)
        self.assertEqual(toc.last_track, 2)
        self.assertEqual(toc.leadout_sector, 20925)
        self.assertEqual(len(toc.tracks), 2)

        # Track 1: 3900 sectors / 75 = 52.0s
        t1 = toc.tracks[0]
        self.assertEqual(t1.track_number, 1)
        self.assertEqual(t1.start_sector, 150)
        self.assertEqual(t1.length_sectors, 3900)
        self.assertAlmostEqual(t1.duration_seconds, 52.0)

        # Track 2: 16875 sectors / 75 = 225.0s (3m45s)
        t2 = toc.tracks[1]
        self.assertEqual(t2.track_number, 2)
        self.assertEqual(t2.start_sector, 4050)
        self.assertAlmostEqual(t2.duration_seconds, 225.0)

        # Total duration
        self.assertAlmostEqual(toc.total_duration_seconds, 277.0)
        # Computed DiscID is 28 chars
        self.assertEqual(len(toc.disc_id), 28)

    def test_parse_cdparanoia_toc_empty(self):
        self.assertIsNone(parse_cdparanoia_toc_output(""))
        self.assertIsNone(parse_cdparanoia_toc_output("Error: no disc present"))

    def test_read_cda_file(self):
        import tempfile
        # Construct synthetic 44-byte RIFF CDDA chunk
        # Track 1, start sector 150, length 3750 sectors (50 seconds)
        data = bytearray(44)
        data[0:4] = b"RIFF"
        data[4:8] = (36).to_bytes(4, "little")
        data[8:12] = b"CDDA"
        data[12:16] = b"fmt "
        data[16:20] = (24).to_bytes(4, "little")
        data[20:22] = (1).to_bytes(2, "little")
        data[22:24] = (1).to_bytes(2, "little")  # Track 1
        data[28:32] = (150).to_bytes(4, "little")  # Start sector 150
        data[32:36] = (3750).to_bytes(4, "little")  # Length 3750 sectors

        with tempfile.NamedTemporaryFile(suffix=".cda", delete=False) as f:
            f.write(data)
            tmp_path = Path(f.name)

        try:
            track = read_cda_file(tmp_path)
            self.assertIsNotNone(track)
            self.assertEqual(track.track_number, 1)
            self.assertEqual(track.start_sector, 150)
            self.assertEqual(track.length_sectors, 3750)
            self.assertEqual(track.end_sector, 3900)
            self.assertAlmostEqual(track.duration_seconds, 50.0)
        finally:
            tmp_path.unlink(missing_ok=True)

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_read_windows_cda_toc(self, mock_listdir, mock_exists):
        import tempfile
        mock_exists.return_value = True
        mock_listdir.return_value = ["Track01.cda", "Track02.cda"]

        # Synthetic CDA files
        d1 = bytearray(44)
        d1[0:4] = b"RIFF"
        d1[8:12] = b"CDDA"
        d1[22:24] = (1).to_bytes(2, "little")
        d1[28:32] = (150).to_bytes(4, "little")
        d1[32:36] = (3000).to_bytes(4, "little")

        d2 = bytearray(44)
        d2[0:4] = b"RIFF"
        d2[8:12] = b"CDDA"
        d2[22:24] = (2).to_bytes(2, "little")
        d2[28:32] = (3150).to_bytes(4, "little")
        d2[32:36] = (4500).to_bytes(4, "little")

        with patch.object(Path, "read_bytes", side_effect=[bytes(d1), bytes(d2)]):
            toc = read_windows_cda_toc("D:")
            self.assertIsNotNone(toc)
            self.assertEqual(toc.first_track, 1)
            self.assertEqual(toc.last_track, 2)
            self.assertEqual(len(toc.tracks), 2)
            self.assertEqual(len(toc.disc_id), 28)
            self.assertEqual(toc.tracks[0].track_number, 1)
            self.assertEqual(toc.tracks[1].track_number, 2)


class TestOpticalDriveDetection(unittest.TestCase):
    @patch("lazycdripper.disc.drive.detect_optical_drives")
    def test_get_default_optical_drive(self, mock_detect):
        mock_detect.return_value = [DriveInfo(device_path=r"\\.\D:", name="[D:] DVD Drive", drive_letter="D:")]
        drive = get_default_optical_drive()
        self.assertIsNotNone(drive)
        self.assertEqual(drive.device_path, r"\\.\D:")

        mock_detect.return_value = []
        self.assertIsNone(get_default_optical_drive())

    def test_detect_windows_drives_win32_fast_path(self):
        """Test Windows Win32 GetDriveTypeW fast detection path."""
        mock_kernel32 = MagicMock()
        mock_kernel32.GetDriveTypeW.side_effect = lambda path: 5 if path == "D:\\" else 3
        mock_ctypes = MagicMock()
        mock_ctypes.windll.kernel32 = mock_kernel32
        with patch("lazycdripper.disc.drive.ctypes", mock_ctypes), \
             patch("lazycdripper.disc.drive._get_windows_drive_model_ioctl", return_value="ASUS BW-16D1HT"):
            drives = _detect_windows_drives()
            self.assertEqual(len(drives), 1)
            self.assertEqual(drives[0].drive_letter, "D:")
            self.assertEqual(drives[0].device_path, r"\\.\D:")
            self.assertIn("ASUS BW-16D1HT", drives[0].name)

    @patch("lazycdripper.disc.drive.ctypes", None)
    @patch("subprocess.run")
    def test_detect_windows_drives_powershell_fallback(self, mock_subproc):
        """Test fallback when ctypes Win32 subsystem is unavailable."""
        mock_subproc.return_value = MagicMock(
            returncode=0,
            stdout='{"Drive": "D:", "Caption": "HL-DT-ST DVDRAM GU90N"}',
        )
        drives = _detect_windows_drives()
        self.assertEqual(len(drives), 1)
        self.assertEqual(drives[0].drive_letter, "D:")
        self.assertEqual(drives[0].device_path, r"\\.\D:")
        self.assertIn("HL-DT-ST DVDRAM GU90N", drives[0].name)


if __name__ == "__main__":
    unittest.main()
