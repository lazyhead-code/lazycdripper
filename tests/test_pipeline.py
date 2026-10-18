"""End-to-end integration tests for the RipPipelineOrchestrator and RipReport integrity audits."""

from pathlib import Path
import tempfile
import unittest
from lazycdripper.core.models import (
    AlbumInfo,
    ArtworkCandidate,
    TrackInfo,
)
from lazycdripper.encoder import MockEncoder
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
            self.assertEqual(report.summary_headline, "🟢 Rip Complete")
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

            # 3. Verify MP3 sister library folder & files
            expected_mp3_dir = base_output / "Pink Floyd - Wish You Were Here (1975) [MP3]"
            self.assertTrue(expected_mp3_dir.exists())
            self.assertTrue((expected_mp3_dir / "01 - Shine On You Crazy Diamond (Pts. 1-5).mp3").exists())
            self.assertTrue((expected_mp3_dir / "02 - Welcome to the Machine.mp3").exists())
            self.assertTrue((expected_mp3_dir / "cover.jpg").exists())

            # 4. Verify directory sizes tracked in report
            self.assertGreater(report.flac_size_bytes, 0)
            self.assertGreater(report.mp3_size_bytes, 0)
            self.assertGreater(report.aac_size_bytes, 0)

    def test_execute_rip_multi_disc_companion_cover(self):
        """Verify that multi-disc albums place cover.jpg inside each Disc XX subfolder and not in parent."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_output = Path(temp_dir) / "Music"

            cover_file = Path(temp_dir) / "cached_cover.jpg"
            cover_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9")

            artwork = ArtworkCandidate(
                image_id="202",
                url="https://example.com/cover.jpg",
                local_cache_path=cover_file,
            )

            album = AlbumInfo(
                title="Everybody's Talkin'",
                artist="Tedeschi Trucks Band",
                album_artist="Tedeschi Trucks Band",
                year=2012,
                total_tracks=1,
                total_discs=2,
                tracks=[
                    TrackInfo(track_number=1, title="Midnight in Harlem", artist="Tedeschi Trucks Band", disc_number=1),
                ],
                selected_artwork=artwork,
            )

            orchestrator = RipPipelineOrchestrator(
                ripper=MockRipper(sample_duration_seconds=0.1),
                encoder=MockEncoder(),
                tagger=AudioTagger(),
            )

            report = orchestrator.execute_rip(
                album=album,
                base_output_dir=base_output,
            )

            self.assertIsNotNone(report)
            expected_flac_dir = base_output / "Tedeschi Trucks Band - Everybody's Talkin' (2012) [FLAC]"
            expected_mp3_dir = base_output / "Tedeschi Trucks Band - Everybody's Talkin' (2012) [MP3]"

            # Verify cover.jpg is inside Disc 01 subfolders
            self.assertTrue((expected_flac_dir / "Disc 01" / "cover.jpg").exists())
            self.assertTrue((expected_mp3_dir / "Disc 01" / "cover.jpg").exists())

            # Verify cover.jpg is NOT placed directly in parent album folders
            self.assertFalse((expected_flac_dir / "cover.jpg").exists())
            self.assertFalse((expected_mp3_dir / "cover.jpg").exists())

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
        self.assertIn("Unrecoverable Skips: 2 sector(s)", dmg_report.human_readable_summary)
        self.assertIn("Sector Retries: 10 recovered", dmg_report.human_readable_summary)

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
            self.assertIsNone(report.mp3_directory)
            self.assertIsNone(report.aac_directory)
            self.assertEqual(len(report.track_reports), 2)
            self.assertEqual(report.track_reports[0].status, "failed")
            self.assertEqual(report.track_reports[1].status, "failed")

    def test_execute_rip_cumulative_error_telemetry(self):
        from lazycdripper.core.models import RipProgress

        class SimErrorRipper:
            def rip_track(self, track_number, output_wav_path, device=None, total_tracks=2, on_progress=None):
                if track_number == 1:
                    # Simulate Track 1 having 5 retries and 3 errors
                    p = RipProgress(
                        current_track=1,
                        total_tracks=2,
                        track_percent=50.0,
                        read_retries=5,
                        unrecoverable_errors=3,
                        status_message="Reading...",
                    )
                    if on_progress:
                        on_progress(p)
                    # Write dummy WAV so pipeline continues
                    output_wav_path.write_bytes(b"RIFF" + b"\x00" * 100)
                    return True
                else:
                    # Track 2 has 2 retries and 0 errors
                    p = RipProgress(
                        current_track=2,
                        total_tracks=2,
                        track_percent=100.0,
                        read_retries=2,
                        unrecoverable_errors=0,
                        status_message="Reading...",
                    )
                    if on_progress:
                        on_progress(p)
                    output_wav_path.write_bytes(b"RIFF" + b"\x00" * 100)
                    return True

        with tempfile.TemporaryDirectory() as temp_dir:
            base_output = Path(temp_dir) / "Music"
            album = AlbumInfo(
                title="The Dark Side of the Moon",
                artist="Pink Floyd",
                album_artist="Pink Floyd",
                year=1973,
                total_tracks=2,
                tracks=[
                    TrackInfo(track_number=1, title="Speak to Me", artist="Pink Floyd"),
                    TrackInfo(track_number=2, title="Breathe", artist="Pink Floyd"),
                ],
            )

            orchestrator = RipPipelineOrchestrator(
                ripper=SimErrorRipper(),
                encoder=MockEncoder(),
                tagger=AudioTagger(),
            )

            telemetry_events = []

            def on_progress(p: RipProgress):
                telemetry_events.append((p.current_track, p.read_retries, p.unrecoverable_errors, p.status_message))

            report = orchestrator.execute_rip(
                album=album,
                base_output_dir=base_output,
                on_progress=on_progress,
            )

            self.assertIsNotNone(report)
            # Overall report totals
            self.assertEqual(report.total_retries, 7)
            self.assertEqual(report.total_errors, 3)
            self.assertEqual(report.overall_status, "damaged")

            # Track 1 individual report
            self.assertEqual(report.track_reports[0].read_retries, 5)
            self.assertEqual(report.track_reports[0].unrecoverable_errors, 3)
            self.assertEqual(report.track_reports[0].status, "damaged")

            # Track 2 individual report
            self.assertEqual(report.track_reports[1].read_retries, 2)
            self.assertEqual(report.track_reports[1].unrecoverable_errors, 0)
            self.assertEqual(report.track_reports[1].status, "recovered")

            # Verify cumulative telemetry was delivered to UI during Track 2:
            # During Track 2, unrecoverable_errors in telemetry should NEVER drop back to 0!
            track2_events = [e for e in telemetry_events if e[0] == 2]
            self.assertGreater(len(track2_events), 0)
            for ev in track2_events:
                track_num, retries, errors, msg = ev
                self.assertGreaterEqual(errors, 3, f"Errors dropped to {errors} during Track 2 event: {msg}")
                self.assertGreaterEqual(retries, 5, f"Retries dropped to {retries} during Track 2 event: {msg}")

            # Final Track 2 event should have full cumulative counts (7 retries, 3 errors)
            final_t2 = track2_events[-1]
            self.assertEqual(final_t2[1], 7)
            self.assertEqual(final_t2[2], 3)


if __name__ == "__main__":
    unittest.main()
