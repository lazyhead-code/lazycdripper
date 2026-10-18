"""Unit tests for GUI components, theme constants, and dialog content."""

import unittest
from lazycdripper.gui.theme import (
    COLOR_AMBER,
    COLOR_BG_DARK,
    DARK_ROCK_STYLESHEET,
)
from lazycdripper.gui.widgets.liner_notes_dialog import LINER_NOTES_TEXT
from lazycdripper.core.models import RipProgress
from lazycdripper.gui.widgets.ripping_view import (
    HiFiOpticalTransportWidget,
    NOSTALGIC_MEMORIES,
    RippingViewWidget,
)


class TestGuiThemeAndContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from PySide6.QtWidgets import QApplication
            cls._app = QApplication.instance() or QApplication(["-platform", "offscreen"])
        except ImportError:
            cls._app = None

    def test_theme_colors(self):
        self.assertEqual(COLOR_AMBER, "#FF9E3B")
        self.assertEqual(COLOR_BG_DARK, "#0C0C0F")
        self.assertIn("#FF9E3B", DARK_ROCK_STYLESHEET)
        self.assertIn("primaryRipButton", DARK_ROCK_STYLESHEET)
        self.assertIn("pillButton", DARK_ROCK_STYLESHEET)
        self.assertIn("policyCard", DARK_ROCK_STYLESHEET)
        self.assertIn("btnIconRefresh", DARK_ROCK_STYLESHEET)
        self.assertIn("QPushButton#btnIconRefresh", DARK_ROCK_STYLESHEET)
        self.assertIn("border-radius: 8px;", DARK_ROCK_STYLESHEET)
        self.assertIn("QComboBox", DARK_ROCK_STYLESHEET)
        self.assertIn("QComboBox::drop-down", DARK_ROCK_STYLESHEET)
        self.assertIn("artworkFrame", DARK_ROCK_STYLESHEET)
        self.assertIn("padding: 0px;", DARK_ROCK_STYLESHEET)
        self.assertIn("QScrollBar:vertical", DARK_ROCK_STYLESHEET)
        self.assertIn("margin: 14px 4px 14px 0px;", DARK_ROCK_STYLESHEET)
        self.assertIn("QHeaderView", DARK_ROCK_STYLESHEET)
        self.assertIn("QTableWidget", DARK_ROCK_STYLESHEET)

    def test_nostalgic_memories_ticker_content(self):
        self.assertGreaterEqual(len(NOSTALGIC_MEMORIES), 6)
        self.assertEqual(len(set(NOSTALGIC_MEMORIES)), len(NOSTALGIC_MEMORIES))
        # Check that festival, alone party, friend party, and jewel case memories are present
        memories_combined = " ".join(NOSTALGIC_MEMORIES)
        self.assertIn("jewel case", memories_combined)
        self.assertIn("lyric booklet", memories_combined)
        self.assertIn("festival", memories_combined)
        self.assertIn("best friends", memories_combined)
        self.assertIn("partying alone", memories_combined)

    def test_liner_notes_philosophy_text(self):
        self.assertIn("We've gained so much with music streaming services.", LINER_NOTES_TEXT)
        self.assertIn("opinionated AF", LINER_NOTES_TEXT)
        self.assertIn("surrender to an illusion :)", LINER_NOTES_TEXT)
        self.assertIn("Lazyhead Code 💿", LINER_NOTES_TEXT)

    def test_locate_app_icon_path(self):
        from lazycdripper.gui.main_window import locate_app_icon_path
        icon_path = locate_app_icon_path()
        self.assertIsNotNone(icon_path)
        self.assertTrue(icon_path.is_file())
        self.assertIn(icon_path.name, ["logo.ico", "icon.png", "logo.jpg"])

    def test_hifi_optical_transport_widget(self):
        from lazycdripper.gui.widgets.ripping_view import HAVE_QT
        if HAVE_QT:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication(["-platform", "offscreen"])
        widget = HiFiOpticalTransportWidget()
        widget.set_track_progress(0.45)
        self.assertAlmostEqual(widget._track_progress, 0.45)
        # Bounds clamping
        widget.set_track_progress(-0.5)
        self.assertEqual(widget._track_progress, 0.0)
        widget.set_track_progress(1.5)
        self.assertEqual(widget._track_progress, 1.0)

    def test_ripping_view_update_progress(self):
        from lazycdripper.gui.widgets.ripping_view import HAVE_QT
        if HAVE_QT:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication(["-platform", "offscreen"])
        view = RippingViewWidget()
        if hasattr(view, "spec_badge"):
            self.assertEqual(view.spec_badge.text(), "AUDIO CD • 16-BIT / 44.1 kHz")

        prog = RipProgress(
            current_track=2,
            total_tracks=10,
            track_percent=55.0,
            overall_percent=15.5,
            status_message="Extracting track...",
            current_speed="14.2x",
            jitter_corrections=3,
        )
        view.update_progress(prog)
        if hasattr(view, "transport_widget") and view.transport_widget:
            self.assertAlmostEqual(view.transport_widget._track_progress, 0.55)
        if hasattr(view, "headline"):
            self.assertFalse(view.headline.wordWrap())
            self.assertFalse(view.status_sub.wordWrap())
            self.assertGreaterEqual(view.visual_frame.minimumWidth(), 600)
            self.assertEqual(view.headline.text(), "Track 2 of 10")
            self.assertEqual(view.track_label.text(), "Extracting")
            self.assertEqual(view.status_sub.text(), "Reading disc  •  14.2x")
            self.assertEqual(view.memory_card.maximumHeight(), 72)
            self.assertEqual(view.memory_card.minimumHeight(), 72)

        self.assertEqual(view.MEMORY_ROTATION_INTERVAL_MS, 90000)

        # Test dual-transcoding progress state
        prog_encode = RipProgress(
            current_track=2,
            total_tracks=10,
            track_percent=100.0,
            overall_percent=20.0,
            status_message="Transcoding: Lossless FLAC + 320k MP3...",
        )
        view.update_progress(prog_encode)
        if hasattr(view, "headline"):
            self.assertEqual(view.headline.text(), "Track 2 of 10")
            self.assertEqual(view.track_label.text(), "Transcoding")
            self.assertEqual(view.status_sub.text(), "Encoding  •  Lossless FLAC + MP3")

        # Test tagging progress state
        prog_tag = RipProgress(
            current_track=2,
            total_tracks=10,
            track_percent=100.0,
            overall_percent=20.0,
            status_message="Embedding metadata & cover art...",
        )
        view.update_progress(prog_tag)
        if hasattr(view, "headline"):
            self.assertEqual(view.headline.text(), "Track 2 of 10")
            self.assertEqual(view.track_label.text(), "Tagging")
            self.assertEqual(view.status_sub.text(), "Embedding metadata & cover art")

        # Test track title display when title is present in RipProgress
        prog_named = RipProgress(
            current_track=2,
            total_tracks=10,
            track_percent=62.0,
            overall_percent=18.0,
            status_message="Extracting track...",
            track_title="Something",
        )
        view.update_progress(prog_named)
        if hasattr(view, "headline"):
            self.assertEqual(view.headline.text(), 'Track 2 of 10: "Something"')
            self.assertEqual(view.track_label.text(), "Extracting")
            self.assertEqual(view.status_sub.text(), "Reading disc...")

        # Test encoding and tagging with track title
        prog_named_enc = RipProgress(
            current_track=2,
            total_tracks=10,
            track_percent=100.0,
            overall_percent=20.0,
            status_message="Transcoding: Lossless FLAC + 320k MP3...",
            track_title="Something",
        )
        view.update_progress(prog_named_enc)
        if hasattr(view, "headline"):
            self.assertEqual(view.headline.text(), 'Track 2 of 10: "Something"')
            self.assertEqual(view.track_label.text(), "Transcoding")
            self.assertEqual(view.status_sub.text(), "Encoding  •  Lossless FLAC + MP3")

        # Test track title resolution via AlbumInfo set_album
        from lazycdripper.core.models import AlbumInfo, TrackInfo
        album = AlbumInfo(
            title="Abbey Road",
            artist="The Beatles",
            album_artist="The Beatles",
            tracks=[
                TrackInfo(track_number=1, title="Come Together", artist="The Beatles"),
                TrackInfo(track_number=2, title="Something", artist="The Beatles"),
            ],
        )
        view.set_album(album)
        prog_album_res = RipProgress(
            current_track=1,
            total_tracks=2,
            track_percent=40.0,
            overall_percent=20.0,
            status_message="Extracting Track 1...",
        )
        view.update_progress(prog_album_res)
        if hasattr(view, "headline"):
            self.assertEqual(view.headline.text(), 'Track 1 of 2: "Come Together"')
            self.assertEqual(view.track_label.text(), "Extracting")

    def test_backdrop_artwork_pixmap(self):
        from lazycdripper.gui.main_window import BackgroundBackdropWidget, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not installed")
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(["-platform", "offscreen"])
        backdrop = BackgroundBackdropWidget()
        self.assertIsNone(backdrop._artwork_pixmap)
        from PySide6.QtGui import QPixmap
        pix = QPixmap(100, 100)
        backdrop.set_artwork_pixmap(pix)
        self.assertEqual(backdrop._artwork_pixmap, pix)
        backdrop.set_artwork_pixmap(None)
        self.assertIsNone(backdrop._artwork_pixmap)


class TestDiscDetectionWorker(unittest.TestCase):
    def test_worker_fallback_for_unindexed_disc(self):
        from unittest.mock import MagicMock, patch
        from lazycdripper.disc.drive import DriveInfo
        from lazycdripper.disc.toc import DiscTOC, TrackTOC
        from lazycdripper.gui.main_window import DiscDetectionWorker

        mock_toc = DiscTOC(
            first_track=1,
            last_track=2,
            leadout_sector=20000,
            tracks=[
                TrackTOC(track_number=1, start_sector=150, end_sector=10000, length_sectors=9850),
                TrackTOC(track_number=2, start_sector=10000, end_sector=20000, length_sectors=10000),
            ],
            disc_id="test_disc_id_12345678901234",
        )

        worker = DiscDetectionWorker(target_device="D:", is_manual=True, metadata_service=None)
        emitted_results = []

        if hasattr(worker, "detection_finished"):
            worker.detection_finished.connect(lambda *args: emitted_results.append(args))

        with patch("lazycdripper.gui.main_window.detect_optical_drives", return_value=[DriveInfo("D:", "CD Drive", True)]), \
             patch("lazycdripper.gui.main_window.get_disc_toc", return_value=mock_toc):
            worker.run()

        self.assertEqual(len(emitted_results), 1)
        drives, toc, album, is_manual = emitted_results[0]
        self.assertEqual(len(drives), 1)
        self.assertIsNotNone(toc)
        self.assertIsNotNone(album)
        self.assertEqual(album.title, "Audio CD (2 Tracks)")
        self.assertEqual(album.artist, "Unknown Artist")
        self.assertEqual(len(album.tracks), 2)
        self.assertTrue(is_manual)

    def test_worker_skips_network_when_disc_already_loaded(self):
        from unittest.mock import MagicMock, patch
        from lazycdripper.disc.drive import DriveInfo
        from lazycdripper.disc.toc import DiscTOC, TrackTOC
        from lazycdripper.gui.main_window import DiscDetectionWorker

        mock_toc = DiscTOC(
            first_track=1,
            last_track=2,
            leadout_sector=20000,
            tracks=[
                TrackTOC(track_number=1, start_sector=150, end_sector=10000, length_sectors=9850),
                TrackTOC(track_number=2, start_sector=10000, end_sector=20000, length_sectors=10000),
            ],
            disc_id="loaded_disc_id_abc",
        )

        mock_metadata_service = MagicMock()
        worker = DiscDetectionWorker(
            target_device="D:",
            is_manual=False,
            metadata_service=mock_metadata_service,
            current_disc_id="loaded_disc_id_abc",
        )
        emitted_results = []
        if hasattr(worker, "detection_finished"):
            worker.detection_finished.connect(lambda *args: emitted_results.append(args))

        with patch("lazycdripper.gui.main_window.detect_optical_drives", return_value=[DriveInfo("D:", "CD Drive", True)]), \
             patch("lazycdripper.gui.main_window.get_disc_toc", return_value=mock_toc):
            worker.run()

        self.assertEqual(len(emitted_results), 1)
        drives, toc, album, is_manual = emitted_results[0]
        self.assertEqual(toc.disc_id, "loaded_disc_id_abc")
        self.assertIsNone(album)
        self.assertFalse(is_manual)
        mock_metadata_service.resolve_album_metadata.assert_not_called()

    def test_worker_multi_drive_auto_lock(self):
        from unittest.mock import MagicMock, patch
        from lazycdripper.disc.drive import DriveInfo
        from lazycdripper.disc.toc import DiscTOC, TrackTOC
        from lazycdripper.gui.main_window import DiscDetectionWorker

        mock_toc = DiscTOC(
            first_track=1,
            last_track=1,
            leadout_sector=10000,
            tracks=[
                TrackTOC(track_number=1, start_sector=150, end_sector=10000, length_sectors=9850),
            ],
            disc_id="disc_in_e_drive",
        )

        drives = [
            DriveInfo(device_path=r"\\.\D:", name="[D:] Internal DVD", is_ready=True, drive_letter="D:"),
            DriveInfo(device_path=r"\\.\E:", name="[E:] USB CD Drive", is_ready=True, drive_letter="E:"),
        ]

        def mock_get_toc(dev):
            if dev == r"\\.\E:":
                return mock_toc
            return None

        worker = DiscDetectionWorker(target_device=None, is_manual=False)
        emitted_results = []
        if hasattr(worker, "detection_finished"):
            worker.detection_finished.connect(lambda *args: emitted_results.append(args))

        with patch("lazycdripper.gui.main_window.detect_optical_drives", return_value=drives), \
             patch("lazycdripper.gui.main_window.get_disc_toc", side_effect=mock_get_toc):
            worker.run()

        self.assertEqual(len(emitted_results), 1)
        res_drives, toc, album, _ = emitted_results[0]
        self.assertIsNotNone(toc)
        self.assertEqual(toc.disc_id, "disc_in_e_drive")
        # Drive E: was automatically moved to the front because it contains the active audio CD!
        self.assertEqual(res_drives[0].device_path, r"\\.\E:")

    def test_worker_progressive_hydration(self):
        from unittest.mock import MagicMock, patch
        from lazycdripper.disc.drive import DriveInfo
        from lazycdripper.disc.toc import DiscTOC, TrackTOC
        from lazycdripper.core.models import AlbumInfo, TrackInfo
        from lazycdripper.gui.main_window import DiscDetectionWorker

        mock_toc = DiscTOC(
            first_track=1,
            last_track=2,
            leadout_sector=20000,
            tracks=[
                TrackTOC(track_number=1, start_sector=150, end_sector=10000, length_sectors=9850),
                TrackTOC(track_number=2, start_sector=10000, end_sector=20000, length_sectors=10000),
            ],
            disc_id="progressive_disc_id_xyz",
        )
        full_album = AlbumInfo(
            title="A Rush of Blood to the Head",
            artist="Coldplay",
            album_artist="Coldplay",
            tracks=[
                TrackInfo(track_number=1, title="Politik", artist="Coldplay", duration_seconds=318.0),
                TrackInfo(track_number=2, title="In My Place", artist="Coldplay", duration_seconds=228.0),
            ],
        )

        mock_metadata_service = MagicMock()
        mock_metadata_service.resolve_album_metadata.return_value = full_album

        worker = DiscDetectionWorker(
            target_device="D:",
            is_manual=True,
            metadata_service=mock_metadata_service,
            current_disc_id=None,
        )

        toc_results = []
        meta_results = []
        finish_results = []

        if hasattr(worker, "toc_detected"):
            worker.toc_detected.connect(lambda *args: toc_results.append(args))
        if hasattr(worker, "metadata_resolved"):
            worker.metadata_resolved.connect(lambda *args: meta_results.append(args))
        if hasattr(worker, "detection_finished"):
            worker.detection_finished.connect(lambda *args: finish_results.append(args))

        with patch("lazycdripper.gui.main_window.detect_optical_drives", return_value=[DriveInfo("D:", "CD Drive", True)]), \
             patch("lazycdripper.gui.main_window.get_disc_toc", return_value=mock_toc):
            worker.run()

        # 1. Instant toc_detected signal emitted first with basic album
        self.assertEqual(len(toc_results), 1)
        drives, toc, basic_album, is_manual = toc_results[0]
        self.assertEqual(basic_album.title, "Audio CD (2 Tracks)")
        self.assertEqual(basic_album.artist, "Unknown Artist")
        self.assertEqual(len(basic_album.tracks), 2)

        # 2. metadata_resolved signal emitted with full album
        self.assertEqual(len(meta_results), 1)
        res_toc, resolved_album = meta_results[0]
        self.assertEqual(resolved_album.title, "A Rush of Blood to the Head")
        self.assertEqual(resolved_album.artist, "Coldplay")

        # 3. detection_finished signal emitted with full album
        self.assertEqual(len(finish_results), 1)
        self.assertEqual(finish_results[0][2].title, "A Rush of Blood to the Head")


class TestTrackTableWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from PySide6.QtWidgets import QApplication
            cls._app = QApplication.instance() or QApplication(["-platform", "offscreen"])
        except ImportError:
            cls._app = None

    def test_table_columns_and_formatting(self):
        from lazycdripper.gui.widgets.track_table import TrackTableWidget, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        widget = TrackTableWidget()
        self.assertEqual(widget.table.columnCount(), 4)
        labels = [widget.table.horizontalHeaderItem(i).text() for i in range(4)]
        self.assertEqual(labels, ["#", "Title", "Artist", "Time"])
        self.assertNotIn("Master Format", labels)

        from lazycdripper.core.models import TrackInfo
        tracks = [
            TrackInfo(track_number=1, title="Track One", artist="Artist One", duration_seconds=185.0),
        ]
        widget.set_tracks(tracks)
        self.assertEqual(widget.table.rowCount(), 1)
        self.assertEqual(widget.table.item(0, 0).text(), "01")
        self.assertEqual(widget.table.item(0, 1).text(), "Track One")
        self.assertEqual(widget.table.item(0, 2).text(), "Artist One")
        self.assertEqual(widget.table.item(0, 3).text(), "03:05")

    def test_credits_dialog_initialization(self):
        from lazycdripper.gui.widgets.credits_dialog import CreditsDialog, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        dialog = CreditsDialog()
        self.assertEqual("Credits — Lazy CD Ripper", dialog.windowTitle())

    def test_main_window_clean_title(self):
        from lazycdripper.gui.main_window import MainWindow, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication, QLabel
        from unittest.mock import patch
        app = QApplication.instance() or QApplication([])

        with patch("lazycdripper.gui.main_window.detect_optical_drives", return_value=[]):
            from lazycdripper import __codename__, __version__
            window = MainWindow()
            self.assertEqual(window.windowTitle(), "Lazy CD Ripper")
            self.assertEqual(window.version_label.text(), f"v{__version__} • {__codename__} • Credits")
            self.assertEqual(window.version_label.objectName(), "chassisVersionLabel")
            policy_labels = window.findChildren(QLabel, "policyCard")
            self.assertEqual(len(policy_labels), 1)
            text = policy_labels[0].text()
            self.assertIn("320k", text)
            self.assertIn("Level 8", text)
            self.assertIn("LAME", text)
            self.assertIn("Perfect CD copy", text)
            self.assertIn("Compressed but still great", text)
            self.assertIn("bit-perfect", text)

            # Window default geometry tests
            self.assertEqual(window.minimumSize().width(), 1020)
            self.assertEqual(window.minimumSize().height(), 700)
            self.assertEqual(window.sizeHint().width(), 1020)
            self.assertEqual(window.sizeHint().height(), 700)
            self.assertEqual(window.minimumSizeHint().width(), 1020)
            self.assertEqual(window.minimumSizeHint().height(), 700)
            self.assertEqual(window.main_deck.sizeHint().width(), 1020)
            self.assertEqual(window.main_deck.sizeHint().height(), 700)
            self.assertEqual(window.main_deck.minimumSizeHint().width(), 1020)
            self.assertEqual(window.main_deck.minimumSizeHint().height(), 700)
            self.assertEqual(window.ripping_page.sizeHint().width(), 1020)
            self.assertEqual(window.ripping_page.sizeHint().height(), 700)
            self.assertEqual(window.ripping_page.minimumSizeHint().width(), 1020)
            self.assertEqual(window.ripping_page.minimumSizeHint().height(), 700)
            self.assertEqual(window.track_table.sizeHint().width(), 600)
            self.assertEqual(window.track_table.sizeHint().height(), 360)
            self.assertEqual(window.track_table.minimumSizeHint().width(), 400)
            self.assertEqual(window.track_table.minimumSizeHint().height(), 200)

            # Metadata source provenance label tests
            self.assertTrue(window.album_source_label.isHidden())
            window._load_mock_demo_disc()
            self.assertFalse(window.album_source_label.isHidden())
            self.assertIn("MusicBrainz", window.album_source_label.text())

            # Integrated Hi-Fi Rack Brand Faceplate tests
            self.assertEqual(window.brand_title_label.text(), "LAZY CD RIPPER")
            self.assertEqual(window.brand_subtitle_label.text(), "AN ALBUM IS AN EXPERIENCE, NOT A STREAM")

            window._set_empty_state()
            self.assertTrue(window.album_source_label.isHidden())

    def test_main_window_instant_drive_population_on_startup(self):
        from lazycdripper.gui.main_window import MainWindow, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication
        from unittest.mock import patch
        from lazycdripper.disc.drive import DriveInfo
        app = QApplication.instance() or QApplication([])

        mock_drives = [
            DriveInfo(device_path=r"\\.\D:", name="[D:] Plextor Premium", is_ready=True, drive_letter="D:"),
        ]
        with patch("lazycdripper.gui.main_window.detect_optical_drives", return_value=mock_drives):
            window = MainWindow()
            self.assertEqual(len(window.current_drives), 1)
            self.assertIsNotNone(window.active_drive)
            self.assertEqual(window.album_artist_label.text(), "OPTICAL DRIVE READY")
            self.assertFalse(window.album_artist_label.isHidden())
            self.assertEqual(window.album_title_label.text(), "Insert audio CD")
            self.assertEqual(window.album_meta_label.text(), "[D:] Plextor Premium ready")

    def test_main_window_progressive_detection_slots(self):
        from lazycdripper.gui.main_window import MainWindow, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication
        from unittest.mock import patch
        from lazycdripper.disc.drive import DriveInfo
        from lazycdripper.disc.toc import DiscTOC, TrackTOC
        from lazycdripper.core.models import AlbumInfo, TrackInfo
        app = QApplication.instance() or QApplication([])

        with patch("lazycdripper.gui.main_window.detect_optical_drives", return_value=[]):
            window = MainWindow()

            toc = DiscTOC(first_track=1, last_track=1, leadout_sector=10000, tracks=[
                TrackTOC(track_number=1, start_sector=150, end_sector=10000, length_sectors=9850)
            ], disc_id="disc_instant_test")

            basic = AlbumInfo(
                title="Audio CD (1 Tracks)",
                artist="Unknown Artist",
                album_artist="Unknown Artist",
                tracks=[TrackInfo(track_number=1, title="Track 01", artist="Unknown Artist", duration_seconds=131.0)],
            )

            # 1. Trigger _on_toc_detected (in-flight hardware lock & query state)
            window._on_toc_detected([], toc, basic, False)
            self.assertEqual(window.album_title_label.text(), "Fetching Metadata...")
            self.assertIn("Querying MusicBrainz", window.album_source_label.text())
            self.assertEqual(window.track_table.table.rowCount(), 1)
            self.assertFalse(window.btn_rip.isEnabled())
            self.assertEqual(window.btn_rip.text(), "Rip to FLAC + MP3")

            # 2. Trigger _on_metadata_resolved (online metadata lock & ready to rip)
            full = AlbumInfo(
                title="Parachutes",
                artist="Coldplay",
                album_artist="Coldplay",
                tracks=[TrackInfo(track_number=1, title="Don't Panic", artist="Coldplay", duration_seconds=131.0)],
                musicbrainz_release_id="mbid-coldplay-123",
            )
            window._on_metadata_resolved(toc, full)
            self.assertEqual(window.album_title_label.text(), "Parachutes")
            self.assertEqual(window.album_artist_label.text(), "COLDPLAY")
            self.assertIn("MusicBrainz", window.album_source_label.text())
            self.assertTrue(window.btn_rip.isEnabled())
            self.assertEqual(window.btn_rip.text(), "Rip to FLAC + MP3")

    def test_artwork_card_widget_alignment(self):
        from lazycdripper.gui.widgets.artwork_card import ArtworkCardWidget, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication
        from lazycdripper.core.models import AlbumInfo, ArtworkCandidate
        app = QApplication.instance() or QApplication([])

        widget = ArtworkCardWidget()
        self.assertEqual(widget.width(), 280)
        self.assertEqual(widget.height(), 280)
        self.assertEqual(widget.frame.objectName(), "artworkFrame")
        self.assertEqual(widget.frame.width(), 280)
        self.assertEqual(widget.frame.height(), 280)
        self.assertEqual(widget.image_label.width(), 268)
        self.assertEqual(widget.image_label.height(), 268)
        self.assertFalse(widget.acceptDrops())

        # Test crop and rounded rect with QPixmap
        from PySide6.QtGui import QPixmap
        pix = QPixmap(400, 300)
        cropped = widget._prepare_cover_pixmap(pix, target_size=268, radius=8)
        self.assertEqual(cropped.width(), 268)
        self.assertEqual(cropped.height(), 268)

    def test_artwork_card_crop_fallback_when_null(self):
        from lazycdripper.gui.widgets.artwork_card import ArtworkCardWidget
        widget = ArtworkCardWidget()
        # Ensure _prepare_cover_pixmap handles None or null safely
        self.assertIsNone(widget._prepare_cover_pixmap(None))

    def test_artwork_card_placeholder_platter(self):
        from lazycdripper.gui.widgets.artwork_card import ArtworkCardWidget, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        widget = ArtworkCardWidget()

        platter = widget._draw_machined_platter(268, 268)
        self.assertFalse(platter.isNull())
        self.assertGreaterEqual(platter.devicePixelRatio(), 1.0)
        self.assertGreaterEqual(platter.width(), 268)
        self.assertGreaterEqual(platter.height(), 268)

    def test_artwork_card_album_display(self):
        from pathlib import Path
        import tempfile
        from lazycdripper.gui.widgets.artwork_card import ArtworkCardWidget, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QColor, QPixmap
        app = QApplication.instance() or QApplication(["-platform", "offscreen"])
        widget = ArtworkCardWidget()

        # Initial state should show placeholder
        self.assertIsNone(widget.current_pixmap)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = Path(f.name)

        try:
            pix = QPixmap(50, 50)
            pix.fill(QColor("blue"))
            pix.save(str(temp_path), "PNG")

            from lazycdripper.core.models import AlbumInfo, ArtworkCandidate
            candidate = ArtworkCandidate(
                image_id="caa_123",
                url="https://coverartarchive.org/release/123/front.jpg",
                local_cache_path=temp_path,
            )
            album = AlbumInfo(
                title="Test Album",
                artist="Test Artist",
                album_artist="Test Artist",
                selected_artwork=candidate,
                artwork_candidates=[candidate],
            )

            widget.set_album(album)
            self.assertIsNotNone(widget.current_pixmap)
            self.assertFalse(widget.image_label.pixmap().isNull())

            # Setting album to None should revert to placeholder
            widget.set_album(None)
            self.assertIsNone(widget.current_pixmap)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_main_window_provenance_label(self):
        """Verify provenance label reflects MusicBrainz / Cover Art Archive without custom upload."""
        from unittest.mock import MagicMock
        from lazycdripper.gui.main_window import MainWindow
        from lazycdripper.core.models import AlbumInfo, ArtworkCandidate

        win = MainWindow.__new__(MainWindow)
        win.album_title_label = MagicMock()
        win.album_artist_label = MagicMock()
        win.album_meta_label = MagicMock()
        win.album_source_label = MagicMock()
        win.artwork_card = MagicMock()
        win.backdrop = MagicMock()
        win.track_table = MagicMock()
        win.btn_rip = MagicMock()
        win._get_current_artwork_pixmap = MagicMock(return_value=None)

        # 1. With MusicBrainz and CAA artwork
        candidate = ArtworkCandidate(image_id="art1", url="http://example.com/art.jpg")
        album = AlbumInfo(
            title="Online Title",
            artist="Online Artist",
            album_artist="Online Artist",
            musicbrainz_release_id="mb-123",
            artwork_candidates=[candidate],
            selected_artwork=candidate,
        )
        win._populate_album(album)
        win.album_source_label.setText.assert_called_with("Metadata: MusicBrainz  •  Artwork: Cover Art Archive")

        # 2. Offline / unindexed CD
        offline_album = AlbumInfo(title="Audio CD", artist="Various Artists", album_artist="Various Artists")
        win._populate_album(offline_album)
        win.album_source_label.setVisible.assert_called_with(False)

    def test_progressive_detection_query_state(self):
        """Verify in-flight querying state disables Rip button and displays illuminated indicator."""
        from unittest.mock import MagicMock
        from lazycdripper.gui.main_window import MainWindow
        from lazycdripper.core.models import AlbumInfo, TrackInfo
        from lazycdripper.disc.toc import DiscTOC, TrackTOC

        win = MainWindow.__new__(MainWindow)
        win.album_title_label = MagicMock()
        win.album_artist_label = MagicMock()
        win.album_meta_label = MagicMock()
        win.album_source_label = MagicMock()
        win.artwork_card = MagicMock()
        win.backdrop = MagicMock()
        win.track_table = MagicMock()
        win.btn_rip = MagicMock()
        win._loaded_disc_id = None
        win.current_album = None
        win._is_ripping = False
        win._get_current_artwork_pixmap = MagicMock(return_value=None)
        win._update_drive_combo = MagicMock()

        toc = DiscTOC(
            first_track=1,
            last_track=1,
            leadout_sector=10000,
            tracks=[TrackTOC(track_number=1, start_sector=150, end_sector=10000, length_sectors=9850)],
            disc_id="disc_123",
        )
        basic = AlbumInfo(
            title="Audio CD (1 Tracks)",
            artist="Unknown Artist",
            album_artist="Unknown Artist",
            tracks=[TrackInfo(track_number=1, title="Track 01", artist="Unknown Artist", duration_seconds=131.0)],
        )

        # 1. Hardware TOC detected: In-flight metadata query state
        win._on_toc_detected([], toc, basic, False)
        win.album_artist_label.setText.assert_called_with("OPTICAL DISC DETECTED")
        win.album_title_label.setText.assert_called_with("Fetching Metadata...")
        win.album_source_label.setText.assert_called_with("◌  Querying MusicBrainz & Cover Art Archive...")
        win.btn_rip.setEnabled.assert_called_with(False)
        win.btn_rip.setText.assert_not_called()

        # 2. Metadata resolved online
        resolved = AlbumInfo(
            title="The Dark Side of the Moon",
            artist="Pink Floyd",
            album_artist="Pink Floyd",
            musicbrainz_release_id="mb-456",
            tracks=[TrackInfo(track_number=1, title="Speak to Me", artist="Pink Floyd", duration_seconds=68.0)],
        )
        win._on_metadata_resolved(toc, resolved)
        win.album_title_label.setText.assert_called_with("The Dark Side of the Moon")
        win.album_artist_label.setText.assert_called_with("PINK FLOYD")
        win.btn_rip.setEnabled.assert_called_with(True)

        # 3. Fallback when unindexed / offline
        win._on_metadata_resolved(toc, basic)
        win.album_title_label.setText.assert_called_with("Audio CD (1 Tracks)")
        win.album_source_label.setVisible.assert_called_with(False)
        win.btn_rip.setEnabled.assert_called_with(True)

    def test_platform_windows_helpers(self):
        from lazycdripper.gui.platform_windows import hex_to_colorref, setup_windows_window
        # COLORREF format is 0x00BBGGRR
        self.assertEqual(hex_to_colorref("#25252E"), 0x002E2525)
        self.assertEqual(hex_to_colorref("#0C0C0F"), 0x000F0C0C)
        self.assertEqual(hex_to_colorref("#F2F1EC"), 0x00ECF1F2)
        self.assertEqual(hex_to_colorref("invalid"), 0)

        # On non-Windows platform, setup_windows_window safely returns False without crashing
        self.assertFalse(setup_windows_window(object()))

    def test_completion_dialog_states(self):
        from lazycdripper.gui.widgets.completion_dialog import CompletionDialog, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication, QFrame
        from lazycdripper.core.models import AlbumRipReport, TrackRipReport
        app = QApplication.instance() or QApplication([])

        # Failed report
        fail_rep = AlbumRipReport(
            album_title="Fail Disc",
            artist="Artist",
            total_tracks=2,
            overall_status="failed",
            total_errors=2,
            track_reports=[
                TrackRipReport(track_number=1, title="T1", status="failed"),
                TrackRipReport(track_number=2, title="T2", status="failed"),
            ],
        )
        dlg_fail = CompletionDialog(fail_rep)
        self.assertIsNotNone(dlg_fail)

        # Pristine report (streamlined: no redundant list of zeroes)
        good_rep = AlbumRipReport(
            album_title="Good Disc",
            artist="Artist",
            total_tracks=1,
            overall_status="pristine",
            duration_seconds=371.0,
            track_reports=[
                TrackRipReport(track_number=1, title="T1", status="pristine"),
            ],
        )
        self.assertIn("6m 11s", good_rep.human_readable_summary)
        self.assertIn("100% bit-perfect accuracy", good_rep.human_readable_summary)
        dlg_good = CompletionDialog(good_rep)
        self.assertIsNotNone(dlg_good)
        # Pristine dialog should not contain defect previewCard
        preview_frames = [f for f in dlg_good.findChildren(QFrame) if f.objectName() == "previewCard"]
        self.assertEqual(len(preview_frames), 0)

        # Degraded report with retries
        rec_rep = AlbumRipReport(
            album_title="Scratched Disc",
            artist="Artist",
            total_tracks=1,
            overall_status="recovered",
            total_retries=3,
            track_reports=[
                TrackRipReport(track_number=1, title="T1", status="recovered", read_retries=3),
            ],
        )
        dlg_rec = CompletionDialog(rec_rep)
        rec_preview_frames = [f for f in dlg_rec.findChildren(QFrame) if f.objectName() == "previewCard"]
        self.assertEqual(len(rec_preview_frames), 1)

    def test_track_table_widget_non_selectable(self):
        from lazycdripper.gui.widgets.track_table import TrackTableWidget, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication, QTableWidget
        from lazycdripper.core.models import TrackInfo
        app = QApplication.instance() or QApplication([])

        widget = TrackTableWidget()
        self.assertEqual(widget.table.selectionMode(), QTableWidget.NoSelection)
        self.assertFalse(widget.table.horizontalHeader().sectionsClickable())
        self.assertFalse(widget.table.horizontalHeader().highlightSections())

        tracks = [
            TrackInfo(track_number=1, title="Track 1", artist="Artist", duration_seconds=180.0),
        ]
        widget.set_tracks(tracks)
        item = widget.table.item(0, 1)
        self.assertIsNotNone(item)
        self.assertTrue(bool(item.flags() & Qt.ItemIsEnabled))
        self.assertFalse(bool(item.flags() & Qt.ItemIsSelectable))

    def test_empty_state_transitions(self):
        """Verify empty state switches accurately between no drive and no disc inserted."""
        from unittest.mock import MagicMock
        from lazycdripper.gui.main_window import MainWindow
        from lazycdripper.disc.drive import DriveInfo

        win = MainWindow.__new__(MainWindow)
        win.album_title_label = MagicMock()
        win.album_artist_label = MagicMock()
        win.album_meta_label = MagicMock()
        win.album_source_label = MagicMock()
        win.artwork_card = MagicMock()
        win.backdrop = MagicMock()
        win.track_table = MagicMock()
        win.btn_rip = MagicMock()
        win.current_album = None
        win._loaded_disc_id = None
        win.active_drive = None
        win.current_drives = []

        # 1. No drives detected
        win._set_empty_state()
        win.album_artist_label.setText.assert_called_with("OPTICAL DRIVE")
        win.album_title_label.setText.assert_called_with("No Optical Drive Detected")
        win.album_meta_label.setText.assert_called_with("Connect a USB optical drive to get started")
        win.btn_rip.setEnabled.assert_called_with(False)

        # 2. Drive detected, but empty tray
        win.current_drives = [
            DriveInfo(device_path=r"\\.\D:", name="[D:] ASUS SDRW-08U7M-U", is_ready=True, drive_letter="D:")
        ]
        win._set_empty_state()
        win.album_artist_label.setText.assert_called_with("OPTICAL DRIVE READY")
        win.album_title_label.setText.assert_called_with("Insert audio CD")
        win.album_meta_label.setText.assert_called_with("[D:] ASUS SDRW-08U7M-U ready")
        win.btn_rip.setEnabled.assert_called_with(False)
        win.btn_rip.setText.assert_not_called()

    def test_integrated_hifi_rack_branding(self):
        """Verify Integrated Hi-Fi Rack architecture: top bar removed, brand integrated into left deck."""
        from lazycdripper.gui.main_window import MainWindow

        # Standalone top bar removed in favor of integrated left deck faceplate
        self.assertFalse(hasattr(MainWindow, "_create_top_bar"))
        self.assertTrue(hasattr(MainWindow, "_create_main_deck"))

    def test_ripping_view_completion_and_reset(self):
        """Verify RippingViewWidget native in-screen completion and reset behavior."""
        from lazycdripper.gui.widgets.ripping_view import RippingViewWidget, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from pathlib import Path
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
        from lazycdripper.core.models import AlbumRipReport, TrackRipReport, AlbumInfo

        app = QApplication.instance() or QApplication(["-platform", "offscreen"])

        view = RippingViewWidget()
        view.show()
        self.assertTrue(view.active_container.isVisible())
        self.assertFalse(view.completion_container.isVisible())

        # Test pristine completion
        pristine_rep = AlbumRipReport(
            album_title="Test Pristine",
            artist="Audiophile Artist",
            total_tracks=2,
            overall_status="pristine",
            duration_seconds=120.0,
            destination_directory=Path("/tmp/rip"),
            flac_directory=Path("/tmp/rip/Artist - Album [FLAC]"),
            mp3_directory=Path("/tmp/rip/Artist - Album [MP3]"),
            flac_size_bytes=50 * 1024 * 1024,
            mp3_size_bytes=15 * 1024 * 1024,
            track_reports=[
                TrackRipReport(track_number=1, title="T1", status="pristine"),
                TrackRipReport(track_number=2, title="T2", status="pristine"),
            ],
        )

        done_called = []
        view.show_completion(pristine_rep, on_done=lambda: done_called.append(True))

        self.assertFalse(view.active_container.isVisible())
        self.assertTrue(view.completion_container.isVisible())
        self.assertIn("Rip Complete", view.headline.text())
        self.assertFalse(view.headline.text().startswith("🟢"))
        self.assertTrue(view.status_led.isVisible())
        self.assertFalse(hasattr(view, "defect_card"))
        self.assertTrue(view.output_card.isVisible())
        self.assertIn("Artist - Album [FLAC] - Perfect CD copy", view.flac_dir_label.text())
        self.assertIn("Artist - Album [MP3] - Compressed but still great", view.mp3_dir_label.text())
        self.assertIn("Artist - Album [MP3] - Compressed but still great", view.aac_dir_label.text())
        self.assertIn("50.0 MB", view.flac_dir_label.text())
        self.assertEqual(view.track_label.alignment(), Qt.AlignCenter)
        self.assertEqual(view.overall_label.alignment(), Qt.AlignCenter)
        self.assertEqual(view.flac_dir_label.alignment(), Qt.AlignCenter)
        self.assertEqual(view.mp3_dir_label.alignment(), Qt.AlignCenter)
        self.assertEqual(view.aac_dir_label.alignment(), Qt.AlignCenter)
        self.assertEqual(view.status_sub.alignment(), Qt.AlignCenter)
        # Sloth completion mascot is displayed in place of transport disc
        self.assertTrue(view.sloth_emblem.isVisible())
        self.assertFalse(view.transport_widget.isVisible())

        # Test Done button callback
        view.btn_done.click()
        self.assertEqual(done_called, [True])

        # Test damaged/recovered report shows defects in upper visual card summary
        scratched_rep = AlbumRipReport(
            album_title="Scratched",
            artist="Artist",
            total_tracks=1,
            overall_status="recovered",
            total_retries=5,
            track_reports=[
                TrackRipReport(track_number=1, title="T1", status="recovered", read_retries=5),
            ],
        )
        view.show_completion(scratched_rep)
        self.assertIn("Sector Retries: 5 recovered", view.status_sub.text())
        self.assertTrue(view.status_led.isVisible())

        # Test damaged report with unrecoverable errors (surface damage triggers sad sloth mascot)
        damaged_rep = AlbumRipReport(
            album_title="Damaged",
            artist="Artist",
            total_tracks=2,
            overall_status="degraded",
            total_retries=10,
            total_errors=4,
            track_reports=[
                TrackRipReport(track_number=1, title="T1", status="pristine"),
                TrackRipReport(track_number=2, title="T2", status="degraded", unrecoverable_errors=4),
            ],
        )
        view.show_completion(damaged_rep)
        self.assertIn("Surface Damage Detected", view.headline.text())
        self.assertFalse(view.headline.text().startswith("🔴"))
        self.assertTrue(view.status_led.isVisible())
        self.assertIn("Unrecoverable Skips: 4 sector(s)", view.status_sub.text())
        self.assertTrue(view.sloth_emblem.isVisible())

        # Test reset_view resets containers and states
        view.reset_view()
        self.assertTrue(view.active_container.isVisible())
        self.assertFalse(view.completion_container.isVisible())
        self.assertFalse(view.sloth_emblem.isVisible())
        self.assertFalse(view.status_led.isVisible())
        self.assertTrue(view.transport_widget.isVisible())
        self.assertEqual(view.track_bar.value(), 0)
        self.assertEqual(view.overall_bar.value(), 0)
        self.assertEqual(view.headline.text(), "Extracting Audio Tracks...")

        # Test set_album resets view
        view.show_completion(scratched_rep)
        self.assertTrue(view.completion_container.isVisible())
        view.set_album(AlbumInfo(title="New Album", artist="New Artist", album_artist="New Artist"))
        self.assertTrue(view.active_container.isVisible())
        self.assertFalse(view.completion_container.isVisible())

    def test_ripping_view_emblem_spacing_symmetry(self):
        """Verify symmetrical spacing above and below the center visual emblem."""
        from lazycdripper.gui.widgets.ripping_view import RippingViewWidget, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication, QSpacerItem
        app = QApplication.instance() or QApplication(["-platform", "offscreen"])

        view = RippingViewWidget()
        self.assertTrue(hasattr(view, "emblem_container"))
        self.assertTrue(hasattr(view, "sloth_emblem"))
        self.assertTrue(hasattr(view, "spec_badge"))

        # Verify sloth emblem has clean transparent background without asymmetric margin-bottom
        self.assertNotIn("margin-bottom", view.sloth_emblem.styleSheet())
        self.assertEqual(view.sloth_emblem.width(), 200)
        self.assertEqual(view.sloth_emblem.height(), 200)
        self.assertEqual(view.status_led.width(), 18)
        self.assertEqual(view.status_led.height(), 18)

        # Inspect visual_layout items
        visual_layout = view.visual_frame.layout()
        self.assertEqual(visual_layout.spacing(), 0)

        # Find items in visual_layout
        items = [visual_layout.itemAt(i) for i in range(visual_layout.count())]
        badge_idx = None
        emblem_idx = None
        headline_idx = None

        for idx, item in enumerate(items):
            if item.widget() == view.spec_badge:
                badge_idx = idx
            elif item.widget() == view.emblem_container:
                emblem_idx = idx
            elif item.layout() is not None:
                headline_idx = idx
                break

        self.assertIsNotNone(badge_idx)
        self.assertIsNotNone(emblem_idx)
        self.assertIsNotNone(headline_idx)

        # Spacer between badge and emblem
        spacer_above = items[badge_idx + 1]
        # Spacer between emblem and headline
        spacer_below = items[emblem_idx + 1]

        self.assertIsInstance(spacer_above, QSpacerItem)
        self.assertIsInstance(spacer_below, QSpacerItem)
        # Symmetrical spacing heights must be exactly equal
        self.assertEqual(spacer_above.sizeHint().height(), spacer_below.sizeHint().height())

    def test_dialog_sizes_and_hints(self):
        """Verify all secondary modal dialogs enforce explicit compact size hints."""
        from lazycdripper.gui.widgets.credits_dialog import CreditsDialog, HAVE_QT
        from lazycdripper.gui.widgets.liner_notes_dialog import LinerNotesDialog
        from lazycdripper.gui.widgets.completion_dialog import CompletionDialog
        from lazycdripper.core.models import AlbumRipReport

        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(["-platform", "offscreen"])

        credits_dlg = CreditsDialog()
        self.assertEqual(credits_dlg.minimumSize().width(), 560)
        self.assertEqual(credits_dlg.minimumSize().height(), 520)
        self.assertEqual(credits_dlg.sizeHint().width(), 560)
        self.assertEqual(credits_dlg.sizeHint().height(), 520)
        self.assertEqual(credits_dlg.minimumSizeHint().width(), 560)
        self.assertEqual(credits_dlg.minimumSizeHint().height(), 520)

        notes_dlg = LinerNotesDialog()
        self.assertEqual(notes_dlg.minimumSize().width(), 540)
        self.assertEqual(notes_dlg.minimumSize().height(), 480)
        self.assertEqual(notes_dlg.sizeHint().width(), 540)
        self.assertEqual(notes_dlg.sizeHint().height(), 480)
        self.assertEqual(notes_dlg.minimumSizeHint().width(), 540)
        self.assertEqual(notes_dlg.minimumSizeHint().height(), 480)

        rep = AlbumRipReport(album_title="Test", artist="Artist", total_tracks=1)
        comp_dlg = CompletionDialog(report=rep)
        self.assertEqual(comp_dlg.sizeHint().width(), 540)
        self.assertEqual(comp_dlg.sizeHint().height(), 480)
        self.assertEqual(comp_dlg.minimumSizeHint().width(), 540)
        self.assertEqual(comp_dlg.minimumSizeHint().height(), 480)

    def test_ripping_view_layout_clamping_and_alignment(self):
        """Verify that progress bars and labels have fixed heights and stay tightly clamped on resize."""
        from lazycdripper.gui.widgets.ripping_view import RippingViewWidget, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication, QSizePolicy
        from lazycdripper.core.models import AlbumRipReport

        app = QApplication.instance() or QApplication(["-platform", "offscreen"])
        view = RippingViewWidget()

        # 1. Active container height clamping
        self.assertEqual(view.active_container.maximumHeight(), 214)
        self.assertEqual(view.track_label.maximumHeight(), 18)
        self.assertEqual(view.track_bar.maximumHeight(), 16)
        self.assertEqual(view.overall_label.maximumHeight(), 18)
        self.assertEqual(view.overall_bar.maximumHeight(), 16)
        self.assertEqual(view.badge_retries.maximumHeight(), 24)
        self.assertEqual(view.badge_errors.maximumHeight(), 24)
        self.assertEqual(view.memory_card.maximumHeight(), 72)

        # 2. Alignment checks on active view
        self.assertEqual(view.track_label.alignment(), Qt.AlignCenter)
        self.assertEqual(view.overall_label.alignment(), Qt.AlignCenter)
        self.assertEqual(view.memory_label.alignment(), Qt.AlignCenter)

        # 3. Size policies
        self.assertEqual(view.active_container.sizePolicy().verticalPolicy(), QSizePolicy.Fixed)
        self.assertEqual(view.visual_frame.sizePolicy().verticalPolicy(), QSizePolicy.Fixed)
        self.assertEqual(view.completion_container.sizePolicy().verticalPolicy(), QSizePolicy.Fixed)

        # 4. Alignment checks on completion view (both success and failure)
        rep = AlbumRipReport(album_title="Test", artist="Artist", total_tracks=1, overall_status="pristine")
        view.show_completion(rep)
        self.assertEqual(view.status_sub.alignment(), Qt.AlignCenter)
        self.assertEqual(view.flac_dir_label.alignment(), Qt.AlignCenter)
        self.assertEqual(view.mp3_dir_label.alignment(), Qt.AlignCenter)
        self.assertEqual(view.aac_dir_label.alignment(), Qt.AlignCenter)

    def test_window_custom_size_preserved_across_transitions(self):
        """Verify that user-resized window dimensions are preserved when switching screens."""
        from lazycdripper.gui.main_window import MainWindow, HAVE_QT
        if not HAVE_QT:
            self.skipTest("PySide6 not available in this environment")

        from PySide6.QtWidgets import QApplication
        from lazycdripper.core.models import AlbumRipReport, AlbumInfo, TrackInfo

        app = QApplication.instance() or QApplication(["-platform", "offscreen"])
        window = MainWindow()

        # User resizes window to larger custom dimensions
        window.resize(1350, 880)
        self.assertEqual(window.width(), 1350)
        self.assertEqual(window.height(), 880)

        # Simulate clicking rip / transitioning to ripping screen
        window.current_album = AlbumInfo(
            title="Test Album",
            artist="Test Artist",
            album_artist="Test Artist",
            total_tracks=1,
            tracks=[TrackInfo(track_number=1, title="T1", artist="Test Artist")],
        )
        window.main_stack.setCurrentIndex(1)
        self.assertEqual(window.width(), 1350)
        self.assertEqual(window.height(), 880)

        # Transition to completion screen
        rep = AlbumRipReport(album_title="Test Album", artist="Test Artist", total_tracks=1, overall_status="pristine")
        window._on_rip_completed(rep)
        self.assertEqual(window.width(), 1350)
        self.assertEqual(window.height(), 880)

        # Dismiss back to main screen
        window._on_rip_done_dismiss()
        self.assertEqual(window.width(), 1350)
        self.assertEqual(window.height(), 880)

        # Error dismissal back to main screen
        window.main_stack.setCurrentIndex(1)
        window._on_rip_error("Simulated error")
        self.assertEqual(window.width(), 1350)
        self.assertEqual(window.height(), 880)


if __name__ == "__main__":
    unittest.main()

