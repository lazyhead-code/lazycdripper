from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Optional
from lazycdripper.core.models import AlbumRipReport
from lazycdripper.gui.platform_windows import setup_windows_window
from lazycdripper.gui.theme import DARK_ROCK_STYLESHEET

try:
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtGui import QColor, QDesktopServices, QPainter
    from PySide6.QtWidgets import (
        QDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLayout,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    QDialog = object
    QWidget = object
    QLayout = object
    QSizePolicy = object


class CompletionDialog(QDialog if HAVE_QT else object):
    """
    Post-rip integrity modal popup confirming bit-perfection or identifying
    problematic sectors, with direct rip folder opening button.
    """

    def __init__(self, report: AlbumRipReport, parent: Optional[QWidget] = None):
        if not HAVE_QT:
            return
        super().__init__(parent)
        self.report = report

        self.setWindowTitle("Rip Complete — Integrity Audit")
        self.setFixedWidth(540)
        if hasattr(Qt, "WindowMaximizeButtonHint"):
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self.setStyleSheet(DARK_ROCK_STYLESHEET)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self._setup_ui()

    def paintEvent(self, event):
        if not HAVE_QT:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0C0C0F"))
        super().paintEvent(event)

    def showEvent(self, event):
        if HAVE_QT:
            super().showEvent(event)
            setup_windows_window(self)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        if hasattr(QLayout, "SetFixedSize"):
            main_layout.setSizeConstraint(QLayout.SetFixedSize)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 1. Headline Badge Card
        badge_card = QFrame()
        badge_card.setObjectName("cardPanel")
        if hasattr(QSizePolicy, "Expanding") and hasattr(QSizePolicy, "Fixed"):
            badge_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if self.report.overall_status == "failed" or self.report.successful_tracks_count == 0:
            card_border = "#EF4444"
            title_color = "#EF4444"
        elif self.report.is_perfect:
            card_border = "#10B981"
            title_color = "#10B981"
        elif self.report.total_errors == 0:
            card_border = "#F59E0B"
            title_color = "#F59E0B"
        else:
            card_border = "#EF4444"
            title_color = "#EF4444"

        badge_card.setStyleSheet(
            f"QFrame#cardPanel {{ background-color: #1A1A22; border: 2px solid {card_border}; border-radius: 12px; padding: 16px; }}"
        )
        badge_layout = QVBoxLayout(badge_card)
        badge_layout.setSpacing(8)

        headline_label = QLabel(self.report.summary_headline)
        headline_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {title_color};")
        badge_layout.addWidget(headline_label)

        sub_label = QLabel(self.report.human_readable_summary)
        sub_label.setStyleSheet("font-size: 13px; color: #D1D5DB; line-height: 1.4;")
        sub_label.setWordWrap(True)
        badge_layout.addWidget(sub_label)

        main_layout.addWidget(badge_card)

        # 2. Key Metrics Table
        metrics_frame = QFrame()
        metrics_frame.setObjectName("previewCard")
        if hasattr(QSizePolicy, "Expanding") and hasattr(QSizePolicy, "Fixed"):
            metrics_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        metrics_layout = QVBoxLayout(metrics_frame)
        metrics_layout.setSpacing(6)

        tracks_str = f"Tracks Extracted: {self.report.successful_tracks_count}/{self.report.total_tracks} tracks"
        jitter_str = f"Jitter Alignments: {self.report.total_jitter}"
        retries_str = f"Sector Retries: {self.report.total_retries}"
        errors_str = f"Unrecoverable Skips: {self.report.total_errors}"
        time_str = f"Time Elapsed: {int(self.report.duration_seconds // 60)}m {int(self.report.duration_seconds % 60)}s"

        for stat_text in [tracks_str, jitter_str, retries_str, errors_str, time_str]:
            lbl = QLabel(f"•  {stat_text}")
            lbl.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 500;")
            metrics_layout.addWidget(lbl)

        main_layout.addWidget(metrics_frame)

        # 3. Output Sister Directories
        if self.report.successful_tracks_count > 0:
            output_box = QVBoxLayout()
            output_box.setSpacing(8)

            flac_mb = self.report.flac_size_bytes / (1024 * 1024)
            aac_mb = self.report.aac_size_bytes / (1024 * 1024)

            flac_label = QLabel(f"📁 [FLAC] Master Archive ({flac_mb:.1f} MB — Level 8 Verified Checksum)")
            flac_label.setStyleSheet("color: #F3F4F6; font-size: 12px; font-weight: 600;")
            output_box.addWidget(flac_label)

            aac_label = QLabel(f"📁 [AAC] Mobile Library ({aac_mb:.1f} MB — 256 kbps Bluetooth-Optimized)")
            aac_label.setStyleSheet("color: #F3F4F6; font-size: 12px; font-weight: 600;")
            output_box.addWidget(aac_label)

            main_layout.addLayout(output_box)
        else:
            err_box = QVBoxLayout()
            err_box.setSpacing(4)
            err_notice = QLabel("⚠️ Optical drive read error prevented audio extraction.")
            err_notice.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: 600;")
            err_desc = QLabel("No audio files were saved. Please inspect the disc surface for smudges or scratches.")
            err_desc.setStyleSheet("color: #9CA3AF; font-size: 12px;")
            err_box.addWidget(err_notice)
            err_box.addWidget(err_desc)
            main_layout.addLayout(err_box)

        # 4. Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        rip_folder = self.report.rip_folder
        if self.report.successful_tracks_count > 0 and rip_folder:
            btn_open_rip = QPushButton("Open Rip Folder")
            btn_open_rip.setStyleSheet("padding: 8px 18px; font-weight: 600;")
            btn_open_rip.clicked.connect(lambda: self._open_folder(rip_folder))
            btn_row.addWidget(btn_open_rip)

        btn_row.addStretch()

        btn_done = QPushButton("Done")
        btn_done.setStyleSheet("background-color: #FF9E3B; color: #121214; font-weight: 700; padding: 8px 24px;")
        btn_done.clicked.connect(self.accept)
        btn_row.addWidget(btn_done)

        main_layout.addLayout(btn_row)

    @staticmethod
    def _open_folder(folder_path: Path):
        """Open the target directory in Windows Explorer or native file viewer."""
        if not folder_path or not folder_path.exists():
            return

        try:
            subprocess.Popen(["explorer", str(folder_path)])
        except Exception:
            if HAVE_QT:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder_path)))
