"""Ripping view screen featuring the nostalgic vinyl/CD visual and rotating memories ticker."""

import math
import random
from typing import Optional
from lazycdripper.core.models import AlbumInfo, RipProgress

try:
    from PySide6.QtCore import QPointF, Qt, QTimer
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QConicalGradient,
        QPainter,
        QPainterPath,
        QPen,
        QRadialGradient,
    )
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QVBoxLayout,
        QWidget,
    )
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    QWidget = object


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
        if HAVE_QT and not self._timer.isActive():
            self._timer.start(30)
        super().showEvent(event)

    def hideEvent(self, event):
        if HAVE_QT and self._timer.isActive():
            self._timer.stop()
        super().hideEvent(event)

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
        self._setup_ui()
        self._start_memory_ticker()

    def set_album(self, album: Optional[AlbumInfo]):
        """Set the active album model to retrieve track titles and metadata."""
        self._current_album = album

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 24, 30, 24)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignCenter)

        # Central Visual Emblem / Animated Optical Transport Banner
        self.visual_frame = QFrame()
        self.visual_frame.setObjectName("rippingBanner")
        self.visual_frame.setMinimumWidth(640)
        self.visual_frame.setMaximumWidth(760)
        self.visual_frame.setStyleSheet(
            "QFrame#rippingBanner { "
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(28, 24, 20, 0.72), stop:1 rgba(16, 16, 22, 0.76)); "
            "  border: 1.5px solid rgba(255, 158, 59, 0.50); "
            "  border-radius: 16px; "
            "  padding: 24px; "
            "}"
        )
        visual_layout = QVBoxLayout(self.visual_frame)
        visual_layout.setAlignment(Qt.AlignCenter)
        visual_layout.setSpacing(10)

        # Hardware engraved top badge
        self.spec_badge = QLabel("RED BOOK AUDIO • 16-BIT / 44.1 kHz PCM")
        self.spec_badge.setStyleSheet(
            "background: rgba(255, 158, 59, 0.08); border: 1px solid rgba(255, 158, 59, 0.25); "
            "color: #DDA15E; font-size: 10px; font-weight: 700; letter-spacing: 1.2px; "
            "padding: 3px 12px; border-radius: 10px;"
        )
        self.spec_badge.setAlignment(Qt.AlignCenter)
        visual_layout.addWidget(self.spec_badge, alignment=Qt.AlignCenter)

        # Custom animated optical transport disc
        self.transport_widget = HiFiOpticalTransportWidget()
        visual_layout.addWidget(self.transport_widget, alignment=Qt.AlignCenter)

        # Generous breathing room between spinning disc and track title
        if HAVE_QT:
            visual_layout.addSpacing(18)

        self.headline = QLabel("Extracting Audio Tracks...")
        self.headline.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #FF9E3B; letter-spacing: 0.3px; padding-top: 4px;"
        )
        self.headline.setAlignment(Qt.AlignCenter)
        self.headline.setWordWrap(False)
        visual_layout.addWidget(self.headline)

        self.status_sub = QLabel("Reading optical sectors with dynamic jitter correction")
        self.status_sub.setStyleSheet("font-size: 12px; color: #9CA3AF; margin-top: 2px;")
        self.status_sub.setAlignment(Qt.AlignCenter)
        self.status_sub.setWordWrap(False)
        visual_layout.addWidget(self.status_sub)

        main_layout.addWidget(self.visual_frame)

        # Progress Section
        progress_container = QWidget()
        progress_container.setMinimumWidth(640)
        progress_container.setMaximumWidth(760)
        progress_box = QVBoxLayout(progress_container)
        progress_box.setContentsMargins(0, 0, 0, 0)
        progress_box.setSpacing(12)

        # 1. Current Track Progress
        self.track_label = QLabel("Extracting")
        self.track_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #F3F4F6;")
        progress_box.addWidget(self.track_label)

        self.track_bar = QProgressBar()
        self.track_bar.setRange(0, 100)
        self.track_bar.setValue(0)
        progress_box.addWidget(self.track_bar)

        # 2. Overall Album Progress
        self.overall_label = QLabel("Overall Album: 0%")
        self.overall_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #F3F4F6;")
        progress_box.addWidget(self.overall_label)

        self.overall_bar = QProgressBar()
        self.overall_bar.setRange(0, 100)
        self.overall_bar.setValue(0)
        progress_box.addWidget(self.overall_bar)

        main_layout.addWidget(progress_container)

        # Telemetry Status Pills
        telemetry_row = QHBoxLayout()
        telemetry_row.setSpacing(16)
        telemetry_row.setAlignment(Qt.AlignCenter)

        self.badge_jitter = QLabel("🟢 Jitter Align: 0")
        self.badge_jitter.setStyleSheet("background: #1A1A22; color: #38BDF8; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        telemetry_row.addWidget(self.badge_jitter)

        self.badge_retries = QLabel("🟢 Sector Retries: 0")
        self.badge_retries.setStyleSheet("background: #1A1A22; color: #10B981; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        telemetry_row.addWidget(self.badge_retries)

        self.badge_errors = QLabel("🟢 Errors: 0")
        self.badge_errors.setStyleSheet("background: #1A1A22; color: #10B981; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        telemetry_row.addWidget(self.badge_errors)

        main_layout.addLayout(telemetry_row)

        # Nostalgic Memories Ticker Card (Fixed height eliminates vertical layout jitter)
        self.memory_card = QFrame()
        self.memory_card.setObjectName("previewCard")
        self.memory_card.setMinimumWidth(640)
        self.memory_card.setMaximumWidth(760)
        self.memory_card.setFixedHeight(58)
        self.memory_card.setStyleSheet("QFrame#previewCard { background-color: #16161C; border: 1px solid #2C2C34; border-radius: 8px; }")
        mem_layout = QHBoxLayout(self.memory_card)
        mem_layout.setContentsMargins(16, 6, 16, 6)
        if HAVE_QT:
            mem_layout.setAlignment(Qt.AlignCenter)

        initial_text = self._shuffled_memories[0] if self._shuffled_memories else ""
        self.memory_label = QLabel(initial_text)
        self.memory_label.setStyleSheet("color: #FFB366; font-size: 13px; font-style: italic; font-weight: 500;")
        self.memory_label.setAlignment(Qt.AlignCenter)
        self.memory_label.setWordWrap(True)
        mem_layout.addWidget(self.memory_label)

        main_layout.addWidget(self.memory_card)

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
                if is_encoding:
                    self.headline.setText(f'Transcoding: "{clean_title}" ({progress.current_track} of {progress.total_tracks})')
                elif is_tagging:
                    self.headline.setText(f'Tagging: "{clean_title}" ({progress.current_track} of {progress.total_tracks})')
                else:
                    self.headline.setText(f'Extracting: "{clean_title}" ({progress.current_track} of {progress.total_tracks})')
            else:
                if is_encoding:
                    self.headline.setText(f"Transcoding Track {progress.current_track} of {progress.total_tracks}...")
                elif is_tagging:
                    self.headline.setText(f"Tagging Track {progress.current_track} of {progress.total_tracks}...")
                else:
                    self.headline.setText(f"Extracting Track {progress.current_track} of {progress.total_tracks}...")
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
        self.overall_label.setText(f"Overall Album Progress: {overall_pct}%")

        # Hardware read status & codec signaling
        speed_suffix = f"  •  {progress.current_speed}" if progress.current_speed else ""
        if is_encoding:
            self.status_sub.setText("Lossless FLAC + 256k AAC")
        elif is_tagging:
            self.status_sub.setText("Embedding metadata & cover art")
        else:
            self.status_sub.setText(f"Reading optical sectors{speed_suffix}")

        # Update telemetry badges
        self.badge_jitter.setText(f"Jitter Align: {progress.jitter_corrections}")

        if progress.read_retries > 0:
            self.badge_retries.setText(f"🟡 Retries: {progress.read_retries}")
            self.badge_retries.setStyleSheet("background: #2E251A; color: #F59E0B; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        else:
            self.badge_retries.setText("🟢 Sector Retries: 0")

        if progress.unrecoverable_errors > 0:
            self.badge_errors.setText(f"🔴 Errors: {progress.unrecoverable_errors}")
            self.badge_errors.setStyleSheet("background: #331A1A; color: #EF4444; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;")
        else:
            self.badge_errors.setText("🟢 Errors: 0")
