"""Ripping view screen featuring the nostalgic vinyl/CD visual and rotating memories ticker."""

import html
import math
from pathlib import Path
import random
import subprocess
import sys
from typing import Callable, Optional
from lazycdripper.core.models import AlbumInfo, AlbumRipReport, RipProgress

try:
    from PySide6.QtCore import QPointF, QSize, Qt, QTimer, QUrl
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QConicalGradient,
        QDesktopServices,
        QPainter,
        QPainterPath,
        QPen,
        QPixmap,
        QRadialGradient,
    )
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    QWidget = object
    QSizePolicy = object
    QPushButton = object


class HiFiOpticalTransportWidget(QWidget if HAVE_QT else object):
    """
    Precision animated boutique hi-fi optical disc transport visualizer.
    Features:
    - Real-time spinning polycarbonate disc with concentric micro-grooves
    - Rotating iridescent diffraction rainbow reflection (conical gradient)
    - Active optical laser pickup sled tracking from inner spiral outward in real-time
    - Pulsing ruby/amber laser diode pinpoint with incandescent photon glow
    - Machined knurled brass center spindle clamp
    - Stroboscopic tachometer rim dots
    - Warm vacuum-tube amber backlight halo
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAVE_QT:
            return
        super().__init__(parent)
        self.setFixedSize(160, 160)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._angle: float = 0.0
        self._laser_phase: float = 0.0
        self._track_progress: float = 0.0  # 0.0 (inner) to 1.0 (outer lead-in)

        # 33 FPS smooth animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(30)

    def showEvent(self, event):
        if HAVE_QT and hasattr(self, "_timer") and not self._timer.isActive():
            self._timer.start(30)
        super().showEvent(event)

    def hideEvent(self, event):
        if HAVE_QT and hasattr(self, "_timer") and self._timer.isActive():
            self._timer.stop()
        super().hideEvent(event)

    def stop_animation(self):
        """Stop rotation and laser pulse animation."""
        if HAVE_QT and hasattr(self, "_timer") and self._timer.isActive():
            self._timer.stop()
            self.update()

    def start_animation(self):
        """Resume rotation and laser pulse animation."""
        if HAVE_QT and hasattr(self, "_timer") and not self._timer.isActive():
            self._timer.start(30)
            self.update()

    def set_track_progress(self, progress: float):
        """Update laser sled radial position (0.0 to 1.0)."""
        self._track_progress = max(0.0, min(1.0, float(progress)))

    def _on_tick(self):
        self._angle = (self._angle + 2.4) % 360.0
        self._laser_phase = (self._laser_phase + 0.12) % (2.0 * math.pi)
        self.update()

    def paintEvent(self, event):
        if not HAVE_QT:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        cx = w / 2.0
        cy = h / 2.0

        r_outer = 68.0
        r_lead_in = 64.0
        r_data_inner = 23.0
        r_hub = 18.0
        r_hole = 8.0

        # 1. Warm vacuum-tube amber backlight halo
        tube_pulse = 0.7 + 0.3 * math.sin(self._laser_phase * 0.5)
        glow_alpha = int(45 * tube_pulse)
        radial_glow = QRadialGradient(cx, cy, r_outer + 12.0)
        radial_glow.setColorAt(0.0, QColor(255, 158, 59, glow_alpha + 35))
        radial_glow.setColorAt(0.6, QColor(255, 158, 59, glow_alpha))
        radial_glow.setColorAt(1.0, QColor(255, 158, 59, 0))
        painter.fillRect(self.rect(), radial_glow)

        # 2. Recessed optical well bevel / shadow
        painter.setPen(QPen(QColor(37, 37, 46, 180), 2.0))
        painter.setBrush(QBrush(QColor(10, 10, 14, 220)))
        painter.drawEllipse(QPointF(cx, cy), r_outer + 3.0, r_outer + 3.0)

        # 3. Polycarbonate disc base body
        disc_grad = QRadialGradient(cx, cy, r_outer)
        disc_grad.setColorAt(0.0, QColor(43, 45, 52))
        disc_grad.setColorAt(0.85, QColor(61, 65, 77))
        disc_grad.setColorAt(0.96, QColor(90, 95, 110))
        disc_grad.setColorAt(1.0, QColor(30, 32, 38))
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1.0))
        painter.setBrush(QBrush(disc_grad))
        painter.drawEllipse(QPointF(cx, cy), r_outer, r_outer)

        # 4. Rotating iridescent diffraction rainbow reflection (CD signature sheen)
        data_path = QPainterPath()
        data_path.addEllipse(QPointF(cx, cy), r_lead_in, r_lead_in)
        inner_path = QPainterPath()
        inner_path.addEllipse(QPointF(cx, cy), r_data_inner, r_data_inner)
        data_annulus = data_path.subtracted(inner_path)

        conic = QConicalGradient(cx, cy, self._angle)
        conic.setColorAt(0.00, QColor(255, 255, 255, 0))
        conic.setColorAt(0.08, QColor(255, 100, 120, 65))
        conic.setColorAt(0.12, QColor(255, 180, 50, 85))
        conic.setColorAt(0.16, QColor(120, 240, 120, 75))
        conic.setColorAt(0.20, QColor(60, 200, 255, 90))
        conic.setColorAt(0.24, QColor(180, 100, 255, 70))
        conic.setColorAt(0.32, QColor(255, 255, 255, 0))
        conic.setColorAt(0.58, QColor(255, 100, 120, 65))
        conic.setColorAt(0.62, QColor(255, 180, 50, 85))
        conic.setColorAt(0.66, QColor(120, 240, 120, 75))
        conic.setColorAt(0.70, QColor(60, 200, 255, 90))
        conic.setColorAt(0.74, QColor(180, 100, 255, 70))
        conic.setColorAt(0.82, QColor(255, 255, 255, 0))
        conic.setColorAt(1.00, QColor(255, 255, 255, 0))

        painter.save()
        painter.setClipPath(data_annulus)
        painter.setBrush(QBrush(conic))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), r_lead_in, r_lead_in)

        # Concentric track micro-grooves
        painter.setPen(QPen(QColor(255, 255, 255, 10), 1.0))
        for r_groove in (31.0, 39.0, 47.0, 55.0):
            painter.drawEllipse(QPointF(cx, cy), r_groove, r_groove)
        painter.restore()

        # 5. Stroboscopic tachometer dots on disc rim
        num_dots = 32
        for i in range(num_dots):
            dot_rad = math.radians(self._angle + (i * 360.0 / num_dots))
            dx = cx + math.cos(dot_rad) * (r_outer - 2.5)
            dy = cy + math.sin(dot_rad) * (r_outer - 2.5)
            dot_color = QColor(255, 255, 255, 75) if (i % 2 == 0) else QColor(255, 158, 59, 65)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(QPointF(dx, dy), 1.1, 1.1)

        # 6. Clear mirror lead-in ring
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1.0))
        painter.setBrush(QBrush(QColor(200, 205, 220, 30)))
        painter.drawEllipse(QPointF(cx, cy), r_data_inner, r_data_inner)

        # 7. Center spindle hub & machined brass clamp
        hub_grad = QRadialGradient(cx - 2.0, cy - 2.0, r_hub)
        hub_grad.setColorAt(0.0, QColor("#E6D3A3"))
        hub_grad.setColorAt(0.35, QColor("#C49A45"))
        hub_grad.setColorAt(0.8, QColor("#5A4418"))
        hub_grad.setColorAt(1.0, QColor("#241B0A"))
        painter.setBrush(QBrush(hub_grad))
        painter.setPen(QPen(QColor(255, 215, 120, 140), 1.2))
        painter.drawEllipse(QPointF(cx, cy), r_hub, r_hub)

        # 8 machined radial knurling marks on clamp
        painter.setPen(QPen(QColor(255, 255, 255, 55), 1.0))
        for i in range(8):
            k_rad = math.radians(self._angle + (i * 45.0))
            p1 = QPointF(cx + math.cos(k_rad) * (r_hole + 2.0), cy + math.sin(k_rad) * (r_hole + 2.0))
            p2 = QPointF(cx + math.cos(k_rad) * (r_hub - 2.0), cy + math.sin(k_rad) * (r_hub - 2.0))
            painter.drawLine(p1, p2)

        # Spindle center hole
        painter.setBrush(QBrush(QColor("#0A0A0D")))
        painter.setPen(QPen(QColor(255, 255, 255, 45), 1.5))
        painter.drawEllipse(QPointF(cx, cy), r_hole, r_hole)

        # 8. Active optical laser pickup sled
        # Tracks outward from r_data_inner + 2 to r_lead_in - 2 based on track progress
        laser_rad_pos = r_data_inner + 2.0 + (r_lead_in - r_data_inner - 4.0) * self._track_progress
        laser_angle = math.radians(135.0)  # ~8 o'clock position
        lx = cx + math.cos(laser_angle) * laser_rad_pos
        ly = cy + math.sin(laser_angle) * laser_rad_pos

        # Sled guide rail
        p_rail_start = QPointF(cx + math.cos(laser_angle) * (r_data_inner - 2.0), cy + math.sin(laser_angle) * (r_data_inner - 2.0))
        p_rail_end = QPointF(cx + math.cos(laser_angle) * (r_lead_in + 4.0), cy + math.sin(laser_angle) * (r_lead_in + 4.0))
        painter.setPen(QPen(QColor(255, 255, 255, 25), 1.5))
        painter.drawLine(p_rail_start, p_rail_end)

        # Laser lens aperture housing
        painter.setBrush(QBrush(QColor("#1E1E26")))
        painter.setPen(QPen(QColor("#424254"), 1.2))
        painter.drawEllipse(QPointF(lx, ly), 3.2, 3.2)

        # Glowing pulsing laser diode pinpoint
        pulse = 0.6 + 0.4 * math.sin(self._laser_phase)
        laser_glow = QRadialGradient(lx, ly, 6.5)
        laser_glow.setColorAt(0.0, QColor(255, 245, 210, int(255 * pulse)))
        laser_glow.setColorAt(0.3, QColor(255, 80, 50, int(220 * pulse)))
        laser_glow.setColorAt(0.7, QColor(255, 158, 59, int(110 * pulse)))
        laser_glow.setColorAt(1.0, QColor(255, 158, 59, 0))
        painter.setBrush(QBrush(laser_glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(lx, ly), 6.5, 6.5)

        # Intense photon core
        painter.setBrush(QBrush(QColor(255, 255, 255, 250)))
        painter.drawEllipse(QPointF(lx, ly), 1.0, 1.0)


def make_status_led(color: str, size: int = 15) -> Optional["QPixmap"]:
    """Generate a high-fidelity glowing circular hardware LED indicator."""
    if not HAVE_QT:
        return None
    dpr = 2.0
    pad = int(1.5 * dpr)
    halo_d = int(size * dpr)
    s = halo_d + 2 * pad
    pix = QPixmap(s, s)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)

    c = QColor(color)
    # 1. Soft atmospheric illuminated halo
    halo_color = QColor(c.red(), c.green(), c.blue(), 55)
    painter.setBrush(QBrush(halo_color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(pad, pad, halo_d, halo_d)

    # 2. Precision circular bezel & solid illuminated core
    bezel_inset = pad + int(1.5 * dpr)
    core_size = halo_d - 2 * int(1.5 * dpr)
    painter.setPen(QPen(QColor(30, 30, 38, 200), 1.0 * dpr))
    painter.setBrush(QBrush(c))
    painter.drawEllipse(bezel_inset, bezel_inset, core_size, core_size)

    # 3. Glossy convex glass highlight
    hl_color = QColor(255, 255, 255, 185)
    painter.setBrush(QBrush(hl_color))
    painter.setPen(Qt.NoPen)
    hl_w = int(core_size * 0.45)
    hl_h = int(core_size * 0.28)
    painter.drawEllipse(bezel_inset + int(1.5 * dpr), bezel_inset + int(1.0 * dpr), hl_w, hl_h)

    painter.end()
    pix.setDevicePixelRatio(dpr)
    return pix


def locate_sloth_complete_pixmap(size: int = 200, dpr: float = 2.0, sad: bool = False) -> Optional["QPixmap"]:
    """Locate and prepare the metallic rock sloth mascot completion emblem at high DPI."""
    if not HAVE_QT:
        return None

    assets_dirs = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            assets_dirs.append(Path(meipass) / "assets" / "images")
        assets_dirs.append(Path(sys.executable).parent / "assets" / "images")

    cur = Path(__file__).resolve().parent
    for _ in range(7):
        candidate = cur / "assets" / "images"
        if candidate.is_dir():
            assets_dirs.append(candidate)
        cur = cur.parent

    assets_dirs.append(Path.cwd() / "assets" / "images")

    # If sad (surface damage/failure), search for sloth_sad first, falling back to sloth_complete
    names_to_try = ["sloth_sad", "sloth_complete"] if sad else ["sloth_complete"]

    for name in names_to_try:
        for adir in assets_dirs:
            for ext in [".jpg", ".png", ".jpeg"]:
                p = adir / f"{name}{ext}"
                if p.is_file():
                    pix = QPixmap(str(p))
                    if not pix.isNull():
                        render_size = int(size * dpr)
                        target = QPixmap(render_size, render_size)
                        target.fill(Qt.transparent)
                        painter = QPainter(target)
                        painter.setRenderHint(QPainter.Antialiasing)
                        painter.setRenderHint(QPainter.SmoothPixmapTransform)

                        scaled = pix.scaled(
                            render_size,
                            render_size,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation,
                        )

                        # The circular medallion bezel extends to ~96% of the source image.
                        # Align the circular clip and outer rim halo along the outer knurled metal rim and bolts
                        # to cleanly mask the 4 square corners without cropping any part of the medallion.
                        bezel_d = int(round(render_size * 0.96))
                        if (render_size - bezel_d) % 2 != 0:
                            bezel_d -= 1
                        offset = (render_size - bezel_d) // 2

                        # Circular clip strictly for the 4 square corners outside the circular bezel
                        path = QPainterPath()
                        path.addEllipse(offset, offset, bezel_d, bezel_d)
                        painter.setClipPath(path)
                        painter.drawPixmap(0, 0, scaled)
                        painter.setClipping(False)

                        # Outer ambient chassis rim halo hugging the knurled bezel
                        rim_color = QColor(239, 68, 68, 110) if sad else QColor(255, 158, 59, 95)
                        painter.setPen(QPen(rim_color, 1.5 * dpr))
                        painter.drawEllipse(offset, offset, bezel_d, bezel_d)
                        painter.end()
                        target.setDevicePixelRatio(dpr)
                        return target
    return None


from lazycdripper.gui.memories import NOSTALGIC_MEMORIES


class RippingViewWidget(QWidget if HAVE_QT else object):
    """
    Renders the active ripping screen with real-time sector telemetry,
    dual progress bars, animated optical transport disc visualizer,
    and the nostalgic 'Liner Notes Memories' ticker.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAVE_QT:
            return
        super().__init__(parent)
        self._current_album: Optional[AlbumInfo] = None
        self._shuffled_memories = list(NOSTALGIC_MEMORIES)
        random.shuffle(self._shuffled_memories)
        self._memory_index = 0
        self._on_done_callback: Optional[Callable[[], None]] = None
        self._current_rip_folder: Optional[Path] = None
        self._setup_ui()
        self._start_memory_ticker()

    def sizeHint(self):
        if HAVE_QT:
            return QSize(1020, 700)
        return super().sizeHint() if hasattr(super(), "sizeHint") else None

    def minimumSizeHint(self):
        if HAVE_QT:
            return QSize(1020, 700)
        return super().minimumSizeHint() if hasattr(super(), "minimumSizeHint") else None

    def set_album(self, album: Optional[AlbumInfo]):
        """Set the active album model to retrieve track titles and metadata."""
        self._current_album = album
        self.reset_view()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 24, 30, 24)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignCenter)

        # Central Visual Emblem / Animated Optical Transport Banner
        self.visual_frame = QFrame()
        self.visual_frame.setObjectName("rippingBanner")
        self.visual_frame.setMinimumWidth(860)
        self.visual_frame.setMaximumWidth(960)
        if HAVE_QT:
            self.visual_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.visual_frame.setStyleSheet(
            "QFrame#rippingBanner { "
            "  background-color: #14141A; "
            "  border: 1px solid #2C2C36; "
            "  border-radius: 12px; "
            "  padding: 24px; "
            "}"
        )
        visual_layout = QVBoxLayout(self.visual_frame)
        visual_layout.setAlignment(Qt.AlignCenter)
        visual_layout.setContentsMargins(24, 24, 24, 24)
        visual_layout.setSpacing(0)

        # Hardware engraved top badge
        self.spec_badge = QLabel("AUDIO CD • 16-BIT / 44.1 kHz")
        self.spec_badge.setStyleSheet(
            "background: rgba(255, 158, 59, 0.08); border: 1px solid rgba(255, 158, 59, 0.25); "
            "color: #DDA15E; font-size: 10px; font-weight: 700; letter-spacing: 1.2px; "
            "padding: 3px 12px; border-radius: 10px;"
        )
        self.spec_badge.setAlignment(Qt.AlignCenter)
        visual_layout.addWidget(self.spec_badge, alignment=Qt.AlignCenter)

        # Symmetrical spacing between spec badge and visual emblem
        if HAVE_QT:
            visual_layout.addSpacing(8)

        # Central visual emblem container (active spinning disc or completion sloth mascot)
        self.emblem_container = QWidget()
        self.emblem_container.setStyleSheet("background: transparent;")
        emblem_layout = QVBoxLayout(self.emblem_container)
        emblem_layout.setContentsMargins(0, 0, 0, 0)
        emblem_layout.setSpacing(0)
        emblem_layout.setAlignment(Qt.AlignCenter)

        # Custom animated optical transport disc
        self.transport_widget = HiFiOpticalTransportWidget()
        emblem_layout.addWidget(self.transport_widget, alignment=Qt.AlignCenter)

        # Tactile metallic rock sloth mascot shown on completion
        self.sloth_emblem = QLabel()
        self.sloth_emblem.setFixedSize(200, 200)
        self.sloth_emblem.setAlignment(Qt.AlignCenter)
        self.sloth_emblem.setStyleSheet("background: transparent;")
        self.sloth_emblem.setVisible(False)
        emblem_layout.addWidget(self.sloth_emblem, alignment=Qt.AlignCenter)

        visual_layout.addWidget(self.emblem_container, alignment=Qt.AlignCenter)

        # Symmetrical spacing between visual emblem and headline status row (identical to top spacing)
        if HAVE_QT:
            visual_layout.addSpacing(8)

        headline_row = QHBoxLayout()
        headline_row.setSpacing(8)
        headline_row.setContentsMargins(0, 0, 0, 0)
        headline_row.setAlignment(Qt.AlignCenter)

        self.status_led = QLabel()
        self.status_led.setFixedSize(18, 18)
        self.status_led.setStyleSheet("background: transparent;")
        self.status_led.setAlignment(Qt.AlignCenter)
        self.status_led.setVisible(False)
        headline_row.addWidget(self.status_led, alignment=Qt.AlignCenter)

        self.headline = QLabel("Extracting Audio Tracks...")
        self.headline.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #FF9E3B; padding: 2px 4px; min-height: 24px;"
        )
        self.headline.setAlignment(Qt.AlignCenter)
        self.headline.setWordWrap(False)
        headline_row.addWidget(self.headline, alignment=Qt.AlignCenter)

        visual_layout.addLayout(headline_row)

        if HAVE_QT:
            visual_layout.addSpacing(10)

        self.status_sub = QLabel("Reading disc...")
        self.status_sub.setStyleSheet("font-size: 12px; color: #9CA3AF; margin-top: 2px;")
        self.status_sub.setAlignment(Qt.AlignCenter)
        self.status_sub.setWordWrap(False)
        visual_layout.addWidget(self.status_sub, alignment=Qt.AlignCenter)

        main_layout.addWidget(self.visual_frame, alignment=Qt.AlignCenter)

        # Active Progress Container (visible during active ripping)
        self.active_container = QWidget()
        self.active_container.setMinimumWidth(860)
        self.active_container.setMaximumWidth(960)
        if HAVE_QT:
            self.active_container.setFixedHeight(246)
            self.active_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        active_box = QVBoxLayout(self.active_container)
        active_box.setContentsMargins(0, 0, 0, 0)
        active_box.setSpacing(0)
        active_box.setAlignment(Qt.AlignCenter)

        # 1. Current Track & Album Progress (Fixed spacing so distance never stretches on resize)
        progress_box = QVBoxLayout()
        progress_box.setContentsMargins(0, 0, 0, 0)
        progress_box.setSpacing(0)

        self.track_label = QLabel("Extracting")
        self.track_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #F3F4F6;")
        self.track_label.setAlignment(Qt.AlignCenter)
        if HAVE_QT:
            self.track_label.setFixedHeight(18)
        progress_box.addWidget(self.track_label)

        if HAVE_QT:
            progress_box.addSpacing(8)

        self.track_bar = QProgressBar()
        self.track_bar.setRange(0, 100)
        self.track_bar.setValue(0)
        if HAVE_QT:
            self.track_bar.setFixedHeight(20)
        progress_box.addWidget(self.track_bar)

        if HAVE_QT:
            progress_box.addSpacing(22)

        self.overall_label = QLabel("Overall Album Progress")
        self.overall_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #F3F4F6;")
        self.overall_label.setAlignment(Qt.AlignCenter)
        if HAVE_QT:
            self.overall_label.setFixedHeight(18)
        progress_box.addWidget(self.overall_label)

        if HAVE_QT:
            progress_box.addSpacing(8)

        self.overall_bar = QProgressBar()
        self.overall_bar.setRange(0, 100)
        self.overall_bar.setValue(0)
        if HAVE_QT:
            self.overall_bar.setFixedHeight(20)
        progress_box.addWidget(self.overall_bar)

        active_box.addLayout(progress_box)

        if HAVE_QT:
            active_box.addSpacing(18)

        # 2. Telemetry Status Pills
        telemetry_row = QHBoxLayout()
        telemetry_row.setSpacing(16)
        telemetry_row.setAlignment(Qt.AlignCenter)

        self.badge_retries = QLabel("🟢 Retries: 0")
        self.badge_retries.setStyleSheet("background: #1A1A22; color: #10B981; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        if HAVE_QT:
            self.badge_retries.setFixedHeight(24)
        telemetry_row.addWidget(self.badge_retries)

        self.badge_errors = QLabel("🟢 Errors: 0")
        self.badge_errors.setStyleSheet("background: #1A1A22; color: #10B981; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        if HAVE_QT:
            self.badge_errors.setFixedHeight(24)
        telemetry_row.addWidget(self.badge_errors)

        active_box.addLayout(telemetry_row)

        if HAVE_QT:
            active_box.addSpacing(18)

        # 3. Nostalgic Memories Ticker Card
        self.memory_card = QFrame()
        self.memory_card.setObjectName("previewCard")
        self.memory_card.setFixedHeight(72)
        self.memory_card.setStyleSheet("QFrame#previewCard { background-color: #16161C; border: 1px solid #2C2C34; border-radius: 8px; }")
        mem_layout = QHBoxLayout(self.memory_card)
        mem_layout.setContentsMargins(16, 6, 16, 6)

        initial_text = self._shuffled_memories[0] if self._shuffled_memories else ""
        self.memory_label = QLabel(initial_text)
        self.memory_label.setStyleSheet("color: #FFB366; font-size: 13px; font-style: italic; font-weight: 500; background: transparent;")
        self.memory_label.setAlignment(Qt.AlignCenter)
        self.memory_label.setWordWrap(True)
        if HAVE_QT:
            self.memory_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        mem_layout.addWidget(self.memory_label)

        active_box.addWidget(self.memory_card)
        main_layout.addWidget(self.active_container, alignment=Qt.AlignCenter)

        # Completion Container (replaces active container when rip finishes)
        self.completion_container = QWidget()
        self.completion_container.setMinimumWidth(860)
        self.completion_container.setMaximumWidth(960)
        if HAVE_QT:
            self.completion_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        comp_box = QVBoxLayout(self.completion_container)
        comp_box.setContentsMargins(0, 0, 0, 0)
        comp_box.setSpacing(16)
        comp_box.setAlignment(Qt.AlignCenter)

        # Output Sister Directories Card
        self.output_card = QFrame()
        self.output_card.setObjectName("previewCard")
        self.output_card.setStyleSheet(
            "QFrame#previewCard { background-color: #16161C; border: 1px solid #2C2C34; border-radius: 10px; padding: 16px; }"
        )
        out_layout = QVBoxLayout(self.output_card)
        out_layout.setSpacing(10)
        out_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.flac_dir_label = QLabel("📁  <b style='color: #F9FAFB;'>[FLAC]</b> <span style='color: #636270;'>•</span> <span style='color: #9CA3AF; font-size: 12px; font-weight: 400;'>Perfect CD copy</span>")
        if HAVE_QT:
            self.flac_dir_label.setTextFormat(Qt.RichText)
        self.flac_dir_label.setStyleSheet("color: #F3F4F6; font-size: 13px;")
        self.flac_dir_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        out_layout.addWidget(self.flac_dir_label, alignment=Qt.AlignLeft)
        self.mp3_dir_label = QLabel("📁  <b style='color: #F9FAFB;'>[MP3]</b> <span style='color: #636270;'>•</span> <span style='color: #9CA3AF; font-size: 12px; font-weight: 400;'>Compressed but still great</span>")
        if HAVE_QT:
            self.mp3_dir_label.setTextFormat(Qt.RichText)
        self.mp3_dir_label.setStyleSheet("color: #F3F4F6; font-size: 13px;")
        self.mp3_dir_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        out_layout.addWidget(self.mp3_dir_label, alignment=Qt.AlignLeft)
        self.aac_dir_label = self.mp3_dir_label  # Backward-compatible attribute alias
        comp_box.addWidget(self.output_card, alignment=Qt.AlignCenter)

        # Action Buttons Row
        comp_btn_row = QHBoxLayout()
        comp_btn_row.setSpacing(16)
        comp_btn_row.setAlignment(Qt.AlignCenter)

        self.btn_open_rip = QPushButton("Open Rip Folder")
        self.btn_open_rip.setStyleSheet(
            "QPushButton { background: #22222B; color: #E5E7EB; border: 1px solid #3B3B48; "
            "border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600; } "
            "QPushButton:hover { background: #2E2E3A; border-color: #FF9E3B; color: #FFFFFF; }"
        )
        self.btn_open_rip.clicked.connect(self._on_open_folder_clicked)
        comp_btn_row.addWidget(self.btn_open_rip)

        self.btn_done = QPushButton("Done")
        self.btn_done.setStyleSheet(
            "QPushButton { background-color: #FF9E3B; color: #121214; border: none; "
            "border-radius: 8px; padding: 10px 32px; font-size: 13px; font-weight: 700; } "
            "QPushButton:hover { background-color: #FFAE5B; }"
        )
        self.btn_done.clicked.connect(self._on_done_clicked)
        comp_btn_row.addWidget(self.btn_done)

        comp_box.addLayout(comp_btn_row)

        self.completion_container.setVisible(False)
        main_layout.addWidget(self.completion_container, alignment=Qt.AlignCenter)

    def show_completion(self, report: AlbumRipReport, on_done: Optional[Callable[[], None]] = None):
        """Transition the ripping view directly into the completion summary screen."""
        self._on_done_callback = on_done
        self._current_rip_folder = report.rip_folder
        if not HAVE_QT:
            return

        if report.overall_status == "failed" or report.successful_tracks_count == 0:
            title_color = "#EF4444"
        elif report.is_perfect:
            title_color = "#10B981"
        elif report.total_errors == 0:
            title_color = "#F59E0B"
        else:
            title_color = "#EF4444"

        led_pix = make_status_led(title_color, size=15)
        if led_pix and not led_pix.isNull():
            self.status_led.setPixmap(led_pix)
            self.status_led.setVisible(True)
        else:
            self.status_led.setVisible(False)

        self.headline.setText(report.clean_headline)
        self.headline.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {title_color}; padding: 2px 4px; min-height: 24px;"
        )
        self.status_sub.setStyleSheet("font-size: 13px; color: #D1D5DB;")
        self.status_sub.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_sub.setWordWrap(False)
        self.status_sub.setText(report.human_readable_summary)

        if report.successful_tracks_count > 0:
            flac_mb = report.flac_size_bytes / (1024 * 1024)
            mp3_bytes = report.mp3_size_bytes or report.aac_size_bytes
            mp3_dir = report.mp3_directory or report.aac_directory
            mp3_mb = mp3_bytes / (1024 * 1024)
            flac_title = report.flac_directory.name if report.flac_directory else "[FLAC]"
            mp3_title = mp3_dir.name if mp3_dir else "[MP3]"
            self.flac_dir_label.setText(
                f"📁  <b style='color: #F9FAFB;'>{html.escape(flac_title)}</b> "
                f"<span style='color: #636270;'>•</span> "
                f"<span style='color: #9CA3AF; font-size: 12px; font-weight: 400;'>Perfect CD copy ({flac_mb:.1f} MB)</span>"
            )
            self.mp3_dir_label.setText(
                f"📁  <b style='color: #F9FAFB;'>{html.escape(mp3_title)}</b> "
                f"<span style='color: #636270;'>•</span> "
                f"<span style='color: #9CA3AF; font-size: 12px; font-weight: 400;'>Compressed but still great ({mp3_mb:.1f} MB)</span>"
            )
            self.flac_dir_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.mp3_dir_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.output_card.setVisible(True)
            self.btn_open_rip.setVisible(bool(report.rip_folder))
        else:
            self.output_card.setVisible(False)
            self.btn_open_rip.setVisible(False)

        is_sad = (
            report.overall_status == "failed"
            or report.total_errors > 0
            or report.successful_tracks_count == 0
        )
        sloth_pix = locate_sloth_complete_pixmap(200, sad=is_sad)
        if sloth_pix and not sloth_pix.isNull():
            self.sloth_emblem.setPixmap(sloth_pix)
            self.transport_widget.stop_animation()
            self.transport_widget.setVisible(False)
            self.sloth_emblem.setVisible(True)
        else:
            self.transport_widget.set_track_progress(1.0)
            self.transport_widget.stop_animation()
            self.sloth_emblem.setVisible(False)
            self.transport_widget.setVisible(True)

        self.active_container.setVisible(False)
        self.completion_container.setVisible(True)

    def reset_view(self):
        """Reset the ripping screen to active extraction state for a new disc."""
        if not HAVE_QT:
            return
        if hasattr(self, "sloth_emblem"):
            self.sloth_emblem.setVisible(False)
        if hasattr(self, "status_led"):
            self.status_led.setVisible(False)
        self.transport_widget.setVisible(True)
        self.transport_widget.set_track_progress(0.0)
        self.transport_widget.start_animation()
        self.headline.setText("Extracting Audio Tracks...")
        self.headline.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #FF9E3B; padding: 2px 4px; min-height: 24px;"
        )
        self.status_sub.setStyleSheet("font-size: 12px; color: #9CA3AF; margin-top: 2px;")
        self.status_sub.setAlignment(Qt.AlignCenter)
        self.status_sub.setWordWrap(False)
        self.status_sub.setText("Reading disc...")
        self.track_bar.setValue(0)
        self.overall_bar.setValue(0)
        self.track_label.setText("Extracting")
        self.overall_label.setText("Overall Album Progress")
        self.badge_retries.setText("🟢 Retries: 0")
        self.badge_retries.setStyleSheet("background: #1A1A22; color: #10B981; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        self.badge_errors.setText("🟢 Errors: 0")
        self.badge_errors.setStyleSheet("background: #1A1A22; color: #10B981; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        self.active_container.setVisible(True)
        self.completion_container.setVisible(False)

    def _on_open_folder_clicked(self):
        folder_path = self._current_rip_folder
        if not folder_path or not folder_path.exists():
            return
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", str(folder_path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder_path)])
            else:
                subprocess.Popen(["xdg-open", str(folder_path)])
        except Exception:
            if HAVE_QT:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder_path)))

    def _on_done_clicked(self):
        if self._on_done_callback:
            self._on_done_callback()

    MEMORY_ROTATION_INTERVAL_MS = 90000  # 90 seconds (1.5 minutes) per nostalgic vignette

    def _start_memory_ticker(self):
        """Cycle through nostalgic quotes every 90 seconds for calm, relaxed reading."""
        if HAVE_QT:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._next_memory)
            self.timer.start(self.MEMORY_ROTATION_INTERVAL_MS)

    def _next_memory(self):
        if not self._shuffled_memories:
            return
        self._memory_index += 1
        if self._memory_index >= len(self._shuffled_memories):
            random.shuffle(self._shuffled_memories)
            self._memory_index = 0
        self.memory_label.setText(self._shuffled_memories[self._memory_index])

    def update_progress(self, progress: RipProgress):
        """Update live progress bars and real-time error telemetry."""
        if not HAVE_QT:
            return

        track_pct = int(round(progress.track_percent))
        overall_pct = int(round(progress.overall_percent))

        # Update animated optical transport laser sled position
        if hasattr(self, "transport_widget") and self.transport_widget:
            self.transport_widget.set_track_progress(progress.track_percent / 100.0)
        if hasattr(self, "status_led"):
            self.status_led.setVisible(False)

        msg = progress.status_message or ""
        msg_lower = msg.lower()
        is_encoding = "transcoding" in msg_lower or "encoding" in msg_lower
        is_tagging = "tagging" in msg_lower or "embedding" in msg_lower or "writing tags" in msg_lower

        # Resolve track title
        title = (getattr(progress, "track_title", "") or "").strip()
        if not title and self._current_album and self._current_album.tracks:
            for t in self._current_album.tracks:
                if t.track_number == progress.current_track:
                    title = (t.title or "").strip()
                    break

        has_title = bool(
            title
            and title.lower() not in (
                f"track {progress.current_track}".lower(),
                f"track {progress.current_track:02d}".lower(),
                f"track{progress.current_track}".lower(),
            )
        )
        clean_title = title.strip('"')

        if progress.current_track > 0 and progress.total_tracks > 0:
            if has_title:
                self.headline.setText(f'Track {progress.current_track} of {progress.total_tracks}: "{clean_title}"')
            else:
                self.headline.setText(f"Track {progress.current_track} of {progress.total_tracks}")
        else:
            self.headline.setText("Extracting Audio Tracks...")

        # Progress bar label: clean phase indicator without track title/number duplication
        if is_encoding:
            self.track_label.setText("Transcoding")
        elif is_tagging:
            self.track_label.setText("Tagging")
        else:
            self.track_label.setText("Extracting")

        self.track_bar.setValue(track_pct)
        self.overall_bar.setValue(overall_pct)
        self.overall_label.setText("Overall Album Progress")

        # Hardware read status & codec signaling
        if is_encoding:
            self.status_sub.setText("Encoding  •  Lossless FLAC + Lossy MP3")
        elif is_tagging:
            self.status_sub.setText("Embedding metadata & cover art")
        elif progress.current_speed:
            self.status_sub.setText(f"Reading disc  •  {progress.current_speed}")
        else:
            self.status_sub.setText("Reading disc...")

        # Update telemetry badges
        if progress.read_retries > 0:
            self.badge_retries.setText(f"🟡 Retries: {progress.read_retries}")
            self.badge_retries.setStyleSheet("background: #2E251A; color: #F59E0B; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        else:
            self.badge_retries.setText("🟢 Retries: 0")
            self.badge_retries.setStyleSheet("background: #1A1A22; color: #10B981; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")

        if progress.unrecoverable_errors > 0:
            self.badge_errors.setText(f"🔴 Errors: {progress.unrecoverable_errors}")
            self.badge_errors.setStyleSheet("background: #331A1A; color: #EF4444; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        else:
            self.badge_errors.setText("🟢 Errors: 0")
            self.badge_errors.setStyleSheet("background: #1A1A22; color: #10B981; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
