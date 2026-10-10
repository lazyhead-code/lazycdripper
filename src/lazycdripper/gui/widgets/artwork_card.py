"""Album artwork presentation card with tactile jewel-case frame and analog CD platter placeholder."""

import logging
from pathlib import Path
from typing import Optional
from lazycdripper.core.models import AlbumInfo

logger = logging.getLogger(__name__)

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
    from PySide6.QtWidgets import (
        QFrame,
        QLabel,
        QVBoxLayout,
        QWidget,
    )
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    QWidget = object


class ArtworkCardWidget(QWidget if HAVE_QT else object):
    """
    Renders the selected album cover inside an elegant jewel-case frame,
    or displays a precision-machined CD platter placeholder when no artwork is available.
    Adheres strictly to the '1-Button Perfect Ripper' philosophy: fully automated, zero configuration.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAVE_QT:
            return
        super().__init__(parent)
        self._current_album: Optional[AlbumInfo] = None
        self._current_pixmap: Optional[QPixmap] = None
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(280, 280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if HAVE_QT:
            layout.setAlignment(Qt.AlignCenter)

        # Jewel-case styled frame (280x280 outer, 268x268 inner image)
        self.frame = QFrame()
        self.frame.setObjectName("artworkFrame")
        self.frame.setFixedSize(280, 280)
        self.frame.setStyleSheet(
            "QFrame#artworkFrame { "
            "  background-color: #0E0E12; "
            "  border: 1px solid #25252E; "
            "  border-radius: 12px; "
            "  padding: 0px; "
            "  margin: 0px; "
            "}"
        )

        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        if HAVE_QT:
            frame_layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setFixedSize(268, 268)
        if HAVE_QT:
            self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setStyleSheet(
            "border-radius: 8px; background-color: #121217; padding: 0px; margin: 0px; border: none;"
        )
        frame_layout.addWidget(self.image_label, alignment=Qt.AlignCenter if HAVE_QT else None)

        layout.addWidget(self.frame, alignment=Qt.AlignCenter if HAVE_QT else None)

        self._show_placeholder()

    def _prepare_cover_pixmap(self, pix: QPixmap, target_size: int = 268, radius: int = 8) -> Optional[QPixmap]:
        """Process cover artwork into a centered 1:1 square with smooth rounded corners.

        Follows the 'crop, not squeeze' principle: center-crops non-square images to 1:1,
        smoothly scales to target dimensions, and clips with an anti-aliased rounded rectangle.
        """
        if not HAVE_QT or pix is None or pix.isNull():
            return None

        w, h = pix.width(), pix.height()
        if w <= 0 or h <= 0:
            return pix

        # 1. Center-crop to 1:1 square ("crop, not squeeze")
        side = min(w, h)
        cx = (w - side) // 2
        cy = (h - side) // 2
        square_pix = pix.copy(cx, cy, side, side)

        # 2. Smooth scale to target dimensions
        scaled_square = square_pix.scaled(
            target_size,
            target_size,
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation,
        )

        # 3. Clip with anti-aliased rounded corners
        rounded_pix = QPixmap(target_size, target_size)
        rounded_pix.fill(Qt.transparent)

        painter = QPainter(rounded_pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        path = QPainterPath()
        path.addRoundedRect(0, 0, target_size, target_size, radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled_square)
        painter.end()

        return rounded_pix

    @property
    def current_pixmap(self) -> Optional[QPixmap]:
        """Return the unscaled artwork pixmap currently loaded, or None."""
        return getattr(self, "_current_pixmap", None)

    def set_album(self, album: Optional[AlbumInfo]):
        """Update the displayed artwork based on the current album model."""
        self._current_album = album
        if not album:
            self._current_pixmap = None
            self._show_placeholder()
            return

        # 1. Load full-resolution image if cached locally
        if album.selected_artwork and album.selected_artwork.local_cache_path:
            path = album.selected_artwork.local_cache_path
            if path.exists() and path.stat().st_size > 0:
                pix = QPixmap(str(path))
                if pix.isNull() and HAVE_QT:
                    try:
                        from PySide6.QtGui import QImageReader
                        reader = QImageReader(str(path))
                        reader.setAutoDetectImageFormat(True)
                        qimg = reader.read()
                        if not qimg.isNull():
                            pix = QPixmap.fromImage(qimg)
                    except Exception:
                        pass
                if not pix.isNull():
                    self._current_pixmap = pix
                    display_pix = self._prepare_cover_pixmap(pix, 268, 8)
                    self.image_label.setPixmap(display_pix)
                    return

        # 2. Fast preview with thumbnail cache if full image is still downloading
        if album.selected_artwork and album.selected_artwork.image_id:
            thumb_path = Path.home() / ".cache" / "lazycdripper" / "artwork" / f"thumb_{album.selected_artwork.image_id}.jpg"
            if thumb_path.exists() and thumb_path.stat().st_size > 0:
                pix = QPixmap(str(thumb_path))
                if not pix.isNull():
                    self._current_pixmap = pix
                    display_pix = self._prepare_cover_pixmap(pix, 268, 8)
                    self.image_label.setPixmap(display_pix)
                    return

        self._current_pixmap = None
        self._show_placeholder()

    def _draw_machined_platter(self, width: int = 268, height: int = 268) -> QPixmap:
        """Render a machined anodized aluminum CD platter with concentric grooves and center LED.

        Rendered at high-resolution supersampling (at least 2x or screen devicePixelRatio)
        with anti-aliased text and geometry, preventing subpixel chromatic blur on high-DPI displays.
        """
        dpr = float(self.devicePixelRatioF()) if hasattr(self, "devicePixelRatioF") else 1.0
        if dpr <= 0:
            dpr = 1.0
        # Supersample at 2x minimum (or screen DPR if higher) for razor-sharp text & geometry
        scale = max(2.0, dpr)
        target_w = int(round(width * scale))
        target_h = int(round(height * scale))

        pixmap = QPixmap(target_w, target_h)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Scale coordinate space to logical dimensions
        painter.scale(scale, scale)

        # Clip to rounded rectangle (radius: 8px) matching the jewel-case window
        clip_path = QPainterPath()
        clip_path.addRoundedRect(0, 0, width, height, 8, 8)
        painter.setClipPath(clip_path)

        # Platter base background
        painter.fillPath(clip_path, QColor("#0E0E12"))

        cx = width / 2.0
        cy = height / 2.0

        # Outer milled platter rim
        painter.setPen(QPen(QColor("#25252E"), 2))
        painter.setBrush(QBrush(QColor("#131318")))
        painter.drawEllipse(12, 12, width - 24, height - 24)

        # Concentric spiral laser groove tracks
        # Outer data track band: spaced cleanly so no lines collide with or bisect the lower text branding zone
        for r in [114, 102, 90, 78]:
            painter.setPen(QPen(QColor(255, 255, 255, 12), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(int(cx - r), int(cy - r), r * 2, r * 2)

        # Inner mirror clamping ring
        painter.setPen(QPen(QColor("#343340"), 1))
        painter.setBrush(QBrush(QColor("#191922")))
        painter.drawEllipse(int(cx - 38), int(cy - 38), 76, 76)

        # Spindle center hub
        painter.setPen(QPen(QColor("#FF9E3B"), 2))
        painter.setBrush(QBrush(QColor("#0A0A0D")))
        painter.drawEllipse(int(cx - 16), int(cy - 16), 32, 32)

        # Amber glowing center indicator diode
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#FF9E3B")))
        painter.drawEllipse(int(cx - 4), int(cy - 4), 8, 8)

        # Platter engraved branding: COMPACT DISC DIGITAL AUDIO
        font = painter.font()
        font.setStyleHint(QFont.SansSerif)
        font.setPixelSize(10)
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        painter.setFont(font)
        painter.setPen(QColor("#C5C4D4"))
        painter.drawText(0, int(cy + 42), width, 16, Qt.AlignCenter, "COMPACT DISC DIGITAL AUDIO")

        # Platter engraved spec: RED BOOK • 44.1 kHz / 16-BIT PCM
        font.setPixelSize(9)
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.6)
        painter.setFont(font)
        painter.setPen(QColor("#9CA3AF"))
        painter.drawText(0, int(cy + 60), width, 16, Qt.AlignCenter, "RED BOOK • 44.1 kHz / 16-BIT PCM")

        painter.end()
        pixmap.setDevicePixelRatio(scale)
        return pixmap

    def _show_placeholder(self):
        """Display an analog CD disc placeholder when no cover art is available."""
        if hasattr(self, "image_label") and HAVE_QT:
            try:
                pix = self._draw_machined_platter(268, 268)
                self.image_label.setPixmap(pix)
            except Exception:
                self.image_label.setText("NO DISC LOADED")
                self.image_label.setStyleSheet(
                    "color: #555460; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; text-align: center; background-color: #121217; border-radius: 8px;"
                )
