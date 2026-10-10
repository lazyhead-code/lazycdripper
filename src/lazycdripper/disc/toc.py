import base64
from dataclasses import dataclass, field
import hashlib
import logging
import os
from pathlib import Path
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

SECTORS_PER_SECOND = 75  # Red Book CD-DA standard: 75 sectors per second


@dataclass
class TrackTOC:
    """Represents a single track entry in the CD Table of Contents."""
    track_number: int
    start_sector: int
    end_sector: int
    length_sectors: int
    is_audio: bool = True

    @property
    def duration_seconds(self) -> float:
        """Calculate track duration in seconds from sector count."""
        return float(self.length_sectors) / SECTORS_PER_SECOND


@dataclass
class DiscTOC:
    """Represents the complete Table of Contents for an optical disc."""
    first_track: int
    last_track: int
    leadout_sector: int
    tracks: List[TrackTOC] = field(default_factory=list)
    disc_id: str = ""
    freedb_disc_id: str = ""

    @property
    def total_tracks(self) -> int:
        return len(self.tracks)

    @property
    def total_duration_seconds(self) -> float:
        return sum(t.duration_seconds for t in self.tracks)

    @property
    def musicbrainz_toc_string(self) -> str:
        """
        Formatted TOC string for MusicBrainz WS2:
        '{first_track} {last_track} {leadout_sector} {track1_offset} {track2_offset} ...'
        """
        parts = [str(self.first_track), str(self.last_track), str(self.leadout_sector)]
        parts.extend(str(t.start_sector) for t in self.tracks)
        return " ".join(parts)


def calculate_musicbrainz_discid(
    first_track: int,
    last_track: int,
    leadout_sector: int,
    track_offsets: List[int],
) -> str:
    """
    Calculate the official 28-character MusicBrainz DiscID from CD TOC sector offsets
    using pure Python (SHA-1 + URL-safe Base64).
    Matches libdiscid specification bit-for-bit with zero external C dependencies.
    """
    msg = f"{first_track:02X}{last_track:02X}"
    offsets = [leadout_sector] + list(track_offsets)

    for i in range(100):
        if i < len(offsets):
            msg += f"{offsets[i]:08X}"
        else:
            msg += "00000000"

    digest = hashlib.sha1(msg.encode("ascii")).digest()

    # Convert to URL-safe base64 used by MusicBrainz: '+' -> '.', '/' -> '_', '=' -> '-'
    disc_id = (
        base64.b64encode(digest)
        .decode("ascii")
        .replace("+", ".")
        .replace("/", "_")
        .replace("=", "-")
    )
    return disc_id


def calculate_freedb_discid(
    first_track: int,
    last_track: int,
    leadout_sector: int,
    track_offsets: List[int],
) -> str:
    """
    Calculate the standard 8-character FreeDB/GNUDb DiscID.
    Matches libdiscid create_freedb_disc_id implementation.
    """
    def cddb_sum(n: int) -> int:
        ret = 0
        while n > 0:
            ret += n % 10
            n //= 10
        return ret

    n = 0
    for offset in track_offsets:
        n += cddb_sum(offset // SECTORS_PER_SECOND)

    first_offset = track_offsets[0] if track_offsets else 150
    t = (leadout_sector // SECTORS_PER_SECOND) - (first_offset // SECTORS_PER_SECOND)
    disc_id = f"{((n % 0xFF) << 24 | (t << 8) | last_track):08x}"
    return disc_id


def parse_cdparanoia_toc_output(output: str) -> Optional[DiscTOC]:
    """
    Parse the standard text output from 'cdparanoia -Q' (Table of Contents query).
    Returns a DiscTOC object with calculated DiscID, or None if no audio tracks found.
    """
    if not output:
        return None

    tracks: List[TrackTOC] = []
    leadout_sector: Optional[int] = None

    # Matches lines like: "  1.     3900 [00:52.00]          150 [00:02.00]    no   no  2"
    # Group 1: track num, Group 2: length sectors, Group 3: begin sector
    track_regex = re.compile(r"^\s*(\d+)\.\s+(\d+)\s+\[.*?\]\s+(\d+)\s+\[.*?\]", re.MULTILINE)
    # Matches: "TOTAL   234000 [52:00.00] (lead-out at sector 234150)"
    leadout_regex = re.compile(r"lead-out at sector\s+(\d+)", re.IGNORECASE)

    for match in track_regex.finditer(output):
        track_num = int(match.group(1))
        length_sec = int(match.group(2))
        begin_sec = int(match.group(3))
        end_sec = begin_sec + length_sec

        tracks.append(
            TrackTOC(
                track_number=track_num,
                start_sector=begin_sec,
                end_sector=end_sec,
                length_sectors=length_sec,
                is_audio=True,
            )
        )

    lead_match = leadout_regex.search(output)
    if lead_match:
        leadout_sector = int(lead_match.group(1))
    elif tracks:
        # Fallback: last track's end sector
        leadout_sector = tracks[-1].end_sector

    if not tracks or leadout_sector is None:
        return None

    first_track = tracks[0].track_number
    last_track = tracks[-1].track_number
    offsets = [t.start_sector for t in tracks]

    disc_id = calculate_musicbrainz_discid(
        first_track=first_track,
        last_track=last_track,
        leadout_sector=leadout_sector,
        track_offsets=offsets,
    )
    freedb_id = calculate_freedb_discid(
        first_track=first_track,
        last_track=last_track,
        leadout_sector=leadout_sector,
        track_offsets=offsets,
    )

    return DiscTOC(
        first_track=first_track,
        last_track=last_track,
        leadout_sector=leadout_sector,
        tracks=tracks,
        disc_id=disc_id,
        freedb_disc_id=freedb_id,
    )


def _extract_drive_letter(device: Optional[str]) -> Optional[str]:
    """Extract Windows drive letter (e.g. 'D:') from device path or string."""
    if not device:
        return None
    m = re.search(r"([A-Za-z]):", str(device))
    if m:
        return f"{m.group(1).upper()}:"
    return None


def read_cda_file(file_path: Path) -> Optional[TrackTOC]:
    """
    Parse a Windows .cda stub file (44-byte RIFF resource) to extract track number,
    start sector, and duration in sectors.
    """
    try:
        data = file_path.read_bytes()
        if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"CDDA":
            return None

        # Track number at offset 0x16 (2 bytes uint16 little-endian)
        track_num = int.from_bytes(data[0x16:0x18], "little")
        if track_num == 0:
            m = re.search(r"Track(\d+)", file_path.name, re.IGNORECASE)
            if m:
                track_num = int(m.group(1))

        # Start sector (range offset in frames) at 0x1C (4 bytes uint32 little-endian)
        start_sector = int.from_bytes(data[0x1C:0x20], "little")
        # Fallback to MSF format at 0x24-0x26 if 0x1C is empty: (min * 60 + sec) * 75 + frames
        if start_sector == 0 and len(data) >= 0x28:
            start_sector = (data[0x26] * 60 + data[0x25]) * 75 + data[0x24]

        # Duration in sectors at 0x20 (4 bytes uint32 little-endian)
        length_sectors = int.from_bytes(data[0x20:0x24], "little")
        # Fallback to MSF duration at 0x28-0x2A
        if length_sectors == 0 and len(data) >= 0x2B:
            length_sectors = (data[0x2A] * 60 + data[0x29]) * 75 + data[0x28]

        if track_num > 0 and length_sectors > 0:
            return TrackTOC(
                track_number=track_num,
                start_sector=start_sector,
                end_sector=start_sector + length_sectors,
                length_sectors=length_sectors,
                is_audio=True,
            )
    except Exception as err:
        logger.debug("Failed to read CDA file %s: %s", file_path, err)
    return None


def read_windows_cda_toc(drive_letter: str) -> Optional[DiscTOC]:
    """
    Read Audio CD Table of Contents on Windows by inspecting mounted .cda files.
    Works for any standard non-administrator user process.
    """
    try:
        letter = _extract_drive_letter(drive_letter)
        if not letter:
            return None
        clean_letter = letter.rstrip(":")

        root_candidates = [f"{clean_letter}:\\", f"{clean_letter}:/"]
        cda_files: List[Path] = []

        for root_str in root_candidates:
            try:
                if os.path.exists(root_str):
                    try:
                        for fname in os.listdir(root_str):
                            if fname.lower().endswith(".cda"):
                                cda_files.append(Path(root_str) / fname)
                    except OSError:
                        pass
            except Exception:
                pass
            if cda_files:
                break

        if not cda_files:
            return None

        tracks: List[TrackTOC] = []
        for f in cda_files:
            t = read_cda_file(f)
            if t:
                tracks.append(t)

        if not tracks:
            return None

        tracks.sort(key=lambda x: x.track_number)

        # Standard Red Book CD audio track 1 offset normalization:
        # MusicBrainz DiscID specification requires absolute disc frame count (Track 1 is at 150 frames = 2 sec pregap).
        # If Track 1's start_sector was stored as relative LBA 0, adjust all sectors by +150.
        if tracks and tracks[0].start_sector < 150:
            shift = 150 - tracks[0].start_sector
            for t in tracks:
                t.start_sector += shift
                t.end_sector += shift

        first_track = tracks[0].track_number
        last_track = tracks[-1].track_number
        leadout_sector = tracks[-1].end_sector
        track_offsets = [t.start_sector for t in tracks]

        disc_id = calculate_musicbrainz_discid(
            first_track=first_track,
            last_track=last_track,
            leadout_sector=leadout_sector,
            track_offsets=track_offsets,
        )
        freedb_id = calculate_freedb_discid(
            first_track=first_track,
            last_track=last_track,
            leadout_sector=leadout_sector,
            track_offsets=track_offsets,
        )

        logger.info(
            "Successfully read Windows .cda TOC for %s: %d tracks, disc_id=%s, freedb_id=%s",
            drive_letter, len(tracks), disc_id, freedb_id,
        )
        return DiscTOC(
            first_track=first_track,
            last_track=last_track,
            leadout_sector=leadout_sector,
            tracks=tracks,
            disc_id=disc_id,
            freedb_disc_id=freedb_id,
        )
    except Exception as err:
        logger.debug("Windows .cda TOC reading failed for %s: %s", drive_letter, err)
        return None


def read_windows_ioctl_toc(drive_letter: str) -> Optional[DiscTOC]:
    """
    Read CD Table of Contents on Windows directly via Win32 IOCTL_CDROM_READ_TOC.
    Provides bit-for-bit physical disc TOC from optical drive firmware.
    """
    try:
        import ctypes
        from ctypes import wintypes

        GENERIC_READ = 0x80000000
        FILE_SHARE_READ = 0x00000001
        FILE_SHARE_WRITE = 0x00000002
        OPEN_EXISTING = 3
        IOCTL_CDROM_READ_TOC = 0x00024000

        class TRACK_DATA(ctypes.Structure):
            _fields_ = [
                ("Reserved", ctypes.c_uint8),
                ("ControlAndAdr", ctypes.c_uint8),
                ("TrackNumber", ctypes.c_uint8),
                ("Reserved1", ctypes.c_uint8),
                ("Address", ctypes.c_uint8 * 4),
            ]

        class CDROM_TOC(ctypes.Structure):
            _fields_ = [
                ("Length", ctypes.c_uint8 * 2),
                ("FirstTrack", ctypes.c_uint8),
                ("LastTrack", ctypes.c_uint8),
                ("TrackData", TRACK_DATA * 100),
            ]

        letter = _extract_drive_letter(drive_letter)
        clean_letter = letter.rstrip(":") if letter else drive_letter.rstrip("\\/").rstrip(":")
        device_path = f"\\\\.\\{clean_letter}:"

        h_device = ctypes.windll.kernel32.CreateFileW(
            device_path,
            GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            0,
            None,
        )

        if h_device in (-1, 0xFFFFFFFFFFFFFFFF, 0xFFFFFFFF):
            return None

        try:
            toc_buf = CDROM_TOC()
            bytes_returned = wintypes.DWORD()
            success = ctypes.windll.kernel32.DeviceIoControl(
                h_device,
                IOCTL_CDROM_READ_TOC,
                None, 0,
                ctypes.byref(toc_buf),
                ctypes.sizeof(toc_buf),
                ctypes.byref(bytes_returned),
                None,
            )
            if not success:
                return None

            first_track = toc_buf.FirstTrack
            last_track = toc_buf.LastTrack
            num_entries = (bytes_returned.value - 4) // ctypes.sizeof(TRACK_DATA)

            def msf_to_lba(addr):
                return (addr[1] * 60 + addr[2]) * 75 + addr[3]

            tracks: List[TrackTOC] = []
            leadout_sector = 0
            track_offsets: List[int] = []

            for i in range(num_entries):
                entry = toc_buf.TrackData[i]
                t_num = entry.TrackNumber
                lba = msf_to_lba(entry.Address)
                if t_num == 0xAA:  # Lead-out track
                    leadout_sector = lba
                elif first_track <= t_num <= last_track:
                    track_offsets.append(lba)

            for i in range(len(track_offsets)):
                t_num = first_track + i
                start = track_offsets[i]
                end = track_offsets[i + 1] if i + 1 < len(track_offsets) else leadout_sector
                length = max(0, end - start)
                tracks.append(
                    TrackTOC(
                        track_number=t_num,
                        start_sector=start,
                        end_sector=end,
                        length_sectors=length,
                        is_audio=True,
                    )
                )

            if not tracks or leadout_sector == 0:
                return None

            disc_id = calculate_musicbrainz_discid(
                first_track=first_track,
                last_track=last_track,
                leadout_sector=leadout_sector,
                track_offsets=track_offsets,
            )
            freedb_id = calculate_freedb_discid(
                first_track=first_track,
                last_track=last_track,
                leadout_sector=leadout_sector,
                track_offsets=track_offsets,
            )

            logger.info(
                "Successfully read Win32 IOCTL TOC for %s: %d tracks, disc_id=%s, freedb_id=%s",
                device_path, len(tracks), disc_id, freedb_id,
            )
            return DiscTOC(
                first_track=first_track,
                last_track=last_track,
                leadout_sector=leadout_sector,
                tracks=tracks,
                disc_id=disc_id,
                freedb_disc_id=freedb_id,
            )
        finally:
            ctypes.windll.kernel32.CloseHandle(h_device)
    except Exception as err:
        logger.debug("Win32 IOCTL TOC reading failed for %s: %s", drive_letter, err)
        return None


def read_windows_toc(device: Optional[str] = None) -> Optional[DiscTOC]:
    """
    Read Audio CD Table of Contents on Windows using native mechanisms:
    1. Fast IOCTL_CDROM_READ_TOC via DeviceIoControl (firmware accurate leadout & pregaps)
    2. Filesystem inspection of mounted Track*.cda files (fallback)
    """
    letter = _extract_drive_letter(device)
    if not letter:
        # Check detected optical drives first if device was not explicitly specified
        try:
            from lazycdripper.disc.drive import detect_optical_drives
            for d in detect_optical_drives():
                if d.drive_letter:
                    toc = read_windows_ioctl_toc(d.drive_letter) or read_windows_cda_toc(d.drive_letter)
                    if toc:
                        return toc
        except Exception:
            pass

        # Fallback: check standard drive letters D: through Z: for any loaded audio CD
        for cand_letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            cand = f"{cand_letter}:"
            toc = read_windows_ioctl_toc(cand) or read_windows_cda_toc(cand)
            if toc:
                return toc
        return None

    # Try IOCTL first (hardware exact), fallback to .cda
    return read_windows_ioctl_toc(letter) or read_windows_cda_toc(letter)


def get_disc_toc(device: Optional[str] = None) -> Optional[DiscTOC]:
    """
    Retrieve Disc Table of Contents on Windows:
    1. Try native .cda inspection or IOCTL_CDROM_READ_TOC.
    2. Fallback to bundled cdparanoia query if available.
    """
    win_toc = read_windows_toc(device)
    if win_toc:
        return win_toc

    from lazycdripper.ripper.cdparanoia import CdparanoiaRipper
    ripper = CdparanoiaRipper()
    if ripper.is_available:
        return ripper.query_toc(device)

    return None
