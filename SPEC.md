# Lazy CD Ripper — Technical Specification (SPEC.md)

| Status | Version | Date | Target Platforms |
| :--- | :--- | :--- | :--- |
| **Approved / Active** | `0.9.3` | October 2026 | Windows 10 / 11 (64-bit) |

---

## 1. Vision & Core Principles

1. **Effortless Defaults, Zero Clutter:** The software is opinionated. Users do not need to configure sector offsets, gap detection, or complex encoder flags.
2. **Audio Integrity:** Ripping uses native Win32 `IOCTL_CDROM_RAW_READ` sector streaming directly via kernel `DeviceIoControl`. Audio is either preserved losslessly (FLAC) or encoded at maximum perceptual transparency and universal compatibility (MP3 CBR @ 320 kbps).
3. **Optimized Format Pair:** FLAC serves bit-perfect archival needs, while MP3 serves mobile, car, legacy, and Bluetooth listening with 100% patent-free freedom and universal hardware support.
4. **Rich Metadata & Visuals:** Complete track information, disc numbers, and pristine artwork are automatically pulled from MusicBrainz and Cover Art Archive and embedded directly into audio files, along with an album `cover.jpg`.
5. **Decoupled Architecture:** Core logic (disc reading, metadata fetching, transcoding, tagging) is strictly separated from the presentation layer (GUI).

---

## 2. Audio Pipeline & Codec Standards

### 2.1 Source Format
* **Medium:** Compact Disc Digital Audio (CD-DA, Red Book standard).
* **Signal:** 2-channel 16-bit Linear PCM at 44.1 kHz sampling rate (1,411.2 kbps raw bitrate).

### 2.2 Output Formats & Encoding Specifications

| Format | Container | Codec / Encoder | Recommended Preset / Settings | Justification |
| :--- | :--- | :--- | :--- | :--- |
| **FLAC** | `.flac` | Official Xiph.org `flac` (`flac.exe`) | `-8 --verify` | Lossless, bit-perfect, universal playback, built-in MD5 stream integrity check. 100% patent-free open standard (BSD license). |
| **MP3** | `.mp3` | Official RareWares/LAME `lame` (`lame.exe`) | `-b 320 -q 0` | Constant Bitrate (CBR) 320 kbps, highest psychoacoustic quality algorithm (`-q 0`). 100% patent-free worldwide (all MP3 patents expired in 2017). Universal compatibility across all car stereos, mobile devices, and media players. |

### 2.3 The "Zero Dilemma" Always-Dual-Rip Policy
* **No Codec Checkboxes:** Lazy CD Ripper eliminates format choice paralysis. Every rip automatically generates **both** libraries in parallel:
  * `<Artist> - <Album> (<Year>) [FLAC]/` — Lossless master archive for home hi-fi & media servers.
  * `<Artist> - <Album> (<Year>) [MP3]/` — Universal high-bitrate library for phone, car, and portable listening.
* **Why Always Both?**
  * The mechanical CD drive read is the time-consuming step (3–5 minutes).
  * Once the raw 16-bit PCM WAV is in the scratch buffer, encoding to FLAC takes ~10 seconds and encoding to MP3 takes ~5 seconds.
  * Pointing out a destination directory yields both optimal formats in a single pass. If a user only needs one, they can simply delete the sister folder.
* **Why MP3 @ 320 kbps CBR (and not AAC)?**
  * **100% Patent-Free Freedom:** All worldwide patents covering the MP3 format expired in April/May 2017 (Fraunhofer IIS officially terminated the licensing program). In contrast, AAC remains encumbered by proprietary Standard Essential Patents (SEPs) managed by the Via Licensing Alliance (Via LA), which impose royalty liabilities on distributed encoder binaries.
  * **Audiophile Transparency:** At Constant Bitrate 320 kbps with LAME's highest-accuracy psychoacoustic model (`-q:a 0`), MP3 reaches maximum bit reservoir allocation and is indistinguishable from original uncompressed Red Book CD audio in double-blind ABX tests.
  * **Universal Hardware Interoperability:** Plays natively without issue on every vehicle head unit, vintage media player, smartphone, smart TV, gaming console, and desktop OS in existence without container or profile incompatibilities.

---

## 3. Metadata & Album Art Specification

### 3.1 Metadata Provider
* **Primary Source:** **MusicBrainz** via the official XML/JSON Web Service (WS2).
* **Identification Method:** Disc Table of Contents (TOC) hashed into a 28-character base64 **MusicBrainz DiscID** via pure Python SHA-1 calculation (`calculate_musicbrainz_discid`, bit-exact libdiscid compliance with zero native C dependencies).
* **Secondary / Fallback:**
  * Fuzzy TOC matching on MusicBrainz WS2.
  * CD-Text (if present on physical disc).
  * Manual release search / barcode lookup if disc is uncatalogued.

### 3.2 Metadata Tag Mappings

| Field | FLAC (Vorbis Comment) | MP3 (ID3v2.3) |
| :--- | :--- | :--- |
| Track Title | `TITLE` | `TIT2` |
| Artist | `ARTIST` | `TPE1` |
| Album Artist | `ALBUMARTIST` | `TPE2` |
| Album Title | `ALBUM` | `TALB` |
| Release Year | `DATE` | `TYER` |
| Track Number | `TRACKNUMBER` | `TRCK` (formatted as `track/total_tracks`) |
| Total Tracks | `TRACKTOTAL` | `TRCK` |
| Disc Number | `DISCNUMBER` | `TPOS` (formatted as `disc/total_discs`) |
| Total Discs | `DISCTOTAL` | `TPOS` |
| Genre | `GENRE` | `TCON` |
| MusicBrainz DiscID | `MUSICBRAINZ_DISCID` | `TXXX:MusicBrainz DiscID` |

### 3.3 Album Artwork Strategy
* **Source:** **Cover Art Archive (CAA)** (`coverartarchive.org`), linked directly to the MusicBrainz Release ID.
* **Image Sizing:** High-resolution front cover (target 1000px–1400px square). Images are converted/optimized to progressive JPEG.
* **Automated Selection & Ranking:**
  * Uses multi-source aggregation (Release Group + specific pressings) with heuristic scoring:
    - Prioritizes canonical Front covers from Release Group (+3000 pts) and release Fronts (+2000 pts).
    - Heavily demotes non-front scans (back, booklet, CD medium/disc face).
    - Rewards 900–2500px resolution (+400 pts) and 1:1 square aspect ratio (+200 pts).
    - Top candidate is selected and cached automatically, adhering to the 1-button zero-configuration philosophy.
* **Dual Persistence:**
  1. **Embedded:** Stored inside every audio track (FLAC Vorbis picture block type 3; MP3 ID3v2.3 `APIC` frame with MIME `image/jpeg` and picture type 3 Front Cover).
  2. **File Asset:** Saved as `cover.jpg` in the album root folder (and inside each `Disc NN` subfolder for multi-disc sets) for file managers, Windows Media Player, and media servers (Plex/Jellyfin/Roon).

---

## 4. File Organization & Path Naming

### 4.1 Opinionated Directory Hierarchy

#### Single-Disc Album
```text
<Output Directory>/
└── <Artist> - <Album> (<Year>) [<FORMAT>]/
    ├── 01 - <Track Title>.<ext>
    ├── 02 - <Track Title>.<ext>
    ├── ...
    └── cover.jpg
```

#### Multi-Disc Album
```text
<Output Directory>/
└── <Artist> - <Album> (<Year>) [<FORMAT>]/
    ├── Disc 01/
    │   ├── 01 - <Track Title>.<ext>
    │   └── 02 - <Track Title>.<ext>
    ├── Disc 02/
    │   ├── 01 - <Track Title>.<ext>
    │   └── 02 - <Track Title>.<ext>
    └── cover.jpg
```

### 4.2 Opinionated Track Naming
Adhering to the zero-settings philosophy, track filenames are consistently and automatically formatted without manual toggles:
* Format: `<TrackNumber> - <TrackTitle>.<ext>` (e.g., `01 - Same as It Ever Was.flac`)
* Zero-padded 2-digit track numbers.
* Clean, sanitized titles safe across all filesystems.

### 4.3 Sanitization Rules
Paths must be clean across all OS filesystems:
* Reserved characters replaced or stripped: `< > : " / \ | ? *`
* Trailing periods and spaces removed from folder/file names (Windows limitation).
* Track numbers are always zero-padded to 2 digits (`01`, `02`, ... `12`).

---

## 5. Ripping Engine & Error Detection

### 5.1 Ripping Backend
* **Engine:** Native Win32 `IOCTL_CDROM_RAW_READ` via `DeviceIoControl` (`lazycdripper.ripper.windows`) with optional `cdparanoia` CLI fallback.
* **Modes:**
  * Direct Red Book 2,352-byte raw sector stream extraction.
  * Sector batching with single-sector fallback for damaged areas.
  * Buffer alignment and gap padding.
* **Progress Reporting:** Read progress reported per sector/track with error status counters:
  * `Jitter` (corrected automatically).
  * `Scratch / Correction` (multi-pass verified).
  * `Unrecoverable` (flagged in summary log).

---

## 6. User Experience & Aesthetics

### 6.1 Visual Identity: "Rock / Metal / Blues Craft"
* **Theme:** Deep dark mode (charcoal/matte black background, brushed aluminum accents).
* **Accents:** Warm amber / tube amplifier glow (`#FF9E3B`), subtle cyan/silver highlights.
* **Tactile Feedback:** Analog-style progress indicators, high-contrast typography, album art preview with vinyl groove or jewel-case frame styling.
* **In-App Liner Notes & Philosophy:**
  A stylish, accessible drawer or dialog styled like an album insert sleeve containing Lazyhead Code's mission statement:
  > *"We've gained so much with music streaming services.*  
  > *We've lost so much as well.*  
  > 
  > *Buying a music CD and listening to the whole album brings back the magic.*  
  > 
  > *We don't have CD drives in cars and laptops anymore. But we can rip music for ourselves (all it takes is an external drive), copy it to our phone, and have the exact same experience.*  
  > 
  > *This application is opinionated AF, but it rips to virtually the best options: high-quality MP3 (320 kbps CBR) and FLAC. Why MP3 instead of other lossy formats? Because MP3 is 100% patent-free worldwide, universally supported by every car, stereo, and device on Earth, and at 320 kbps CBR it is perceptually transparent. Why FLAC? Because it's a picture-perfect copy of your CD—highest possible quality. We may not really hear the difference much, but I'm glad to surrender to an illusion :)*  
  > 
  > *Have fun and welcome back to the magical world of music!*  
  > 
  > *Yours truly,*  
  > **Lazyhead Code** 💿"*
* **Workflow:**
  1. Disc inserted -> Auto-detected in ~1-2 seconds.
  2. Album metadata & canonical cover artwork automatically loaded from MusicBrainz / Cover Art Archive.
  3. User glances at tracks & artwork.
  4. User clicks one prominent **"Rip to FLAC + MP3"** button and selects destination folder.
  5. Smooth progress view showing track-by-track ripping & parallel FLAC/MP3 encoding with nostalgic music memories.
  6. Completion dialog with file sizes, option to open output folder, or eject disc.

---

## 7. Packaging & Deployment Strategy

* **Zero Installers Policy:** Traditional Windows setup wizards (Inno Setup, NSIS, MSI) are strictly omitted. Unsigned installer executables trigger aggressive Windows Defender SmartScreen warnings, request unnecessary administrative UAC elevation, and leave registry clutter. Since Lazy CD Ripper requires no system drivers or background services, traditional installers add friction with zero user benefit.
* **Portable Bundles Only:**
  * Public releases are distributed exclusively as self-contained Windows `x64` portable `.zip` archives.
  * Every bundle includes the PyInstaller-frozen application (`LazyCDRipper.exe`) and patent-clean encoder binaries (executed silently via `subprocess.CREATE_NO_WINDOW` with zero console flashing).
  * **Patent-Free Binary Architecture (Option A):** Releases bundle the official, dedicated standalone binaries: Xiph.org `flac.exe` (~1.5 MB, BSD) and RareWares/LAME `lame.exe` (~800 KB, LGPL). Total binary footprint is **under 2.5 MB** (drastically reducing app package size from ~85 MB to ~15 MB). Zero AAC or video codec code exists in either binary, guaranteeing 100% patent-free legal distribution.
  * Fully portable: extract anywhere (Desktop, external drive, portable media), launch immediately, and delete the directory to remove. Zero registry writes, zero system dependencies, and zero admin rights needed.
* **Future Distribution (Store Only):**
  * Any future distribution beyond standalone `.zip` archives will be handled exclusively via the Microsoft Store / Windows Store (packaged MSIX) to provide verified cryptographic reputation and sandboxed background updates without ever maintaining separate setup wizards.
