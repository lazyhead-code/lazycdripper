"""Unit tests for domain models."""

from pathlib import Path
import unittest
from lazycdripper.core.models import (
    AlbumInfo,
    ArtworkCandidate,
    AudioFormat,
    RipProgress,
    TrackInfo,
)


class TestModels(unittest.TestCase):
    def test_album_and_track_models(self):
        t1 = TrackInfo(track_number=1, title="Come Together", artist="The Beatles", duration_seconds=259.0)
        t2 = TrackInfo(track_number=2, title="Something", artist="The Beatles", duration_seconds=182.0)

        album = AlbumInfo(
            title="Abbey Road",
            artist="The Beatles",
            album_artist="The Beatles",
            year=1969,
            total_tracks=2,
            tracks=[t1, t2],
        )

        self.assertEqual(album.title, "Abbey Road")
        self.assertEqual(len(album.tracks), 2)
        self.assertEqual(album.tracks[0].title, "Come Together")

        # AlbumInfo without explicit album_artist should default to artist
        album2 = AlbumInfo(title="Help!", artist="The Beatles")
        self.assertEqual(album2.album_artist, "The Beatles")

    def test_artwork_candidate(self):
        art = ArtworkCandidate(
            image_id="12345",
            url="https://coverartarchive.org/release/123/12345.jpg",
            thumbnail_url="https://coverartarchive.org/release/123/12345-250.jpg",
            is_front=True,
            width=1200,
            height=1200,
        )
        self.assertTrue(art.is_front)
        self.assertEqual(art.width, 1200)

    def test_rip_progress(self):
        progress = RipProgress(
            current_track=3,
            total_tracks=10,
            track_percent=75.5,
            overall_percent=27.55,
            status_message="Ripping track 3 of 10",
            jitter_corrections=2,
            track_title="Come Together",
        )
        self.assertEqual(progress.current_track, 3)
        self.assertEqual(progress.jitter_corrections, 2)
        self.assertEqual(progress.track_title, "Come Together")

    def test_album_rip_report_rip_folder(self):
        import tempfile
        from pathlib import Path
        from lazycdripper.core.models import AlbumRipReport

        with tempfile.TemporaryDirectory() as temp_dir:
            dest_dir = Path(temp_dir) / "Music"
            dest_dir.mkdir()
            flac_dir = dest_dir / "Artist - Album [FLAC]"
            flac_dir.mkdir()

            # Using destination_directory directly
            report1 = AlbumRipReport(
                album_title="Test",
                artist="Artist",
                destination_directory=dest_dir,
            )
            self.assertEqual(report1.rip_folder, dest_dir)

            # Fallback to flac_directory parent
            report2 = AlbumRipReport(
                album_title="Test",
                artist="Artist",
                flac_directory=flac_dir,
            )
            self.assertEqual(report2.rip_folder, dest_dir)

    def test_audio_format_enum(self):
        self.assertEqual(AudioFormat.FLAC.value, "flac")
        self.assertEqual(AudioFormat.MP3.value, "mp3")
        self.assertEqual(AudioFormat.AAC.value, "aac")

    def test_album_rip_report_clean_headline(self):
        from lazycdripper.core.models import AlbumRipReport

        # Pristine
        rep_ok = AlbumRipReport(
            album_title="Album",
            artist="Artist",
            total_tracks=1,
            overall_status="pristine",
        )
        self.assertEqual(rep_ok.summary_headline, "🟢 Rip Complete")
        self.assertEqual(rep_ok.clean_headline, "Rip Complete")

        # Degraded / surface damage
        rep_dmg = AlbumRipReport(
            album_title="Album",
            artist="Artist",
            total_tracks=1,
            overall_status="degraded",
            total_errors=2,
        )
        self.assertEqual(rep_dmg.summary_headline, "🔴 Surface Damage Detected")
        self.assertEqual(rep_dmg.clean_headline, "Surface Damage Detected")

        # Recovered
        rep_rec = AlbumRipReport(
            album_title="Album",
            artist="Artist",
            total_tracks=1,
            overall_status="recovered",
            total_retries=3,
        )
        self.assertEqual(rep_rec.summary_headline, "🟡 Recovered With Multi-Pass Correction")
        self.assertEqual(rep_rec.clean_headline, "Recovered With Multi-Pass Correction")

    def test_track_rip_report(self):
        from lazycdripper.core.models import TrackRipReport
        # Standard initialization with unrecoverable_errors
        t1 = TrackRipReport(track_number=1, title="Track 1", unrecoverable_errors=3)
        self.assertEqual(t1.unrecoverable_errors, 3)
        self.assertEqual(t1.read_errors, 3)

        # Alternative alias initialization with read_errors
        t2 = TrackRipReport(track_number=2, title="Track 2", read_errors=5)
        self.assertEqual(t2.unrecoverable_errors, 5)
        self.assertEqual(t2.read_errors, 5)

        # mp3_path and aac_path backward compatibility alias syncing
        mp3_p = Path("/tmp/01.mp3")
        t3 = TrackRipReport(track_number=3, title="Track 3", mp3_path=mp3_p)
        self.assertEqual(t3.mp3_path, mp3_p)
        self.assertEqual(t3.aac_path, mp3_p)

        aac_p = Path("/tmp/04.m4a")
        t4 = TrackRipReport(track_number=4, title="Track 4", aac_path=aac_p)
        self.assertEqual(t4.mp3_path, aac_p)
        self.assertEqual(t4.aac_path, aac_p)

    def test_album_rip_report_mp3_aliases(self):
        from lazycdripper.core.models import AlbumRipReport
        mp3_d = Path("/tmp/Artist - Album [MP3]")
        rep = AlbumRipReport(
            album_title="Album",
            artist="Artist",
            mp3_directory=mp3_d,
            mp3_size_bytes=1000,
        )
        self.assertEqual(rep.mp3_directory, mp3_d)
        self.assertEqual(rep.aac_directory, mp3_d)
        self.assertEqual(rep.mp3_size_bytes, 1000)
        self.assertEqual(rep.aac_size_bytes, 1000)


if __name__ == "__main__":
    unittest.main()
