from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Optional
from lazycdripper.core.models import AlbumRipReport
from lazycdripper.gui.platform_windows import setup_windows_window
from lazycdripper.gui.theme import DARK_ROCK_STYLESHEET

try:
    from PySide6.QtCore import Qt, QUrl, QSize
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
        self.resize(540, 480)
        if hasattr(Qt, "WindowMaximizeButtonHint"):
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self.setStyleSheet(DARK_ROCK_STYLESHEET)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self._setup_ui()

    def sizeHint(self):
        if HAVE_QT:
            return QSize(540, 480)
        return super().sizeHint() if hasattr(super(), "sizeHint") else None

    def minimumSizeHint(self):
        if HAVE_QT:
            return QSize(540, 480)
        return super().minimumSizeHint() if hasattr(super(), "minimumSizeHint") else None

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

        # 2. Defect / Recovery Notices (Only shown if disc had read imperfections)
        has_retries = self.report.total_retries > 0
        has_errors = self.report.total_errors > 0
        incomplete_rip = (
            self.report.total_tracks > 0
            and self.report.successful_tracks_count < self.report.total_tracks
            and self.report.successful_tracks_count > 0
        )
        if not self.report.is_perfect and (has_retries or has_errors or incomplete_rip):
            notice_frame = QFrame()
            notice_frame.setObjectName("previewCard")
            if hasattr(QSizePolicy, "Expanding") and hasattr(QSizePolicy, "Fixed"):
                notice_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            notice_layout = QVBoxLayout(notice_frame)
            notice_layout.setSpacing(6)

            if incomplete_rip:
                lbl_tracks = QLabel(f"•  Tracks Extracted: {self.report.successful_tracks_count}/{self.report.total_tracks} tracks")
                lbl_tracks.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 500;")
                notice_layout.addWidget(lbl_tracks)

            if has_retries:
                lbl_retries = QLabel(f"🟡  Sector Retries: {self.report.total_retries} recovered")
                lbl_retries.setStyleSheet("color: #F59E0B; font-size: 12px; font-weight: 500;")
                notice_layout.addWidget(lbl_retries)

            if has_errors:
                lbl_errors = QLabel(f"🔴  Unrecoverable Skips: {self.report.total_errors} sector(s)")
                lbl_errors.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: 500;")
                notice_layout.addWidget(lbl_errors)

            main_layout.addWidget(notice_frame)

        # 3. Output Sister Directories
        if self.report.successful_tracks_count > 0:
            output_box = QVBoxLayout()
            output_box.setSpacing(8)

            flac_mb = self.report.flac_size_bytes / (1024 * 1024)
            aac_mb = self.report.aac_size_bytes / (1024 * 1024)

            flac_title = self.report.flac_directory.name if self.report.flac_directory else "[FLAC]"
            aac_title = self.report.aac_directory.name if self.report.aac_directory else "[AAC]"
            flac_label = QLabel(f"📁  {flac_title} - Perfect CD copy ({flac_mb:.1f} MB)")
            flac_label.setStyleSheet("color: #F3F4F6; font-size: 12px; font-weight: 600;")
            output_box.addWidget(flac_label)

            aac_label = QLabel(f"📁  {aac_title} - Compressed but still great ({aac_mb:.1f} MB)")
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
