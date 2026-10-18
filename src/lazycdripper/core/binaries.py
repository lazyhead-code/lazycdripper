"""Cross-platform discovery and resolution for external bundled binaries (cdparanoia, flac, lame)."""

import io
import logging
import os
from pathlib import Path
import shutil
import sys
from typing import Callable, List, Optional
import urllib.request
import zipfile

logger = logging.getLogger(__name__)


def _is_executable_file(path: Path) -> bool:
    """Check if path exists, is a regular file, and is executable."""
    if not path.is_file():
        return False
    if os.name == "nt":
        return True
    return os.access(path, os.X_OK)


def get_binary_search_paths() -> List[Path]:
    """Return priority list of directories where bundled binaries might reside."""
    search_dirs: List[Path] = []

    # 1. PyInstaller frozen application bundle
    if getattr(sys, "frozen", False):
        # Temp bundle extraction directory (onefile mode)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            p_mei = Path(meipass)
            search_dirs.extend([p_mei / "bin", p_mei])

        # Executable directory (onedir mode or portable app folder)
        exe_dir = Path(sys.executable).resolve().parent
        search_dirs.extend([exe_dir / "bin", exe_dir])

    # 2. Source tree search paths (root/bin, root/assets/bin)
    try:
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        search_dirs.extend([
            repo_root / "bin",
            repo_root / "assets" / "bin",
        ])
    except Exception:
        pass

    # 3. Current working directory ./bin
    cwd = Path.cwd()
    search_dirs.append(cwd / "bin")

    # 4. User AppData directory (%LOCALAPPDATA%/lazycdripper/bin)
    try:
        local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        if local_app_data:
            search_dirs.append(Path(local_app_data) / "lazycdripper" / "bin")
    except Exception:
        pass

    # Filter unique directories
    unique_dirs: List[Path] = []
    seen = set()
    for d in search_dirs:
        resolved = str(d.resolve()) if d.exists() else str(d)
        if resolved not in seen:
            seen.add(resolved)
            unique_dirs.append(d)

    return unique_dirs


def find_binary(name: str, custom_path: Optional[str] = None) -> str:
    """
    Locate an executable binary by name, searching custom paths, bundled directories, and system PATH.

    Returns the resolved string path to the executable, or the raw binary name as fallback.
    """
    if custom_path:
        return custom_path

    candidate_names = [name]
    if os.name == "nt" and not name.lower().endswith(".exe"):
        candidate_names.insert(0, f"{name}.exe")

    # Check search directories
    for search_dir in get_binary_search_paths():
        if not search_dir.is_dir():
            continue
        for cand in candidate_names:
            target = search_dir / cand
            if _is_executable_file(target):
                logger.debug("Found bundled binary for %s at %s", name, target)
                return str(target.resolve())

    # Fall back to system PATH
    for cand in candidate_names:
        system_bin = shutil.which(cand)
        if system_bin:
            return system_bin

    return name


def is_binary_available(name_or_path: str) -> bool:
    """Return True if the binary exists and can be executed."""
    p = Path(name_or_path)
    if _is_executable_file(p):
        return True
    return shutil.which(name_or_path) is not None


def ensure_encoders(progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
    """
    Ensure working standalone FLAC and LAME binaries are available on the system.
    If already available in PATH or search directories, returns True.
    Otherwise, downloads official standalone static binaries for Windows (flac.exe, lame.exe, lame_enc.dll)
    into the application bin or user local AppData directory.

    Returns True if both encoders are ready, False otherwise.
    """
    flac_found = find_binary("flac")
    lame_found = find_binary("lame")

    if is_binary_available(flac_found) and is_binary_available(lame_found):
        return True

    # Destination directories: preferred repo bin/, fallback user cache
    dest_dir = None
    try:
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        repo_bin = repo_root / "bin"
        repo_bin.mkdir(parents=True, exist_ok=True)
        # Test write access
        test_file = repo_bin / ".test_write"
        test_file.touch()
        test_file.unlink()
        dest_dir = repo_bin
    except Exception:
        dest_dir = None

    if not dest_dir:
        try:
            local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            user_bin = Path(local_app_data) / "lazycdripper" / "bin"
            user_bin.mkdir(parents=True, exist_ok=True)
            dest_dir = user_bin
        except Exception as err:
            logger.error("Could not create destination directory for encoders: %s", err)
            return False

    # Download FLAC if missing
    if not is_binary_available(find_binary("flac")):
        flac_url = "https://github.com/xiph/flac/releases/download/1.4.3/flac-1.4.3-win.zip"
        logger.info("Downloading standalone FLAC binary from %s...", flac_url)
        try:
            req = urllib.request.Request(flac_url, headers={"User-Agent": "LazyCDRipper/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                flac_zip_data = resp.read()
            with zipfile.ZipFile(io.BytesIO(flac_zip_data)) as z:
                flac_entry = None
                for name in z.namelist():
                    if name.endswith("flac.exe") and "win64" in name.lower():
                        flac_entry = name
                        break
                if not flac_entry:
                    for name in z.namelist():
                        if name.endswith("flac.exe"):
                            flac_entry = name
                            break
                if flac_entry:
                    target_flac = dest_dir / "flac.exe"
                    target_flac.write_bytes(z.read(flac_entry))
                    logger.info("Installed standalone FLAC to %s", target_flac)
                else:
                    logger.error("flac.exe not found inside downloaded FLAC zip")
        except Exception as err:
            logger.error("Failed to download FLAC binary: %s", err)

    # Download LAME if missing
    if not is_binary_available(find_binary("lame")):
        lame_url = "https://www.rarewares.org/files/mp3/lame-4.0-x64-q4-patched.zip"
        logger.info("Downloading standalone LAME binary from %s...", lame_url)
        try:
            req = urllib.request.Request(lame_url, headers={"User-Agent": "LazyCDRipper/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                lame_zip_data = resp.read()
            with zipfile.ZipFile(io.BytesIO(lame_zip_data)) as z:
                for entry in z.namelist():
                    lower = entry.lower()
                    if lower.endswith(".exe"):
                        target_exe = dest_dir / Path(entry).name
                        target_exe.write_bytes(z.read(entry))
                        logger.info("Installed standalone LAME executable to %s", target_exe)
                    elif lower.endswith(".dll"):
                        target_dll = dest_dir / Path(entry).name
                        target_dll.write_bytes(z.read(entry))
                        logger.info("Installed standalone LAME DLL to %s", target_dll)
        except Exception as err:
            logger.error("Failed to download LAME binary: %s", err)

    return is_binary_available(find_binary("flac")) and is_binary_available(find_binary("lame"))


__all__ = [
    "find_binary",
    "is_binary_available",
    "ensure_encoders",
    "get_binary_search_paths",
]
