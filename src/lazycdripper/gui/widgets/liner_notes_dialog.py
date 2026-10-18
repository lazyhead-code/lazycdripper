from __future__ import annotations

from typing import Optional

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

LINER_NOTES_TEXT = """We've gained so much with music streaming services.
We've lost so much as well.

Buying a music CD and listening to the whole album brings back the magic.

We don't have CD drives in cars and laptops anymore. But we can rip music for ourselves (all it takes is an external drive), copy it to our phone, and have the exact same experience.

This application is opinionated AF, but it rips to virtually the best options: high-quality MP3 (320 kbps CBR) and FLAC. Why MP3 instead of other lossy formats? Because MP3 is 100% patent-free worldwide, universally supported by every car, stereo, and device on Earth, and at 320 kbps CBR it is perceptually transparent. Why FLAC? Because it's a picture-perfect copy of your CD—highest possible quality. We may not really hear the difference much, but I'm glad to surrender to an illusion :)

Have fun and welcome back to the magical world of music!

Yours truly,
Lazyhead Code 💿"""


class LinerNotesDialog(QDialog if HAVE_QT else object):
    """
    Styled like a physical album insert booklet / gatefold sleeve,
    displaying Lazyhead Code's philosophy statement.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAVE_QT:
            return
        super().__init__(parent)
        self.setWindowTitle("Liner Notes — Why Lazy CD Ripper?")
        self.setMinimumSize(540, 480)
        self.resize(540, 480)
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
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        header = QLabel("🎸 The Liner Notes")
        header.setStyleSheet("font-size: 18px; font-weight: 700; color: #FF9E3B;")
        main_layout.addWidget(header)

        card = QFrame()
        card.setObjectName("cardPanel")
        card.setStyleSheet(
            "QFrame#cardPanel { background-color: #16161C; border: 1px solid #2C2C34; border-radius: 12px; padding: 20px; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        content = QLabel(LINER_NOTES_TEXT)
        content.setStyleSheet("font-size: 13px; color: #E5E7EB; line-height: 1.6;")
        content.setWordWrap(True)
        card_layout.addWidget(content)

        main_layout.addWidget(card)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_close = QPushButton("Back to Music")
        btn_close.setStyleSheet("background-color: #2E251A; color: #FF9E3B; border: 1px solid #FF9E3B; font-weight: 600; padding: 6px 18px;")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        main_layout.addLayout(btn_row)
