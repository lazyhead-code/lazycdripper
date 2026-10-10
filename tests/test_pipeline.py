"""End-to-end integration tests for the RipPipelineOrchestrator and RipReport integrity audits."""

from pathlib import Path
import tempfile
import unittest
from lazycdripper.core.models import (
    AlbumInfo,
    ArtworkCandidate,
    TrackInfo,
)
from lazycdripper.encoder.ffmpeg import MockEncoder
from lazycdripper.pipeline.orchestrator import RipPipelineOrchestrator
from lazycdripper.ripper.mock import MockRipper
from lazycdripper.tagger.tagger import AudioTagger


class TestRipPipelineOrchestrator(unittest.TestCase):
    def test_execute_rip_end_to_end_pristine(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_output = Path(temp_dir) / "Music"

            # Create dummy cover image
            cover_file = Path(temp_dir) / "cached_cover.jpg"
            cover_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9")

            artwork = ArtworkCandidate(
                image_id="101",
                url="https://example.com/cover.jpg",
                thumbnail_url="https://example.com/thumb.jpg",
                local_cache_path=cover_file,
            )

            album = AlbumInfo(
                title="Wish You Were Here",
                artist="Pink Floyd",
                album_artist="Pink Floyd",
                year=1975,
                total_tracks=2,
                tracks=[
                    TrackInfo(track_number=1, title="Shine On You Crazy Diamond (Pts. 1-5)", artist="Pink Floyd"),
                    TrackInfo(track_number=2, title="Welcome to the Machine", artist="Pink Floyd"),
                ],
                selected_artwork=artwork,
            )

            orchestrator = RipPipelineOrchestrator(
                ripper=MockRipper(sample_duration_seconds=0.1),
                encoder=MockEncoder(),
                tagger=AudioTagger(),
            )

            progress_events = []
            status_messages = []

            def progress_tracker(p):
                progress_events.append(p.overall_percent)
                if p.status_message:
                    status_messages.append(p.status_message)

            report = orchestrator.execute_rip(
                album=album,
                base_output_dir=base_output,
                include_track_number=True,
                include_artist=False,
                on_progress=progress_tracker,
            )

            # 1. Verify AlbumRipReport audit
            self.assertIsNotNone(report)
            self.assertEqual(report.album_title, "Wish You Were Here")
            self.assertEqual(report.artist, "Pink Floyd")
            self.assertEqual(report.year, 1975)
            self.assertEqual(report.total_tracks, 2)
            self.assertTrue(report.is_perfect)
            self.assertEqual(report.overall_status, "pristine")
            self.assertEqual(report.summary_headline, "🟢 Bit-Perfect Pristine Rip")
            self.assertIn("100% bit-perfect accuracy", report.human_readable_summary)
            self.assertEqual(len(report.track_reports), 2)
            self.assertGreater(len(progress_events), 0)
            self.assertTrue(any("Transcoding" in m for m in status_messages))
            self.assertTrue(any("metadata" in m or "tags" in m for m in status_messages))

            # 2. Verify FLAC sister library folder & files
            expected_flac_dir = base_output / "Pink Floyd - Wish You Were Here (1975) [FLAC]"
            self.assertTrue(expected_flac_dir.exists())
            self.assertTrue((expected_flac_dir / "01 - Shine On You Crazy Diamond (Pts. 1-5).flac").exists())
            self.assertTrue((expected_flac_dir / "02 - Welcome to the Machine.flac").exists())
            self.assertTrue((expected_flac_dir / "cover.jpg").exists())

            # 3. Verify AAC sister library folder & files
            expected_aac_dir = base_output / "Pink Floyd - Wish You Were Here (1975) [AAC]"
            self.assertTrue(expected_aac_dir.exists())
            self.assertTrue((expected_aac_dir / "01 - Shine On You Crazy Diamond (Pts. 1-5).m4a").exists())
            self.assertTrue((expected_aac_dir / "02 - Welcome to the Machine.m4a").exists())
            self.assertTrue((expected_aac_dir / "cover.jpg").exists())

            # 4. Verify directory sizes tracked in report
            self.assertGreater(report.flac_size_bytes, 0)
            self.assertGreater(report.aac_size_bytes, 0)

    def test_album_rip_report_status_degraded(self):
        # Test headline badges for damaged or recovered discs
        from lazycdripper.core.models import AlbumRipReport

        # Recovered report
        rec_report = AlbumRipReport(
            album_title="Test",
            artist="Artist",
            total_tracks=1,
            total_jitter=2,
            total_retries=5,
            total_errors=0,
        )
        self.assertFalse(rec_report.is_perfect)
        self.assertEqual(rec_report.summary_headline, "🟡 Recovered With Multi-Pass Correction")
        self.assertIn("zero data loss", rec_report.human_readable_summary)

        # Damaged report
        dmg_report = AlbumRipReport(
            album_title="Test",
            artist="Artist",
            total_tracks=1,
            total_retries=10,
            total_errors=2,
        )
        self.assertFalse(dmg_report.is_perfect)
        self.assertEqual(dmg_report.summary_headline, "🔴 Surface Damage Detected")
        self.assertIn("Severe scratch damage", dmg_report.human_readable_summary)

        # Failed report
        fail_report = AlbumRipReport(
            album_title="Test",
            artist="Artist",
            total_tracks=1,
            overall_status="failed",
            total_errors=5,
        )
        self.assertFalse(fail_report.is_perfect)
        self.assertEqual(fail_report.successful_tracks_count, 0)
        self.assertEqual(fail_report.summary_headline, "🔴 Extraction Failed — Drive Read Error")
        self.assertIn("Failed to extract audio tracks", fail_report.human_readable_summary)

    def test_execute_rip_complete_extraction_failure(self):
        class FailingRipper:
            def rip_track(self, track_number, output_wav_path, device=None, total_tracks=1, on_progress=None):
                return False

        with tempfile.TemporaryDirectory() as temp_dir:
            base_output = Path(temp_dir) / "Music"

            album = AlbumInfo(
                title="Peace... Like a River",
                artist="Gov't Mule",
                album_artist="Gov't Mule",
                year=2023,
                total_tracks=2,
                tracks=[
                    TrackInfo(track_number=1, title="Same As It Ever Was", artist="Gov't Mule"),
                    TrackInfo(track_number=2, title="Shake Our Way Out", artist="Gov't Mule"),
                ],
            )

            orchestrator = RipPipelineOrchestrator(
                ripper=FailingRipper(),
                encoder=MockEncoder(),
                tagger=AudioTagger(),
            )

            report = orchestrator.execute_rip(
                album=album,
                base_output_dir=base_output,
            )

            self.assertIsNotNone(report)
            self.assertFalse(report.is_perfect)
            self.assertEqual(report.overall_status, "failed")
            self.assertEqual(report.successful_tracks_count, 0)
            self.assertEqual(report.summary_headline, "🔴 Extraction Failed — Drive Read Error")
            self.assertIn("Failed to extract audio tracks", report.human_readable_summary)
            self.assertIsNone(report.flac_directory)
            self.assertIsNone(report.aac_directory)
            self.assertEqual(len(report.track_reports), 2)
            self.assertEqual(report.track_reports[0].status, "failed")
            self.assertEqual(report.track_reports[1].status, "failed")


if __name__ == "__main__":
    unittest.main()
