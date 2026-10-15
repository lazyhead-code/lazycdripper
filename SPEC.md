# Lazy CD Ripper — Technical Specification (SPEC.md)

| Status | Version | Date | Target Platforms |
| :--- | :--- | :--- | :--- |
| **Approved / Active** | `0.9.2` | October 2026 | Windows 10 / 11 (64-bit) |

---

## 1. Vision & Core Principles

1. **Effortless Defaults, Zero Clutter:** The software is opinionated. Users do not need to configure sector offsets, gap detection, or complex encoder flags.
2. **Audio Integrity:** Ripping uses native Win32 `IOCTL_CDROM_RAW_READ` sector streaming directly via kernel `DeviceIoControl`. Audio is either preserved losslessly (FLAC) or encoded at maximum perceptual transparency (AAC-LC @ 256kbps).
3. **Optimized Format Pair:** FLAC serves bit-perfect archival needs, while AAC-LC serves mobile and Bluetooth listening without cross-codec transcoding penalties.
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
| **FLAC** | `.flac` | Native `flac` (via FFmpeg) | `-compression_level 8 -verify` | Lossless, bit-perfect, universal playback, built-in MD5 stream integrity check. |
| **AAC** | `.m4a` | Fraunhofer FDK-AAC (`libfdk_aac`) or FFmpeg native `aac` | **FDK:** VBR mode 5 (~256-320kbps)<br>**Native:** `-b:a 256k -c:a aac` | AAC-LC profile. Native Bluetooth codec format across modern mobile ecosystems (avoids lossy cross-codec transcode artifacts). |

### 2.3 The "Zero Dilemma" Always-Dual-Rip Policy
* **No Codec Checkboxes:** Lazy CD Ripper eliminates format choice paralysis. Every rip automatically generates **both** libraries in parallel:
  * `<Artist> - <Album> (<Year>) [FLAC]/` — Lossless master archive for home hi-fi & media servers.
  * `<Artist> - <Album> (<Year>) [AAC]/` — High-efficiency library for phone, car, and Bluetooth headphones.
* **Why Always Both?**
  * The mechanical CD drive read is the time-consuming step (3–5 minutes).
  * Once the raw 16-bit PCM WAV is in the scratch buffer, encoding to FLAC takes ~10 seconds and encoding to AAC takes ~5 seconds.
  * Pointing out a destination directory yields both optimal formats in a single pass. If a user only needs one, they can simply delete the sister folder.
* **Why AAC-LC @ 256kbps (Not 320kbps)?**
  * **AAC-LC @ 256kbps VBR/CBR is psychoacoustically transparent to human hearing** (the reference standard utilized by Apple Music and the Fraunhofer Institute), delivering exceptional audio quality without wasting bandwidth or disk space.
  * 320kbps AAC uses ~25% more disk space with zero audible benefit and can exceed Bluetooth bandwidth margins on certain mobile stacks.

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

| Field | FLAC (Vorbis Comment) | AAC (`.m4a` MP4 Atom) |
| :--- | :--- | :--- |
| Track Title | `TITLE` | `©nam` |
| Artist | `ARTIST` | `©ART` |
| Album Artist | `ALBUMARTIST` | `aART` |
| Album Title | `ALBUM` | `©alb` |
| Release Year | `DATE` | `©day` |
| Track Number | `TRACKNUMBER` | `trkn` (tuple: `track, total_tracks`) |
| Total Tracks | `TRACKTOTAL` | `trkn` |
| Disc Number | `DISCNUMBER` | `disk` (tuple: `disc, total_discs`) |
| Total Discs | `DISCTOTAL` | `disk` |
| Genre | `GENRE` | `©gen` |
| MusicBrainz DiscID | `MUSICBRAINZ_DISCID` | `----:com.apple.iTunes:MusicBrainz DiscID` |

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
  1. **Embedded:** Stored inside every audio track (FLAC Vorbis picture block type 3; MP4 atom `covr`).
  2. **File Asset:** Saved as `cover.jpg` in the album root folder for file managers and media servers (Plex/Jellyfin/Roon).

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
  > *This application is opinionated AF, but it rips to virtually the best options: high-quality AAC and FLAC. Why AAC instead of MP3? Because modern Bluetooth headphones use AAC natively; using a lossy codec from a different family is not optimal. Why FLAC? Because it's a picture-perfect copy of your CD—highest possible quality. We may not really hear the difference much, but I'm glad to surrender to an illusion :)*  
  > 
  > *Have fun and welcome back to the magical world of music!*  
  > 
  > *Yours truly,*  
  > **Lazyhead Code** 💿"*
* **Workflow:**
  1. Disc inserted -> Auto-detected in ~1-2 seconds.
  2. Album metadata & canonical cover artwork automatically loaded from MusicBrainz / Cover Art Archive.
  3. User glances at tracks & artwork.
  4. User clicks one prominent **"Rip to FLAC + AAC"** button and selects destination folder.
  5. Smooth progress view showing track-by-track ripping & parallel FLAC/AAC encoding with nostalgic music memories.
  6. Completion dialog with file sizes, option to open output folder, or eject disc.

---

## 7. Packaging & Deployment Strategy

* **Zero Installers Policy:** Traditional Windows setup wizards (Inno Setup, NSIS, MSI) are strictly omitted. Unsigned installer executables trigger aggressive Windows Defender SmartScreen warnings, request unnecessary administrative UAC elevation, and leave registry clutter. Since Lazy CD Ripper requires no system drivers or background services, traditional installers add friction with zero user benefit.
* **Portable Bundles Only:**
  * Public releases are distributed exclusively as self-contained Windows `x64` portable `.zip` archives.
  * Every bundle includes the PyInstaller-frozen application (`LazyCDRipper.exe`) and the pre-bundled `bin/ffmpeg.exe` binary.
  * Fully portable: extract anywhere (Desktop, external drive, portable media), launch immediately, and delete the directory to remove. Zero registry writes, zero system dependencies, and zero admin rights needed.
* **Future Distribution (Store Only):**
  * Any future distribution beyond standalone `.zip` archives will be handled exclusively via the Microsoft Store / Windows Store (packaged MSIX) to provide verified cryptographic reputation and sandboxed background updates without ever maintaining separate setup wizards.
