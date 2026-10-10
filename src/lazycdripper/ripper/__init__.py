"""Audio CD extraction subsystem supporting cdparanoia, native Windows CDDA, and mock backends."""

from typing import Union
from lazycdripper.ripper.cdparanoia import CdparanoiaRipper
from lazycdripper.ripper.mock import MockRipper
from lazycdripper.ripper.windows import WindowsCddaRipper


def get_default_ripper() -> Union[WindowsCddaRipper, CdparanoiaRipper, MockRipper]:
    """
    Select the optimal ripping backend:
    1. Direct native Win32 CDDA extraction (primary engine on Windows).
    2. Fallback to CdparanoiaRipper if available.
    3. Fallback to MockRipper for automated tests and headless environments.
    """
    win_ripper = WindowsCddaRipper()
    if win_ripper.is_available:
        return win_ripper

    cdparanoia = CdparanoiaRipper()
    if cdparanoia.is_available:
        return cdparanoia

    return MockRipper()


__all__ = [
    "CdparanoiaRipper",
    "WindowsCddaRipper",
    "MockRipper",
    "get_default_ripper",
]
