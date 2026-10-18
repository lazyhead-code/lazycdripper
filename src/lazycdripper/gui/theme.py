"""Boutique High-End Audio Equipment theme styling and Qt StyleSheets for Lazy CD Ripper."""

# Color Palette Constants
COLOR_BG_DARK = "#0C0C0F"         # Deep matte obsidian chassis
COLOR_PANEL_BG = "#131318"        # Faceplate panel & card background
COLOR_BORDER = "#25252E"          # Brushed metal hairline border
COLOR_BORDER_FOCUS = "#FF9E3B"    # Focused border (amber tube glow)

# Accents
COLOR_AMBER = "#FF9E3B"           # Vacuum tube warm amber glow
COLOR_AMBER_HOVER = "#FFAE5E"     # Bright incandescent amber
COLOR_AMBER_DARK = "#D97706"      # Deep burnished amber
COLOR_CYAN = "#38BDF8"            # Analog needle secondary accent
COLOR_GREEN = "#10B981"           # Pristine bit-perfect indicator
COLOR_YELLOW = "#F59E0B"          # Recovered indicator
COLOR_RED = "#EF4444"             # Damaged indicator

# Typography
COLOR_TEXT_PRIMARY = "#F2F1EC"    # Warm parchment white (non-fatiguing)
COLOR_TEXT_SECONDARY = "#8E8D96"  # Muted silver / warm zinc secondary
COLOR_TEXT_MUTED = "#5A5964"      # Muted hardware captions

DARK_ROCK_STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLOR_BG_DARK};
    color: {COLOR_TEXT_PRIMARY};
}}

QWidget {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: {COLOR_TEXT_PRIMARY};
    selection-background-color: {COLOR_AMBER};
    selection-color: #000000;
}}

/* Boutique Faceplate Cards */
QFrame#cardPanel {{
    background-color: {COLOR_PANEL_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    padding: 16px;
}}

/* Jewel Case Artwork Frame (Zero padding for precision centered image alignment) */
QFrame#artworkFrame {{
    background-color: #0E0E12;
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    padding: 0px;
    margin: 0px;
}}

/* Gatefold Manifesto Welcome Box */
QFrame#gatefoldCard {{
    background-color: #121217;
    border: 1px solid rgba(255, 158, 59, 0.22);
    border-radius: 16px;
    padding: 24px;
}}

/* Technical Specification Plaque (Dual Rip Info Card) */
QLabel#policyCard {{
    background-color: #121217;
    border: 1px solid #1E1E26;
    border-radius: 8px;
    padding: 10px 14px;
}}

/* Push Buttons */
QPushButton {{
    background-color: #1E1E26;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #282833;
    border-color: #424254;
}}

QPushButton:pressed {{
    background-color: #15151C;
}}

/* Precision Hardware Icon Button ([ ↻ ] Refresh) */
QPushButton#btnIconRefresh {{
    background-color: #141419;
    color: {COLOR_TEXT_SECONDARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    font-size: 15px;
    font-weight: bold;
    padding: 0px;
}}

QPushButton#btnIconRefresh:hover {{
    background-color: #1E1E26;
    border-color: {COLOR_AMBER};
    color: {COLOR_AMBER};
}}

QPushButton#btnIconRefresh:pressed {{
    background-color: #0F0F14;
    border-color: {COLOR_AMBER_DARK};
    color: {COLOR_AMBER_DARK};
}}

/* Primary Action Button ("Rip to FLAC + MP3" — Precision Machined Amber Glow) */
QPushButton#primaryRipButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFAE57, stop:1 #E08528);
    color: #0C0C0F;
    border: none;
    border-radius: 12px;
    padding: 16px 32px;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}

QPushButton#primaryRipButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFBA70, stop:1 #EA8F33);
}}

QPushButton#primaryRipButton:pressed {{
    background: #C46F17;
}}

QPushButton#primaryRipButton:disabled {{
    background: #25252C;
    color: #555560;
}}

/* Tactile Hardware Micro-Toggles (Settings Switches) */
QPushButton#pillButton {{
    background-color: #141419;
    color: {COLOR_TEXT_SECONDARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    min-height: 24px;
    max-height: 26px;
}}

QPushButton#pillButton:checked {{
    background-color: #241A10;
    color: {COLOR_AMBER};
    border: 1px solid {COLOR_AMBER_DARK};
    font-weight: 700;
}}

QPushButton#pillButton:hover {{
    border-color: #3F3E4D;
    color: {COLOR_TEXT_PRIMARY};
}}

QPushButton#pillButton:checked:hover {{
    border-color: {COLOR_AMBER};
}}

/* Boutique Optical Drive Selector / ComboBox */
QComboBox {{
    background-color: #141419;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 6px 32px 6px 14px;
    font-size: 12px;
    font-weight: 600;
}}

QComboBox:hover {{
    border-color: #3D3C4B;
}}

QComboBox:focus {{
    border-color: {COLOR_AMBER};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    background: transparent;
}}

QComboBox::down-arrow {{
    image: none;
    width: 0px;
    height: 0px;
}}

QComboBox QAbstractItemView {{
    background-color: #141419;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    selection-background-color: #291F14;
    selection-color: {COLOR_AMBER};
    padding: 4px;
    outline: none;
}}

/* Precision Track Table (No Clunky Spreadsheet Grid) */
QTableWidget {{
    background-color: #101015;
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    gridline-color: transparent;
    font-size: 13px;
    outline: none;
}}

QTableWidget::item {{
    padding: 10px 12px;
    border-bottom: 1px solid #181820;
}}

QTableWidget::item:selected {{
    background-color: transparent;
}}

QTableWidget::item:hover {{
    background-color: transparent;
}}

QHeaderView {{
    background-color: transparent;
    border: none;
}}

QHeaderView::section {{
    background-color: transparent;
    color: {COLOR_TEXT_SECONDARY};
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* Analog Progress Bar */
QProgressBar {{
    background-color: #15151C;
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    height: 20px;
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    color: {COLOR_TEXT_PRIMARY};
}}

QProgressBar::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLOR_AMBER_DARK}, stop:1 {COLOR_AMBER_HOVER});
    border-radius: 9px;
}}

/* Ergonomic Floating Pill Scrollbars (Comfortable, fat target, rounded capsule track and handle) */
QScrollBar:vertical {{
    background-color: #181820;
    width: 12px;
    margin: 0px;
    border: none;
    border-radius: 6px;
}}

QScrollBar:vertical:hover {{
    background-color: #242330;
}}

QScrollBar::handle:vertical {{
    background-color: #424154;
    min-height: 38px;
    border: none;
    border-radius: 6px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLOR_AMBER};
}}

QScrollBar::handle:vertical:pressed {{
    background-color: {COLOR_AMBER_HOVER};
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    border: none;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    width: 0px;
    background: none;
    border: none;
}}

QScrollBar:horizontal {{
    background-color: #181820;
    height: 12px;
    margin: 0px;
    border: none;
    border-radius: 6px;
}}

QScrollBar:horizontal:hover {{
    background-color: #242330;
}}

QScrollBar::handle:horizontal {{
    background-color: #424154;
    min-width: 38px;
    border: none;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLOR_AMBER};
}}

QScrollBar::handle:horizontal:pressed {{
    background-color: {COLOR_AMBER_HOVER};
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
    border: none;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    height: 0px;
    width: 0px;
    background: none;
    border: none;
}}

QAbstractScrollArea::corner {{
    background: transparent;
    border: none;
}}
"""
