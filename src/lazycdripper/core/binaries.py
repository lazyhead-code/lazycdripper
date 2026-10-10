"""Cross-platform discovery and resolution for external bundled binaries (cdparanoia, ffmpeg)."""

import logging
import os
from pathlib import Path
import shutil
import sys
from typing import Callable, List, Optional

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


def ensure_ffmpeg(progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[str]:
    """
    Ensure a working FFmpeg binary is available on the system.
    If already available in PATH or search directories, returns its path.
    Otherwise, downloads a standalone static binary from official distribution wheels
    into the application or user cache directory.

    Returns the absolute path to the executable, or None if unavailable.
    """
    found = find_binary("ffmpeg")
    if is_binary_available(found):
        return found

    import io
    import urllib.request
    import zipfile

    # Official imageio-ffmpeg wheel distribution URL for Windows 64-bit (clean standalone static build)
    url = "https://files.pythonhosted.org/packages/2c/c6/fa760e12a2483469e2bf5058c5faff664acf66cadb4df2ad6205b016a73d/imageio_ffmpeg-0.6.0-py3-none-win_amd64.whl"
    target_name = "ffmpeg.exe"

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
            logger.error("Could not create destination directory for FFmpeg: %s", err)
            return None

    target_path = dest_dir / target_name

    logger.info("Downloading standalone FFmpeg binary for Windows to %s...", target_path)
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            total_size = int(resp.headers.get("content-length", 0))
            data = bytearray()
            chunk_size = 65536
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                data.extend(chunk)
                if progress_callback and total_size > 0:
                    progress_callback(len(data), total_size)

        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for entry in z.namelist():
                if entry.endswith(".exe"):
                    target_path.write_bytes(z.read(entry))
                    logger.info("Successfully installed standalone FFmpeg to %s", target_path)
                    return str(target_path.resolve())

        logger.error("FFmpeg binary not found inside downloaded wheel package")
        return None
    except Exception as err:
        logger.error("Failed to download/install FFmpeg binary: %s", err)
        return None


__all__ = [
    "find_binary",
    "is_binary_available",
    "ensure_ffmpeg",
    "get_binary_search_paths",
]
