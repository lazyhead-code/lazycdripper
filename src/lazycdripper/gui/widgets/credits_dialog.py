from __future__ import annotations

from typing import Optional

from lazycdripper import __codename__, __version__
from lazycdripper.gui.platform_windows import setup_windows_window
from lazycdripper.gui.theme import DARK_ROCK_STYLESHEET

try:
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QColor, QPainter
    from PySide6.QtWidgets import (
        QDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    QDialog = object
    QWidget = object


class CreditsDialog(QDialog if HAVE_QT else object):
    """
    Hi-Fi Engineering Specifications & Open-Source Credits Plaque.
    Displays third-party engines, Antigravity pair-programming credits,
    and GNU GPLv3 license information.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAVE_QT:
            return
        super().__init__(parent)
        self.setWindowTitle("Credits — Lazy CD Ripper")
        self.setMinimumSize(560, 520)
        self.resize(560, 520)
        self.setStyleSheet(DARK_ROCK_STYLESHEET)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self._setup_ui()

    def sizeHint(self):
        if HAVE_QT:
            return QSize(560, 520)
        return super().sizeHint() if hasattr(super(), "sizeHint") else None

    def minimumSizeHint(self):
        if HAVE_QT:
            return QSize(560, 520)
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
        main_layout.setContentsMargins(24, 22, 24, 22)
        main_layout.setSpacing(14)

        # 1. Header Plaque
        header_container = QVBoxLayout()
        header_container.setSpacing(4)

        title = QLabel(f"LAZY CD RIPPER v{__version__}")
        title.setStyleSheet("font-size: 17px; font-weight: 800; color: #FF9E3B; letter-spacing: 1.5px;")
        header_container.addWidget(title)

        codename = QLabel(
            f"<span style='color: #8E8D96; font-size: 10px; font-weight: 600; letter-spacing: 1px;'>RELEASE CODENAME:</span> "
            f"<b style='color: #E5E7EB; font-size: 10px; letter-spacing: 0.5px;'>\"{__codename__}\"</b>"
        )
        codename.setTextFormat(Qt.RichText)
        header_container.addWidget(codename)

        subtitle = QLabel("AN ALBUM IS AN EXPERIENCE, NOT A STREAM")
        subtitle.setStyleSheet("font-size: 9px; font-weight: 600; color: #727180; letter-spacing: 1.2px;")
        header_container.addWidget(subtitle)

        main_layout.addLayout(header_container)

        # 2. Main Specification Card
        card = QFrame()
        card.setObjectName("cardPanel")
        card.setStyleSheet(
            "QFrame#cardPanel { background-color: #14141A; border: 1px solid #24242E; border-radius: 12px; padding: 18px; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)

        # Section: Open-Source Core Engines
        sec1_title = QLabel("OPEN-SOURCE CORE ENGINES")
        sec1_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #FF9E3B; letter-spacing: 1px;")
        card_layout.addWidget(sec1_title)

        engines_html = (
            "<table width='100%' cellpadding='3' cellspacing='0' style='color: #D1D5DB; font-size: 11px;'>"
            "<tr>"
            "<td width='14' valign='top' style='color: #FF9E3B; font-size: 9px;'>●</td>"
            "<td><b>FFmpeg</b> — Parallel FLAC & AAC transcoding engine</td>"
            "<td align='right' style='color: #727180; font-size: 10px;'>GPLv3</td>"
            "</tr>"
            "<tr>"
            "<td width='14' valign='top' style='color: #FF9E3B; font-size: 9px;'>●</td>"
            "<td><b>Mutagen</b> — Audio metadata tagger & cover art embedder</td>"
            "<td align='right' style='color: #727180; font-size: 10px;'>GPLv2+</td>"
            "</tr>"
            "<tr>"
            "<td width='14' valign='top' style='color: #FF9E3B; font-size: 9px;'>●</td>"
            "<td><b>Qt 6 / PySide6</b> — Hi-DPI hardware GUI framework</td>"
            "<td align='right' style='color: #727180; font-size: 10px;'>LGPLv3</td>"
            "</tr>"
            "<tr>"
            "<td width='14' valign='top' style='color: #FF9E3B; font-size: 9px;'>●</td>"
            "<td><b>MusicBrainz WS2</b> — Global acoustic CD discovery client</td>"
            "<td align='right' style='color: #727180; font-size: 10px;'>BSD-2</td>"
            "</tr>"
            "<tr>"
            "<td width='14' valign='top' style='color: #FF9E3B; font-size: 9px;'>●</td>"
            "<td><b>Pillow</b> — High-resolution cover art processing</td>"
            "<td align='right' style='color: #727180; font-size: 10px;'>HPND</td>"
            "</tr>"
            "</table>"
        )
        engines_label = QLabel(engines_html)
        engines_label.setTextFormat(Qt.RichText)
        card_layout.addWidget(engines_label)

        # Divider
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.HLine)
        divider1.setStyleSheet("background-color: #22222A; max-height: 1px;")
        card_layout.addWidget(divider1)

        # Section: Pair Programming & Craftsmanship
        sec2_title = QLabel("DEVELOPED IN PAIR PROGRAMMING WITH")
        sec2_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #FF9E3B; letter-spacing: 1px;")
        card_layout.addWidget(sec2_title)

        antigravity_html = (
            "<table width='100%' cellpadding='3' cellspacing='0' style='color: #D1D5DB; font-size: 11px;'>"
            "<tr>"
            "<td width='14' valign='top' style='color: #FF9E3B; font-size: 9px;'>●</td>"
            "<td><b>Antigravity</b> — Google DeepMind advanced agentic coding assistant</td>"
            "<td align='right' style='color: #8E8D96; font-size: 10px;'>Google DeepMind</td>"
            "</tr>"
            "</table>"
        )
        antigravity_label = QLabel(antigravity_html)
        antigravity_label.setTextFormat(Qt.RichText)
        card_layout.addWidget(antigravity_label)

        # Divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet("background-color: #22222A; max-height: 1px;")
        card_layout.addWidget(divider2)

        # Section: License & Source
        license_html = (
            "<div style='color: #8E8D96; font-size: 10px; line-height: 1.5;'>"
            "<b style='color: #E5E7EB;'>License:</b> GNU General Public License v3.0 (GPLv3)<br>"
            "<b style='color: #E5E7EB;'>Copyright:</b> © 2026 Lazyhead Code &lt;lazyhead@fastmail.com&gt;<br>"
            "<b style='color: #E5E7EB;'>Repository:</b> <span style='color: #FF9E3B;'>github.com/lazyhead-code/lazycdripper</span>"
            "</div>"
        )
        license_label = QLabel(license_html)
        license_label.setTextFormat(Qt.RichText)
        card_layout.addWidget(license_label)

        main_layout.addWidget(card)

        # 3. Bottom Button Row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(
            "background-color: #2E251A; color: #FF9E3B; border: 1px solid #FF9E3B; "
            "font-weight: 600; padding: 7px 22px; border-radius: 6px;"
        )
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        main_layout.addLayout(btn_row)

