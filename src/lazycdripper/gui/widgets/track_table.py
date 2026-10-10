"""Tracklist table widget displaying album tracks, positions, and durations."""

from typing import List, Optional
from lazycdripper.core.models import TrackInfo

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QHeaderView,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    QWidget = object


class TrackTableWidget(QWidget if HAVE_QT else object):
    """Displays the tracklist with numbers, titles, artists, and durations."""

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAVE_QT:
            return
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "Title", "Artist", "Time"])

        # Configure headers
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionsClickable(False)
        header.setHighlightSections(False)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        if HAVE_QT:
            self.table.viewport().setAutoFillBackground(False)
            header.setAutoFillBackground(False)

        layout.addWidget(self.table)

    def set_tracks(self, tracks: List[TrackInfo]):
        """Populate the table with track records."""
        self.table.setRowCount(len(tracks))
        for row, track in enumerate(tracks):
            item_num = QTableWidgetItem(f"{track.track_number:02d}")
            item_num.setTextAlignment(Qt.AlignCenter)

            item_title = QTableWidgetItem(track.title)

            item_artist = QTableWidgetItem(track.artist)

            dur_str = self._format_duration(track.duration_seconds)
            item_dur = QTableWidgetItem(dur_str)
            item_dur.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            for item in (item_num, item_title, item_artist, item_dur):
                item.setFlags(Qt.ItemIsEnabled)

            self.table.setItem(row, 0, item_num)
            self.table.setItem(row, 1, item_title)
            self.table.setItem(row, 2, item_artist)
            self.table.setItem(row, 3, item_dur)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format seconds into MM:SS string."""
        if seconds <= 0:
            return "--:--"
        total_sec = int(round(seconds))
        minutes = total_sec // 60
        sec = total_sec % 60
        return f"{minutes:02d}:{sec:02d}"
