"""Unit tests for domain models."""

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
        self.assertEqual(AudioFormat.AAC.value, "aac")


if __name__ == "__main__":
    unittest.main()
