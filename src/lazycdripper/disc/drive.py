"""Optical drive detection and hardware abstraction for Windows."""

from dataclasses import dataclass
import json
import logging
import string
import subprocess
from typing import List, Optional

try:
    import ctypes
    from ctypes import wintypes
except ImportError:
    ctypes = None
    wintypes = None

logger = logging.getLogger(__name__)


@dataclass
class DriveInfo:
    """Represents an optical CD/DVD drive detected on the system."""
    device_path: str
    name: str
    is_ready: bool = False
    media_present: bool = False
    drive_letter: Optional[str] = None  # Windows drive letter (e.g. 'D:')


def detect_optical_drives() -> List[DriveInfo]:
    """
    Detect all available CD-ROM / DVD-RW optical drives on Windows.
    Returns a list of DriveInfo instances.
    """
    return _detect_windows_drives()


def _get_windows_drive_model_ioctl(letter: str) -> Optional[str]:
    """Query STORAGE_DEVICE_DESCRIPTOR via direct IOCTL in ~0.1ms without external processes."""
    if not ctypes or not hasattr(ctypes, "windll"):
        return None
    try:
        # dwDesiredAccess = 0 allows querying device attributes without media or admin lock
        FILE_SHARE_READ = 1
        FILE_SHARE_WRITE = 2
        OPEN_EXISTING = 3
        IOCTL_STORAGE_QUERY_PROPERTY = 0x002D1400

        h_device = ctypes.windll.kernel32.CreateFileW(
            f"\\\\.\\{letter}:",
            0,  # Zero access for storage property queries
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            0,
            None,
        )
        if h_device in (-1, 0xFFFFFFFFFFFFFFFF, 0xFFFFFFFF):
            return None

        try:
            # Query StorageDeviceProperty (0), PropertyStandardQuery (0)
            query_buf = (ctypes.c_uint32 * 3)(0, 0, 0)
            out_buf = (ctypes.c_char * 1024)()
            bytes_ret = wintypes.DWORD()
            ok = ctypes.windll.kernel32.DeviceIoControl(
                h_device,
                IOCTL_STORAGE_QUERY_PROPERTY,
                ctypes.byref(query_buf),
                ctypes.sizeof(query_buf),
                ctypes.byref(out_buf),
                ctypes.sizeof(out_buf),
                ctypes.byref(bytes_ret),
                None,
            )
            if ok and bytes_ret.value >= 24:
                vendor_offset = int.from_bytes(out_buf[16:20], "little")
                product_offset = int.from_bytes(out_buf[20:24], "little")
                vendor = ""
                product = ""
                if 0 < vendor_offset < bytes_ret.value:
                    vendor = out_buf[vendor_offset:].split(b"\x00")[0].decode("ascii", "ignore").strip()
                if 0 < product_offset < bytes_ret.value:
                    product = out_buf[product_offset:].split(b"\x00")[0].decode("ascii", "ignore").strip()
                full_name = f"{vendor} {product}".strip()
                if full_name:
                    return full_name
        finally:
            ctypes.windll.kernel32.CloseHandle(h_device)
    except Exception as err:
        logger.debug("Fast IOCTL model check failed for %s: %s", letter, err)
    return None


def _detect_windows_drives() -> List[DriveInfo]:
    """Detect optical drives on Windows using GetDriveTypeW (0.1ms) with native IOCTL descriptor query."""
    drives: List[DriveInfo] = []
    ctypes_available = False

    if ctypes and hasattr(ctypes, "windll"):
        try:
            kernel32 = ctypes.windll.kernel32
            # DRIVE_CDROM = 5 in Win32 API
            DRIVE_CDROM = 5

            # Check all drive letters A to Z (~0.05ms)
            for letter in string.ascii_uppercase:
                root_path = f"{letter}:\\"
                drive_type = kernel32.GetDriveTypeW(root_path)
                if drive_type == DRIVE_CDROM:
                    model_name = _get_windows_drive_model_ioctl(letter) or "CD/DVD Drive"
                    drives.append(
                        DriveInfo(
                            device_path=f"\\\\.\\{letter}:",
                            name=f"[{letter}:] {model_name}",
                            drive_letter=f"{letter}:",
                            is_ready=True,
                        )
                    )
            ctypes_available = True
        except Exception as err:
            logger.debug("ctypes GetDriveTypeW failed or not on Windows: %s", err)
            ctypes_available = False

    # Only invoke slow PowerShell fallback if ctypes was completely unavailable (e.g., unit test mocks)
    if not ctypes_available and not drives:
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_CDROMDrive | Select-Object -Property Drive, Caption | ConvertTo-Json",
            ]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=4,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                items = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
                for item in items:
                    drive_val = item.get("Drive")
                    caption = item.get("Caption") or "CD/DVD Drive"
                    if drive_val:
                        letter = drive_val.rstrip(":\\")
                        drives.append(
                            DriveInfo(
                                device_path=f"\\\\.\\{letter}:",
                                name=f"[{letter}:] {caption}",
                                drive_letter=f"{letter}:",
                                is_ready=True,
                            )
                        )
        except Exception as err:
            logger.debug("PowerShell Win32_CDROMDrive fallback check: %s", err)

    return drives


def get_default_optical_drive() -> Optional[DriveInfo]:
    """Get the primary optical drive, or None if no drive is connected."""
    drives = detect_optical_drives()
    return drives[0] if drives else None
