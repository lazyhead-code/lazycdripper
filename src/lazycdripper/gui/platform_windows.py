"""Windows DWM (Desktop Window Manager) integration for high-end boutique dark theme."""

import logging
import sys

logger = logging.getLogger(__name__)

# DWM attribute constants (Windows 10 / 11)
DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36
DWMWA_COLOR_NONE = 0xFFFFFFFE
DWMWA_COLOR_DEFAULT = 0xFFFFFFFF


def hex_to_colorref(hex_str: str) -> int:
    """Convert '#RRGGBB' to Win32 COLORREF (0x00BBGGRR)."""
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) != 6:
        return 0
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    return (b << 16) | (g << 8) | r


def setup_windows_window(
    widget,
    border_color_hex: str = "#25252E",
    caption_color_hex: str = "#0C0C0F",
    text_color_hex: str = "#F2F1EC",
) -> bool:
    """
    Apply native Windows 11 / 10 DWM dark theme attributes to a Qt window.

    1. Enables native immersive dark mode title bars (eliminates glaring white title bars).
    2. Enforces solid opaque window border color (eliminates 1px transparent DWM bleed-through).
    3. Customizes caption bar and text color to match the boutique hi-fi chassis palette.
    """
    if sys.platform != "win32":
        return False

    try:
        import ctypes
        hwnd = int(widget.winId())
        dwmapi = ctypes.windll.dwmapi

        # 1. Immersive Dark Mode
        true_val = ctypes.c_int(1)
        res = dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(true_val),
            ctypes.sizeof(true_val),
        )
        if res != 0:
            # Fallback for Windows 10 versions 1809 - 1909
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                ctypes.byref(true_val),
                ctypes.sizeof(true_val),
            )

        # 2. Window Border Color (Win11 Build 22000+)
        b_val = ctypes.c_int(hex_to_colorref(border_color_hex))
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_BORDER_COLOR,
            ctypes.byref(b_val),
            ctypes.sizeof(b_val),
        )

        # 3. Caption / Title Bar Color (Win11 Build 22000+)
        c_val = ctypes.c_int(hex_to_colorref(caption_color_hex))
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_CAPTION_COLOR,
            ctypes.byref(c_val),
            ctypes.sizeof(c_val),
        )

        # 4. Title Text Color (Win11 Build 22000+)
        t_val = ctypes.c_int(hex_to_colorref(text_color_hex))
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_TEXT_COLOR,
            ctypes.byref(t_val),
            ctypes.sizeof(t_val),
        )
        return True
    except Exception as err:
        logger.debug("setup_windows_window DWM call skipped: %s", err)
        return False
