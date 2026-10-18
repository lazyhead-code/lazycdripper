from __future__ import annotations

"""Main application window for Lazy CD Ripper with boutique high-end audio craft design."""

import logging
from pathlib import Path
import platform
import sys
from typing import List, Optional

from lazycdripper import __codename__, __version__
from lazycdripper.core.models import (
    AlbumInfo,
    AlbumRipReport,
    RipProgress,
    TrackInfo,
)
from lazycdripper.disc.drive import DriveInfo, detect_optical_drives
from lazycdripper.disc.toc import DiscTOC, get_disc_toc
from lazycdripper.gui.platform_windows import setup_windows_window
from lazycdripper.gui.theme import DARK_ROCK_STYLESHEET
from lazycdripper.gui.widgets.artwork_card import ArtworkCardWidget
from lazycdripper.gui.widgets.credits_dialog import CreditsDialog
from lazycdripper.gui.widgets.ripping_view import RippingViewWidget
from lazycdripper.gui.widgets.track_table import TrackTableWidget
from lazycdripper.metadata.service import MetadataService
from lazycdripper.pipeline.orchestrator import RipPipelineOrchestrator

logger = logging.getLogger(__name__)

try:
    from PySide6.QtCore import QPointF, QSize, QThread, QTimer, Qt, Signal
    from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QRadialGradient
    from PySide6.QtWidgets import (
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    QMainWindow = object
    QWidget = object
    QThread = object
    QIcon = object

    class _MockSignal:
        def __init__(self, *args):
            self._slots = []

        def connect(self, slot):
            self._slots.append(slot)

        def emit(self, *args, **kwargs):
            for s in list(self._slots):
                s(*args, **kwargs)

        def __get__(self, instance, owner):
            if instance is None:
                return self
            attr = f"_mock_sig_{id(self)}"
            if not hasattr(instance, attr):
                setattr(instance, attr, _MockSignal())
            return getattr(instance, attr)

    Signal = _MockSignal
    QPointF = object
    QSize = object
    QPen = object
    QTimer = object


def _get_logo_pixmap() -> Optional[QPixmap]:
    """Locate the brand emblem logo.jpg in frozen bundle or repository root."""
    if not HAVE_QT:
        return None
    candidates = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "assets" / "images" / "logo.jpg")
        candidates.append(Path(sys.executable).parent / "assets" / "images" / "logo.jpg")

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    candidates.append(repo_root / "assets" / "images" / "logo.jpg")

    for p in candidates:
        if p.is_file():
            pm = QPixmap(str(p))
            if not pm.isNull():
                return pm
    return None


def locate_app_icon_path() -> Optional[Path]:
    """Locate brand logo.ico or icon.png in frozen bundle or repository root."""
    candidates = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            for name in ["logo.ico", "icon.png", "logo.jpg"]:
                candidates.append(Path(meipass) / "assets" / "images" / name)
        for name in ["logo.ico", "icon.png", "logo.jpg"]:
            candidates.append(Path(sys.executable).parent / "assets" / "images" / name)

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    for name in ["logo.ico", "icon.png", "logo.jpg"]:
        candidates.append(repo_root / "assets" / "images" / name)

    for p in candidates:
        if p.is_file():
            return p
    return None


class RipWorkerThread(QThread if HAVE_QT else object):
    """Background worker thread executing audio extraction and parallel dual transcoding."""

    progress_signal = Signal(object)      # RipProgress
    completed_signal = Signal(object)     # AlbumRipReport
    error_signal = Signal(str)

    def __init__(
        self,
        orchestrator: RipPipelineOrchestrator,
        album: AlbumInfo,
        output_dir: Path,
        device: Optional[str] = None,
        include_track_number: bool = True,
        include_artist: bool = False,
    ):
        if HAVE_QT:
            super().__init__()
        self.orchestrator = orchestrator
        self.album = album
        self.output_dir = output_dir
        self.device = device
        self.include_track_number = include_track_number
        self.include_artist = include_artist

    def run(self):
        try:
            def on_progress(p: RipProgress):
                self.progress_signal.emit(p)

            report = self.orchestrator.execute_rip(
                album=self.album,
                base_output_dir=self.output_dir,
                device=self.device,
                include_track_number=self.include_track_number,
                include_artist=self.include_artist,
                on_progress=on_progress,
            )
            self.completed_signal.emit(report)
        except Exception as err:
            logger.exception("Rip pipeline encountered an error: %s", err)
            self.error_signal.emit(str(err))


class DiscDetectionWorker(QThread if HAVE_QT else object):
    """Background worker thread that detects drives, reads disc TOC, and resolves metadata without freezing GUI."""

    toc_detected = Signal(list, object, object, bool)        # drives, toc, basic_album, is_manual
    metadata_resolved = Signal(object, object)              # toc, full_album
    detection_finished = Signal(list, object, object, bool)  # drives, toc, album, is_manual

    def __init__(
        self,
        target_device: Optional[str] = None,
        is_manual: bool = False,
        metadata_service: Optional[MetadataService] = None,
        current_disc_id: Optional[str] = None,
    ):
        if HAVE_QT:
            super().__init__()
        self.target_device = target_device
        self.is_manual = is_manual
        self.metadata_service = metadata_service
        self.current_disc_id = current_disc_id

    def run(self):
        try:
            drives = detect_optical_drives()
            toc: Optional[DiscTOC] = None
            album: Optional[AlbumInfo] = None

            # If a specific target device was requested, check it
            if self.target_device:
                toc = get_disc_toc(self.target_device)
            elif drives:
                # Automatically scan all optical drives to find the one with an audio CD
                for drive in drives:
                    t = get_disc_toc(drive.device_path)
                    if t and t.tracks:
                        toc = t
                        # Move the active drive to the front of the drives list so UI knows it's active
                        drives = [drive] + [d for d in drives if d.device_path != drive.device_path]
                        break

            if toc and toc.tracks:
                # Skip querying network repeatedly if disc is already recognized and not a manual refresh
                if not self.is_manual and self.current_disc_id and toc.disc_id == self.current_disc_id:
                    self.detection_finished.emit(drives, toc, None, self.is_manual)
                    return

                # Construct lightweight instant album from physical TOC (< 5ms)
                basic_album = AlbumInfo(
                    title=f"Audio CD ({len(toc.tracks)} Tracks)",
                    artist="Unknown Artist",
                    album_artist="Unknown Artist",
                    tracks=[
                        TrackInfo(
                            track_number=t.track_number,
                            title=f"Track {t.track_number:02d}",
                            artist="Unknown Artist",
                            duration_seconds=t.duration_seconds,
                        )
                        for t in toc.tracks
                    ],
                    total_tracks=len(toc.tracks),
                )
                # Immediate hardware feedback for UI (< 10ms total)
                self.toc_detected.emit(drives, toc, basic_album, self.is_manual)

                # Progressive online metadata resolution (MusicBrainz + Cover Art Archive) in background
                if self.metadata_service:
                    try:
                        album = self.metadata_service.resolve_album_metadata(disc_id=toc.disc_id, toc=toc)
                    except Exception as err:
                        logger.debug("Background metadata lookup error: %s", err)

                resolved_album = album or basic_album
                self.metadata_resolved.emit(toc, resolved_album)
                self.detection_finished.emit(drives, toc, resolved_album, self.is_manual)
                return

            self.toc_detected.emit(drives, None, None, self.is_manual)
            self.detection_finished.emit(drives, None, None, self.is_manual)
        except Exception as err:
            logger.exception("DiscDetectionWorker error: %s", err)
            self.toc_detected.emit([], None, None, self.is_manual)
            self.detection_finished.emit([], None, None, self.is_manual)


class BackgroundBackdropWidget(QWidget if HAVE_QT else object):
    """Draws subtle vintage hi-fi textured background with a dark vignette."""

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAVE_QT:
            return
        super().__init__(parent)
        self._default_pixmap = None
        self._artwork_pixmap: Optional[QPixmap] = None

    def set_artwork_pixmap(self, pixmap: Optional[QPixmap]):
        """Set album artwork to display as subtle ambient background."""
        self._artwork_pixmap = pixmap
        if HAVE_QT and hasattr(self, "update"):
            self.update()

    def paintEvent(self, event):
        if not HAVE_QT:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Base deep chassis color
        painter.fillRect(self.rect(), QColor("#0A0A0D"))

        # Subtle warm dark amber chassis radial vignette
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        radius = max(self.width(), self.height()) * 0.75
        radial = QRadialGradient(center_x, center_y, radius)
        radial.setColorAt(0.0, QColor(24, 20, 18, 90))
        radial.setColorAt(0.65, QColor(14, 14, 18, 140))
        radial.setColorAt(1.0, QColor(10, 10, 13, 255))
        painter.fillRect(self.rect(), radial)

        # Atmospheric ambient album artwork if available
        if self._artwork_pixmap and not self._artwork_pixmap.isNull():
            scaled = self._artwork_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.setOpacity(0.25)
            painter.drawPixmap(x, y, scaled)

            # Soft dark radial vignette so text & cards maintain pristine contrast
            painter.setOpacity(1.0)
            art_radial = QRadialGradient(center_x, center_y, radius)
            art_radial.setColorAt(0.0, QColor(10, 10, 13, 85))
            art_radial.setColorAt(0.65, QColor(10, 10, 13, 175))
            art_radial.setColorAt(1.0, QColor(10, 10, 13, 238))
            painter.fillRect(self.rect(), art_radial)


class MainDeckWidget(QWidget if HAVE_QT else object):
    """The single unified main screen housing the hardware controls and track deck."""

    def sizeHint(self):
        if HAVE_QT:
            return QSize(1020, 700)
        return super().sizeHint() if hasattr(super(), "sizeHint") else None

    def minimumSizeHint(self):
        if HAVE_QT:
            return QSize(1020, 700)
        return super().minimumSizeHint() if hasattr(super(), "minimumSizeHint") else None


class MainWindow(QMainWindow if HAVE_QT else object):
    """Boutique High-End Audio Equipment Main Window."""

    def __init__(
        self,
        metadata_service: Optional[MetadataService] = None,
        orchestrator: Optional[RipPipelineOrchestrator] = None,
    ):
        if not HAVE_QT:
            return
        super().__init__()

        self.metadata_service = metadata_service or MetadataService()
        self.orchestrator = orchestrator or RipPipelineOrchestrator()

        # Ensure audio encoder is available in background if not already found
        if not getattr(self.orchestrator.encoder, "is_available", False):
            import threading
            from lazycdripper.core.binaries import ensure_ffmpeg
            threading.Thread(target=ensure_ffmpeg, daemon=True).start()

        self.current_album: Optional[AlbumInfo] = None
        self.current_drives: List[DriveInfo] = []
        self.active_drive: Optional[DriveInfo] = None
        self._loaded_disc_id: Optional[str] = None
        self._is_ripping: bool = False
        self.worker_thread: Optional[RipWorkerThread] = None
        self.detection_worker: Optional[DiscDetectionWorker] = None
        self.auto_scan_timer: Optional[QTimer] = None
        self._hotplug_timer: Optional[QTimer] = None
        self.last_destination_dir: Optional[str] = None

        self.setWindowTitle("Lazy CD Ripper")
        self.setMinimumSize(1020, 700)
        self.resize(1020, 700)
        self.setStyleSheet(DARK_ROCK_STYLESHEET)

        icon_path = locate_app_icon_path()
        if icon_path and HAVE_QT:
            self.setWindowIcon(QIcon(str(icon_path)))

        self._setup_ui()
        if HAVE_QT:
            self.resize(1020, 700)

        # Synchronously populate detected optical drives on Frame 1 (< 0.1ms on Windows)
        initial_drives = detect_optical_drives()
        self._update_drives(initial_drives)
        self._set_empty_state()

        # Immediate disc detection on startup
        self._trigger_detection(is_manual=False)

        if HAVE_QT:
            # Staggered fast probes on startup to catch drives/media spinning up immediately
            QTimer.singleShot(150, lambda: self._trigger_detection(is_manual=False))
            QTimer.singleShot(500, lambda: self._trigger_detection(is_manual=False))
            QTimer.singleShot(1000, lambda: self._trigger_detection(is_manual=False))

            self.auto_scan_timer = QTimer(self)
            self.auto_scan_timer.setInterval(1500)
            self.auto_scan_timer.timeout.connect(self._on_auto_scan_poll)
            self.auto_scan_timer.start()

    def sizeHint(self):
        if HAVE_QT:
            return QSize(1020, 700)
        return super().sizeHint() if hasattr(super(), "sizeHint") else None

    def minimumSizeHint(self):
        if HAVE_QT:
            return QSize(1020, 700)
        return super().minimumSizeHint() if hasattr(super(), "minimumSizeHint") else None

    def showEvent(self, event):
        if HAVE_QT:
            super().showEvent(event)
            setup_windows_window(self)
            if not self.isMaximized():
                self.resize(1020, 700)
            # Ensure detection fires when window first renders
            QTimer.singleShot(50, lambda: self._trigger_detection(is_manual=False))

    def _setup_ui(self):
        self.backdrop = BackgroundBackdropWidget(self)
        self.setCentralWidget(self.backdrop)

        root_layout = QVBoxLayout(self.backdrop)
        root_layout.setContentsMargins(24, 22, 24, 22)
        root_layout.setSpacing(0)

        # Central Deck Area (QStackedWidget: 0: Main Screen, 1: Active Ripping View)
        self.main_stack = QStackedWidget()

        self.main_deck = self._create_main_deck()
        self.main_stack.addWidget(self.main_deck)

        self.ripping_page = RippingViewWidget()
        self.main_stack.addWidget(self.ripping_page)

        root_layout.addWidget(self.main_stack, stretch=1)

    def _create_main_deck(self) -> QWidget:
        """The single unified main screen housing the hardware controls and track deck."""
        deck = MainDeckWidget()
        layout = QHBoxLayout(deck)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(28)

        # LEFT DECK: Physical Media & Hardware Switches (Fixed width 280px)
        left_container = QWidget()
        left_container.setFixedWidth(280)
        left_deck = QVBoxLayout(left_container)
        left_deck.setContentsMargins(0, 0, 0, 0)
        left_deck.setSpacing(14)

        # 1. Brand Title & Audiophile Manifesto Plaque (Integrated Hi-Fi Rack Faceplate)
        brand_container = QVBoxLayout()
        brand_container.setSpacing(3)
        brand_container.setContentsMargins(0, 0, 0, 4)
        if HAVE_QT:
            brand_container.setAlignment(Qt.AlignLeft)

        # Row 1: Brand Title (Clean architectural lettering)
        self.brand_title_label = QLabel("LAZY CD RIPPER")
        self.brand_title_label.setObjectName("brandTitleLabel")
        self.brand_title_label.setStyleSheet(
            "font-size: 16px; font-weight: 800; color: #FF9E3B; letter-spacing: 2px;"
        )
        brand_container.addWidget(self.brand_title_label)

        # Row 2: Audiophile Manifesto
        self.brand_subtitle_label = QLabel(
            "AN ALBUM IS AN EXPERIENCE, NOT A STREAM"
        )
        self.brand_subtitle_label.setObjectName("brandSubtitleLabel")
        self.brand_subtitle_label.setStyleSheet(
            "font-size: 9px; font-weight: 600; color: #727180; letter-spacing: 1.2px;"
        )
        brand_container.addWidget(self.brand_subtitle_label)

        left_deck.addLayout(brand_container)

        # Jewel-case artwork frame (280x280) displaying canonical Cover Art
        self.artwork_card = ArtworkCardWidget()
        left_deck.addWidget(self.artwork_card, alignment=Qt.AlignHCenter)

        # Push action controls to the bottom
        left_deck.addStretch()

        # The Master Rip Switch: Large Glowing Amber Push Button
        self.btn_rip = QPushButton("Rip to FLAC + MP3")
        self.btn_rip.setObjectName("primaryRipButton")
        self.btn_rip.setEnabled(False)
        self.btn_rip.clicked.connect(lambda: self._start_rip())
        left_deck.addWidget(self.btn_rip)

        # Precision Output Specification Plaque (Dual FLAC + MP3)
        policy_note = QLabel(
            "<table width='100%' cellpadding='0' cellspacing='0' style='border: none;'>"
            "<tr>"
            "<td width='12' valign='top' style='color: #FF9E3B; font-size: 8px; padding-top: 2px;'>●</td>"
            "<td style='padding-bottom: 10px;'>"
            "<div style='color: #E2E1E6; font-size: 10px; font-weight: bold; letter-spacing: 0.3px;'>FLAC LOSSLESS (Perfect CD copy)</div>"
            "<div style='color: #8E8D96; font-size: 9px; margin-top: 3px; line-height: 1.35;'>"
            "Audio CD 16-bit / 44.1 kHz bit-perfect master.<br>"
            "Archival compression (Level 8) with MD5 stream verify."
            "</div>"
            "</td>"
            "</tr>"
            "<tr>"
            "<td width='12' valign='top' style='color: #FF9E3B; font-size: 8px; padding-top: 2px;'>●</td>"
            "<td>"
            "<div style='color: #E2E1E6; font-size: 10px; font-weight: bold; letter-spacing: 0.3px;'>MP3 320k (Compressed but still great)</div>"
            "<div style='color: #8E8D96; font-size: 9px; margin-top: 3px; line-height: 1.35;'>"
            "LAME MP3 (320 kbps CBR / Quality 0 in .mp3).<br>"
            "100% patent-free, universal hardware playback."
            "</div>"
            "</td>"
            "</tr>"
            "</table>"
        )
        policy_note.setObjectName("policyCard")
        policy_note.setWordWrap(True)

        policy_container = QVBoxLayout()
        policy_container.setSpacing(6)
        policy_container.setContentsMargins(0, 0, 0, 0)
        policy_container.addWidget(policy_note)

        # Subtle laser-etched chassis version plate (Clickable to open Credits dialog)
        self.version_label = QLabel(f"v{__version__} • {__codename__} • Credits")
        self.version_label.setObjectName("chassisVersionLabel")
        self.version_label.setStyleSheet(
            "QLabel#chassisVersionLabel { "
            "  font-size: 8px; font-weight: 600; color: #42424E; letter-spacing: 1px; padding-left: 2px; "
            "} "
            "QLabel#chassisVersionLabel:hover { "
            "  color: #FF9E3B; "
            "}"
        )
        self.version_label.setToolTip(
            f'Lazy CD Ripper v{__version__} "{__codename__}"\n'
            "Click to view Credits & License"
        )
        if HAVE_QT:
            self.version_label.setCursor(Qt.PointingHandCursor)
            self.version_label.mousePressEvent = self._on_version_label_clicked
            policy_container.addWidget(self.version_label, alignment=Qt.AlignLeft)
        else:
            policy_container.addWidget(self.version_label)

        left_deck.addLayout(policy_container)

        layout.addWidget(left_container)

        # RIGHT DECK: Master Recording Metadata & Track Display (Flex stretch)
        right_deck = QVBoxLayout()
        right_deck.setSpacing(12)

        # 1. Metadata Header Card
        self.header_card = QFrame()
        self.header_card.setObjectName("cardPanel")
        h_layout = QVBoxLayout(self.header_card)
        h_layout.setContentsMargins(18, 14, 18, 14)
        h_layout.setSpacing(3)

        self.album_artist_label = QLabel("OPTICAL DRIVE")
        self.album_artist_label.setStyleSheet(
            "font-size: 11px; color: #FF9E3B; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;"
        )
        self.album_artist_label.setVisible(True)
        h_layout.addWidget(self.album_artist_label)

        self.album_title_label = QLabel("Insert audio CD")
        self.album_title_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #F2F1EC;")
        h_layout.addWidget(self.album_title_label)

        self.album_meta_label = QLabel("")
        self.album_meta_label.setStyleSheet("font-size: 11px; color: #72717E; font-weight: 500;")
        self.album_meta_label.setVisible(False)
        h_layout.addWidget(self.album_meta_label)

        self.album_source_label = QLabel("")
        self.album_source_label.setStyleSheet("font-size: 11px; color: #646372; font-weight: 500;")
        self.album_source_label.setVisible(False)
        if HAVE_QT:
            h_layout.addWidget(self.album_source_label, alignment=Qt.AlignLeft)
        else:
            h_layout.addWidget(self.album_source_label)

        right_deck.addWidget(self.header_card)

        # 2. Precision Track Table (Takes full remaining vertical and horizontal space)
        self.track_table = TrackTableWidget()
        right_deck.addWidget(self.track_table, stretch=1)

        layout.addLayout(right_deck, stretch=1)

        return deck

    def _trigger_detection(self, target_device: Optional[str] = None, is_manual: bool = False):
        """Asynchronously inspect optical drives and loaded CD TOC without blocking GUI."""
        if self._is_ripping:
            return
        if self.detection_worker and self.detection_worker.isRunning():
            return

        dev = target_device or (self.active_drive.device_path if self.active_drive else None)

        self.detection_worker = DiscDetectionWorker(
            target_device=dev,
            is_manual=is_manual,
            metadata_service=self.metadata_service,
            current_disc_id=self._loaded_disc_id,
        )
        self.detection_worker.toc_detected.connect(self._on_toc_detected)
        self.detection_worker.metadata_resolved.connect(self._on_metadata_resolved)
        self.detection_worker.detection_finished.connect(self._on_detection_finished)
        self.detection_worker.start()

    def _update_drives(self, drives: List[DriveInfo]):
        """Ensure connected optical drive state is updated."""
        self.current_drives = drives
        if not drives:
            self.active_drive = None
        elif not self.active_drive or self.active_drive.device_path not in [d.device_path for d in drives]:
            self.active_drive = drives[0]

    def _update_drive_combo(self, drives: List[DriveInfo]):
        """Compatibility alias for tests."""
        self._update_drives(drives)

    def _on_toc_detected(
        self,
        drives: List[DriveInfo],
        toc: Optional[DiscTOC],
        basic_album: Optional[AlbumInfo],
        is_manual: bool,
    ):
        """Instant hardware detection slot (<10ms): updates drive state and shows disc layout immediately."""
        self._update_drives(drives)

        if toc and basic_album:
            if self._loaded_disc_id != toc.disc_id or self.current_album is None:
                self._loaded_disc_id = toc.disc_id
                self._populate_album(basic_album)

                # In-flight progressive metadata query state
                self.album_artist_label.setText("OPTICAL DISC DETECTED")
                self.album_artist_label.setVisible(True)
                self.album_title_label.setText("Fetching Metadata...")
                self.album_source_label.setText("◌  Querying MusicBrainz & Cover Art Archive...")
                self.album_source_label.setStyleSheet(
                    "background-color: rgba(255, 158, 59, 0.12); "
                    "border: 1px solid #FF9E3B; "
                    "border-radius: 4px; "
                    "color: #FF9E3B; "
                    "font-size: 11px; "
                    "font-weight: 700; "
                    "letter-spacing: 0.8px; "
                    "padding: 3px 8px; "
                    "margin-top: 4px;"
                )
                self.album_source_label.setVisible(True)

                self.btn_rip.setEnabled(False)
        elif not toc:
            if self._loaded_disc_id is not None or self.current_album is not None:
                self._set_empty_state()

    def _on_metadata_resolved(self, toc: Optional[DiscTOC], full_album: Optional[AlbumInfo]):
        """Progressive metadata slot: updates UI once online MusicBrainz / Cover Art Archive info is ready."""
        if self._is_ripping:
            return
        if toc and full_album and self._loaded_disc_id == toc.disc_id:
            self._populate_album(full_album)

    def _on_detection_finished(
        self,
        drives: List[DriveInfo],
        toc: Optional[DiscTOC],
        album: Optional[AlbumInfo],
        is_manual: bool,
    ):
        """Main-thread slot invoked when background disc inspection finishes."""
        self._update_drives(drives)

        # Update album representation if not already populated, if album changed, or to unlock button if still querying
        if toc:
            if album and (
                self._loaded_disc_id != toc.disc_id
                or self.current_album is None
                or self.current_album != album
                or not self.btn_rip.isEnabled()
            ):
                self._loaded_disc_id = toc.disc_id
                self._populate_album(album)
        else:
            self._set_empty_state()

    def _on_auto_scan_poll(self):
        """Periodic background poll for disc insertion/removal."""
        if self._is_ripping or (self.detection_worker and self.detection_worker.isRunning()):
            return
        self._trigger_detection(is_manual=False)

    def nativeEvent(self, event_type, message):
        """Intercept native Windows plug-and-play hardware events (WM_DEVICECHANGE) for instant USB hotplug."""
        if HAVE_QT and platform.system().lower() == "windows":
            try:
                # In PySide6 on Windows, event_type is b"windows_generic_MSG" or b"windows_dispatcher_MSG"
                if event_type in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
                    import ctypes
                    from ctypes import wintypes

                    msg = wintypes.MSG.from_address(int(message))
                    WM_DEVICECHANGE = 0x0219
                    if msg.message == WM_DEVICECHANGE:
                        # Instant USB device arrival or removal notification!
                        if not self._is_ripping and self.current_album is None:
                            self.album_title_label.setText("Checking Optical Drives...")
                            self.album_meta_label.setText("Detecting hardware changes...")
                            self.album_meta_label.setVisible(True)

                        # Debounce device change notifications (Windows fires 6-8 events in rapid succession)
                        # Waiting 750ms after the last event allows the USB bus, drive letter, and media to settle cleanly.
                        if getattr(self, "_hotplug_timer", None) is None:
                            self._hotplug_timer = QTimer(self)
                            self._hotplug_timer.setSingleShot(True)
                            self._hotplug_timer.timeout.connect(lambda: self._trigger_detection(is_manual=False))
                        self._hotplug_timer.start(750)
            except Exception:
                pass

        if hasattr(super(), "nativeEvent"):
            return super().nativeEvent(event_type, message)
        return False, 0

    def _load_disc_data(self):
        """Compatibility wrapper triggering disc data lookup."""
        self._trigger_detection(is_manual=True)

    def _set_empty_state(self):
        """Set UI to clean standby state reflecting drive and disc readiness."""
        self.current_album = None
        self._loaded_disc_id = None
        self.album_artist_label.setText("")
        self.album_artist_label.setVisible(False)
        self.album_source_label.setText("")
        self.album_source_label.setVisible(False)
        self.album_source_label.setStyleSheet("font-size: 11px; color: #646372; font-weight: 500;")

        if not self.current_drives:
            self.active_drive = None
            self.album_artist_label.setText("OPTICAL DRIVE")
            self.album_artist_label.setVisible(True)
            self.album_title_label.setText("No Optical Drive Detected")
            self.album_meta_label.setText("Connect a USB optical drive to get started")
            self.album_meta_label.setVisible(True)
            self.btn_rip.setEnabled(False)
        else:
            drive = self.active_drive or self.current_drives[0]
            self.active_drive = drive
            drive_name = drive.name
            self.album_artist_label.setText("OPTICAL DRIVE READY")
            self.album_artist_label.setVisible(True)
            self.album_title_label.setText("Insert audio CD")
            self.album_meta_label.setText(f"{drive_name} ready")
            self.album_meta_label.setVisible(True)
            self.btn_rip.setEnabled(False)

        self.artwork_card.set_album(None)
        self.backdrop.set_artwork_pixmap(None)
        self.track_table.set_tracks([])

    def _load_mock_demo_disc(self):
        """Load demo album showcase with Pink Floyd metadata on explicit request."""
        demo_album = AlbumInfo(
            title="The Dark Side of the Moon",
            artist="Pink Floyd",
            album_artist="Pink Floyd",
            year=1973,
            genre="Progressive Rock",
            total_tracks=10,
            musicbrainz_release_id="mbid-mock-demo-1973",
            tracks=[
                TrackInfo(track_number=1, title="Speak to Me", artist="Pink Floyd", duration_seconds=68.0),
                TrackInfo(track_number=2, title="Breathe (In the Air)", artist="Pink Floyd", duration_seconds=169.0),
                TrackInfo(track_number=3, title="On the Run", artist="Pink Floyd", duration_seconds=225.0),
                TrackInfo(track_number=4, title="Time", artist="Pink Floyd", duration_seconds=413.0),
                TrackInfo(track_number=5, title="The Great Gig in the Sky", artist="Pink Floyd", duration_seconds=284.0),
                TrackInfo(track_number=6, title="Money", artist="Pink Floyd", duration_seconds=382.0),
                TrackInfo(track_number=7, title="Us and Them", artist="Pink Floyd", duration_seconds=462.0),
                TrackInfo(track_number=8, title="Any Colour You Like", artist="Pink Floyd", duration_seconds=205.0),
                TrackInfo(track_number=9, title="Brain Damage", artist="Pink Floyd", duration_seconds=228.0),
                TrackInfo(track_number=10, title="Eclipse", artist="Pink Floyd", duration_seconds=123.0),
            ],
        )
        self._populate_album(demo_album)

    def _populate_album(self, album: AlbumInfo):
        """Bind album model to UI components."""
        self.current_album = album
        self.album_title_label.setText(album.title)
        self.album_artist_label.setText(album.artist.upper())
        self.album_artist_label.setVisible(True)

        total_secs = sum(t.duration_seconds or 0 for t in album.tracks)
        mins = int(total_secs // 60)
        secs = int(total_secs % 60)
        time_str = f"{mins}:{secs:02d}" if total_secs > 0 else ""
        year_str = f"{album.year}" if album.year else ""
        disc_str = f"Disc {album.disc_number} of {album.total_discs}" if album.total_discs > 1 else ""
        meta_parts = [p for p in [year_str, disc_str, f"{len(album.tracks)} Tracks", time_str, album.genre] if p]
        self.album_meta_label.setText("  •  ".join(meta_parts))
        self.album_meta_label.setVisible(len(meta_parts) > 0)

        # Metadata & artwork provenance badge
        if album.musicbrainz_release_id:
            parts = ["Metadata: MusicBrainz"]
            if album.artwork_candidates:
                parts.append("Artwork: Cover Art Archive")
            self.album_source_label.setText("  •  ".join(parts))
            self.album_source_label.setStyleSheet(
                "background-color: rgba(255, 255, 255, 0.04); "
                "border: 1px solid #282834; "
                "border-radius: 4px; "
                "color: #9CA3AF; "
                "font-size: 11px; "
                "font-weight: 500; "
                "padding: 3px 8px; "
                "margin-top: 4px;"
            )
            self.album_source_label.setVisible(True)
        else:
            self.album_source_label.setText("")
            self.album_source_label.setVisible(False)

        self.track_table.set_tracks(album.tracks)
        self.artwork_card.set_album(album)
        self.backdrop.set_artwork_pixmap(None)

        self.btn_rip.setEnabled(len(album.tracks) > 0)

    def _start_rip(self, checked: bool = False):
        """
        Initiate ripping.
        Prompts user for destination directory on click, eliminating clutter from the main view.
        """
        if not self.current_album:
            return

        # Pre-flight check: ensure audio encoder is available
        if not getattr(self.orchestrator.encoder, "is_available", False):
            from lazycdripper.core.binaries import ensure_ffmpeg
            ensure_ffmpeg()
            if not getattr(self.orchestrator.encoder, "is_available", False):
                QMessageBox.critical(
                    self,
                    "Audio Encoder Required",
                    "An audio encoder (FLAC/LAME or FFmpeg) is required to encode audio into FLAC and MP3, but could not be located.\n\n"
                    "Please ensure encoders are available or internet access is enabled for automated setup.",
                )
                return

        default_dir = self.last_destination_dir or str(Path.home() / "Music")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose Destination Folder for [FLAC] and [MP3] Archives",
            default_dir,
        )
        if not folder:
            return  # User dismissed dialog

        self.last_destination_dir = folder
        out_path = Path(folder)
        device = self.active_drive.device_path if self.active_drive else None

        self._is_ripping = True
        self.ripping_page.set_album(self.current_album)
        self.backdrop.set_artwork_pixmap(self._get_current_artwork_pixmap())
        self.main_stack.setCurrentIndex(1)  # Switch to analog ripping screen

        self.worker_thread = RipWorkerThread(
            orchestrator=self.orchestrator,
            album=self.current_album,
            output_dir=out_path,
            device=device,
            include_track_number=True,
            include_artist=False,
        )

        self.worker_thread.progress_signal.connect(self.ripping_page.update_progress)
        self.worker_thread.completed_signal.connect(self._on_rip_completed)
        self.worker_thread.error_signal.connect(self._on_rip_error)
        self.worker_thread.start()

    def _get_current_artwork_pixmap(self) -> Optional[QPixmap]:
        """Retrieve the currently loaded album artwork as a QPixmap if available."""
        if not HAVE_QT:
            return None
        if hasattr(self, "artwork_card") and self.artwork_card and self.artwork_card.current_pixmap:
            return self.artwork_card.current_pixmap
        if self.current_album and self.current_album.selected_artwork:
            art = self.current_album.selected_artwork
            path = art.local_cache_path
            if path and path.exists() and path.stat().st_size > 0:
                pix = QPixmap(str(path))
                if not pix.isNull():
                    return pix
            if art.image_id:
                thumb = Path.home() / ".cache" / "lazycdripper" / "artwork" / f"thumb_{art.image_id}.jpg"
                if thumb.exists() and thumb.stat().st_size > 0:
                    pix = QPixmap(str(thumb))
                    if not pix.isNull():
                        return pix
        return None

    def _on_rip_completed(self, report: AlbumRipReport):
        self._is_ripping = False
        self.ripping_page.show_completion(
            report=report,
            on_done=self._on_rip_done_dismiss,
        )

    def _on_rip_done_dismiss(self):
        self.backdrop.set_artwork_pixmap(None)
        self.main_stack.setCurrentIndex(0)  # Return to main deck

    def _on_rip_error(self, err_msg: str):
        self._is_ripping = False
        self.backdrop.set_artwork_pixmap(None)
        self.main_stack.setCurrentIndex(0)
        logger.error("Ripping error occurred: %s", err_msg)

    def _on_version_label_clicked(self, event=None):
        """Open the Credits dialog."""
        if not HAVE_QT:
            return
        dialog = CreditsDialog(parent=self)
        dialog.exec()
