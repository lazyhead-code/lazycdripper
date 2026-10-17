"""Native Windows Audio CD extraction backend using Win32 DeviceIoControl raw sector reads."""

import logging
import os
from pathlib import Path
import platform
import re
import time
from typing import Callable, Dict, List, Optional
import wave

from lazycdripper.core.models import RipProgress, TrackInfo
from lazycdripper.disc.toc import DiscTOC, TrackTOC, read_windows_toc

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[RipProgress], None]

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
IOCTL_CDROM_RAW_READ = 0x0002403E
SECTOR_SIZE_RAW = 2352  # 16-bit 44.1kHz stereo PCM per Red Book sector


# TRACK_MODE_TYPE enumeration from ntddcdrm.h:
# YellowMode2 = 0 (Mode 2 Form 1/2 CD-ROM)
# XAForm2 = 1 (CD-ROM XA Mode 2 Form 2)
# CDDA = 2 (Compact Disc Digital Audio, IEC 908 Red Book)
TRACK_MODE_YELLOW_MODE2 = 0
TRACK_MODE_XA_FORM2 = 1
TRACK_MODE_CDDA = 2


def sector_to_lba(sector_offset: int) -> int:
    """
    Convert Red Book MSF frame sector offset (where track 1 begins at sector 150)
    to a zero-based Logical Block Address (LBA) for SCSI/Win32 CD-ROM commands.
    """
    return max(0, sector_offset - 150) if sector_offset >= 150 else max(0, sector_offset)


try:
    import ctypes
    from ctypes import wintypes

    class RAW_READ_INFO(ctypes.Structure):
        _fields_ = [
            ("DiskOffset", ctypes.c_int64),
            ("SectorCount", ctypes.c_uint32),
            ("TrackMode", ctypes.c_uint32),
        ]
except Exception:
    RAW_READ_INFO = None


class WindowsCddaRipper:
    """Extracts Audio CD tracks natively on Windows without requiring external binaries."""

    def __init__(self):
        pass

    @property
    def is_available(self) -> bool:
        """Check if running natively on Windows NT."""
        return os.name == "nt" or "windows" in platform.system().lower()

    def query_toc(self, device: Optional[str] = None) -> Optional[DiscTOC]:
        """Query CD Table of Contents on Windows."""
        return read_windows_toc(device)

    def rip_track(
        self,
        track_number: int,
        output_wav_path: Path,
        device: Optional[str] = None,
        total_tracks: int = 1,
        on_progress: Optional[ProgressCallback] = None,
    ) -> bool:
        """
        Extract a single audio track directly to a 16-bit 44.1kHz PCM WAV file
        via Win32 IOCTL_CDROM_RAW_READ.
        """
        if not self.is_available:
            logger.error("WindowsCddaRipper is only supported on Windows platforms.")
            return False

        output_wav_path.parent.mkdir(parents=True, exist_ok=True)
        toc = self.query_toc(device)
        target_track: Optional[TrackTOC] = None
        if toc:
            for t in toc.tracks:
                if t.track_number == track_number:
                    target_track = t
                    break

        if not target_track:
            logger.error("Track %d not found in disc TOC", track_number)
            return False

        start_sector = target_track.start_sector
        length_sectors = target_track.length_sectors
        if length_sectors <= 0:
            logger.error("Invalid sector length %d for track %d", length_sectors, track_number)
            return False

        # Extract drive letter
        letter = "D:"
        if device:
            m = re.search(r"([A-Za-z]):", str(device))
            if m:
                letter = f"{m.group(1).upper()}:"
        dev_path = f"\\\\.\\{letter}"

        progress = RipProgress(
            current_track=track_number,
            total_tracks=total_tracks,
            track_percent=0.0,
            status_message="Extracting track...",
        )

        try:
            h_device = ctypes.windll.kernel32.CreateFileW(
                dev_path,
                GENERIC_READ,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                None,
                OPEN_EXISTING,
                0,
                None,
            )

            if h_device in (-1, 0xFFFFFFFFFFFFFFFF, 0xFFFFFFFF):
                err = ctypes.windll.kernel32.GetLastError()
                logger.error("Could not open CD device %s for raw extraction (Win32 err %d)", dev_path, err)
                if on_progress:
                    progress.unrecoverable_errors += 1
                    progress.status_message = f"Cannot open drive {dev_path} (error {err})"
                    on_progress(progress)
                return False

            try:
                # Read in batches of 20 sectors (47,040 bytes per batch, ~46KB)
                batch_sectors = 20
                bytes_per_batch = batch_sectors * SECTOR_SIZE_RAW
                buf = (ctypes.c_uint8 * bytes_per_batch)()
                bytes_returned = wintypes.DWORD()

                sectors_read = 0
                pcm_chunks: List[bytes] = []
                consecutive_errors = 0

                start_time = time.monotonic()
                last_speed_time = start_time
                last_speed_sectors = 0

                while sectors_read < length_sectors:
                    cur_sectors = min(batch_sectors, length_sectors - sectors_read)
                    cur_sector_offset = start_sector + sectors_read
                    lba = sector_to_lba(cur_sector_offset)

                    info = RAW_READ_INFO(
                        DiskOffset=lba * 2048,
                        SectorCount=cur_sectors,
                        TrackMode=TRACK_MODE_CDDA,
                    )

                    success = ctypes.windll.kernel32.DeviceIoControl(
                        h_device,
                        IOCTL_CDROM_RAW_READ,
                        ctypes.byref(info),
                        ctypes.sizeof(info),
                        ctypes.byref(buf),
                        cur_sectors * SECTOR_SIZE_RAW,
                        ctypes.byref(bytes_returned),
                        None,
                    )

                    if success:
                        consecutive_errors = 0
                        valid_bytes = bytes_returned.value
                        pcm_chunks.append(bytes(buf[:valid_bytes]))
                        sectors_read += cur_sectors
                    else:
                        err_code = ctypes.windll.kernel32.GetLastError()
                        progress.read_retries += 1
                        logger.warning(
                            "Batch read failed at sector %d (LBA %d, count %d) on %s (Win32 err %d). Falling back to single-sector reads...",
                            cur_sector_offset, lba, cur_sectors, dev_path, err_code,
                        )
                        if on_progress:
                            pct = (sectors_read / length_sectors) * 100.0
                            progress.track_percent = min(100.0, pct)
                            on_progress(progress)

                        # Sector-by-sector fallback for this batch
                        batch_aborted = False
                        for s_idx in range(cur_sectors):
                            single_sector_offset = cur_sector_offset + s_idx
                            single_lba = sector_to_lba(single_sector_offset)
                            single_info = RAW_READ_INFO(
                                DiskOffset=single_lba * 2048,
                                SectorCount=1,
                                TrackMode=TRACK_MODE_CDDA,
                            )
                            single_buf = (ctypes.c_uint8 * SECTOR_SIZE_RAW)()
                            single_returned = wintypes.DWORD()

                            single_ok = False
                            for retry_attempt in range(3):
                                if retry_attempt > 0:
                                    progress.read_retries += 1
                                    if on_progress:
                                        pct = (sectors_read / length_sectors) * 100.0
                                        progress.track_percent = min(100.0, pct)
                                        on_progress(progress)
                                single_ok = ctypes.windll.kernel32.DeviceIoControl(
                                    h_device,
                                    IOCTL_CDROM_RAW_READ,
                                    ctypes.byref(single_info),
                                    ctypes.sizeof(single_info),
                                    ctypes.byref(single_buf),
                                    SECTOR_SIZE_RAW,
                                    ctypes.byref(single_returned),
                                    None,
                                )
                                if single_ok:
                                    break

                            if single_ok:
                                consecutive_errors = 0
                                pcm_chunks.append(bytes(single_buf[:single_returned.value]))
                                sectors_read += 1
                            else:
                                s_err = ctypes.windll.kernel32.GetLastError()
                                progress.unrecoverable_errors += 1
                                consecutive_errors += 1
                                logger.error(
                                    "Failed to read raw sector %d (LBA %d) on %s (Win32 err %d)",
                                    single_sector_offset, single_lba, dev_path, s_err,
                                )
                                # Pad missing sector with silence to maintain track timing
                                pcm_chunks.append(b"\x00" * SECTOR_SIZE_RAW)
                                sectors_read += 1
                                if on_progress:
                                    pct = (sectors_read / length_sectors) * 100.0
                                    progress.track_percent = min(100.0, pct)
                                    on_progress(progress)

                                # Circuit breaker: continuous read failures (e.g. drive disconnected/inaccessible)
                                if consecutive_errors >= 20:
                                    logger.error(
                                        "Aborting Track %d extraction: exceeded 20 consecutive sector failures",
                                        track_number,
                                    )
                                    batch_aborted = True
                                    break

                        if batch_aborted:
                            break

                    # Real-time speed calculation: 75 sectors = 1 second of standard CD audio (1x)
                    now = time.monotonic()
                    dt = now - last_speed_time
                    if dt >= 0.35:
                        d_sec = sectors_read - last_speed_sectors
                        instant_speed = (d_sec / 75.0) / dt
                        if instant_speed > 0.1:
                            progress.current_speed = f"{instant_speed:.1f}x"
                        last_speed_time = now
                        last_speed_sectors = sectors_read

                    pct = (sectors_read / length_sectors) * 100.0
                    progress.track_percent = min(100.0, pct)
                    if on_progress:
                        on_progress(progress)

                # Extraction finished or aborted
                if sectors_read < length_sectors or not pcm_chunks:
                    logger.error(
                        "Track %d extraction aborted early: read %d/%d sectors (%d unrecoverable errors)",
                        track_number, sectors_read, length_sectors, progress.unrecoverable_errors,
                    )
                    pct = (sectors_read / length_sectors) * 100.0
                    progress.track_percent = min(100.0, pct)
                    if on_progress:
                        progress.status_message = f"Track {track_number} extraction failed"
                        on_progress(progress)
                    return False

                if progress.unrecoverable_errors > (length_sectors // 2):
                    logger.error(
                        "Track %d extraction failed: %d/%d sectors unrecoverable (>50%% failure)",
                        track_number, progress.unrecoverable_errors, length_sectors,
                    )
                    if on_progress:
                        progress.status_message = f"Track {track_number} extraction failed"
                        on_progress(progress)
                    return False

                raw_pcm = b"".join(pcm_chunks)
                if not raw_pcm:
                    if on_progress:
                        on_progress(progress)
                    return False

                with wave.open(str(output_wav_path), "wb") as wf:
                    wf.setnchannels(2)      # Stereo
                    wf.setsampwidth(2)     # 16-bit
                    wf.setframerate(44100) # 44.1 kHz
                    wf.writeframes(raw_pcm)

                if on_progress:
                    progress.track_percent = 100.0
                    if progress.unrecoverable_errors > 0:
                        progress.status_message = f"Track {track_number} extracted with {progress.unrecoverable_errors} errors"
                    elif progress.read_retries > 0:
                        progress.status_message = f"Track {track_number} extracted with {progress.read_retries} retries"
                    else:
                        progress.status_message = f"Track {track_number} extracted cleanly"
                    on_progress(progress)

                return output_wav_path.exists()
            finally:
                ctypes.windll.kernel32.CloseHandle(h_device)

        except Exception as err:
            logger.exception("Error extracting track %d via Windows CDDA: %s", track_number, err)
            if on_progress:
                progress.unrecoverable_errors += 1
                progress.status_message = f"Track {track_number} extraction error: {err}"
                on_progress(progress)
            return False

    def rip_disc(
        self,
        tracks: List[TrackInfo],
        scratch_dir: Path,
        device: Optional[str] = None,
        on_progress: Optional[ProgressCallback] = None,
    ) -> Dict[int, Path]:
        """Extract all audio tracks in sequence into scratch WAV files."""
        scratch_dir.mkdir(parents=True, exist_ok=True)
        results: Dict[int, Path] = {}
        total = len(tracks)

        for idx, track in enumerate(tracks, start=1):
            wav_path = scratch_dir / f"track_{track.track_number:02d}_scratch.wav"

            def track_callback(p: RipProgress):
                completed_tracks = idx - 1
                current_contrib = p.track_percent / 100.0
                p.overall_percent = ((completed_tracks + current_contrib) / total) * 100.0
                if on_progress:
                    on_progress(p)

            success = self.rip_track(
                track_number=track.track_number,
                output_wav_path=wav_path,
                device=device,
                total_tracks=total,
                on_progress=track_callback,
            )

            if success:
                results[track.track_number] = wav_path
            else:
                logger.error("Failed to extract track %d", track.track_number)

        return results
