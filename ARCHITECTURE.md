# Lazy CD Ripper — Architecture Document (ARCHITECTURE.md)

## 1. High-Level Architecture Overview

Lazy CD Ripper follows a **Decoupled Engine-Presenter Architecture**. The core audio, disc, metadata, and encoding logic is completely independent of the graphical user interface. This guarantees that:
1. Core logic can be executed and tested via automated unit and integration tests without spinning up a GUI.
2. The core audio pipeline is cleanly separated from the PySide6 presentation layer, making headless automated testing, CI validation, and maintenance trivial.
3. Audio extraction, encoding, tagging, and metadata resolution operate deterministically without UI event loop coupling.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Presentation Layer (GUI)                        │
│                 PySide6 / Qt 6 (Dark Tube-Amp Theme)                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ PySide Signals / Async Worker
┌───────────────────────────────────▼────────────────────────────────────┐
│                       Pipeline Orchestrator                            │
│           (Job Coordinator, State Machine, Thread Management)          │
├───────────────────┬───────────────────┬────────────────────────────────┤
│   Disc Subsystem  │ Metadata Engine   │       Encoding Subsystem       │
│  (TOC, DiscID,    │ (MusicBrainz API, │ (WAV Buffer, FLAC/MP3 Encoders,│
│   Win32 CDDA)     │  CoverArtArchive) │  Multi-threading, Validation)  │
├───────────────────┴───────────────────┴────────────────────────────────┤
│                     Tagging & File Management                          │
│               (Mutagen Vorbis/ID3v2, Path Sanitizer)                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Subsystem Breakdown & Implementation Decisions

### 2.1 `lazycdripper.disc` (Disc & Hardware Abstraction)
* **Final Implementation:**
  * **Direct Win32 Hardware Queries:** Uses Windows `DeviceIoControl` with `IOCTL_STORAGE_QUERY_PROPERTY` for sub-millisecond drive descriptor retrieval without running external shell tools or WMI scripts.
  * **Hardware TOC Reading:** Reads exact lead-in, lead-out, and track offsets via `IOCTL_CDROM_READ_TOC` with fallback to native `.cda` volume inspection.
  * **Pure Python MusicBrainz DiscID Engine:** Calculates the 28-character URL-safe Base64 SHA-1 DiscID directly in Python (`calculate_musicbrainz_discid`).
* **Motivation:**
  * Eliminates fragile external C library dependencies (`libdiscid.dll`, `discid` C-extensions). Guarantees instantaneous, zero-install drive and track discovery on any Windows 10/11 machine.

### 2.2 `lazycdripper.metadata` (Metadata & Cover Art Engine)
* **Final Implementation:**
  * Direct JSON REST communication with MusicBrainz Web Service (WS2) and Cover Art Archive (CAA) via Python `requests`.
  * Automatic multi-tier resolution: Exact DiscID lookup -> Fuzzy TOC matching -> Automated release group & text fallback.
  * Local image caching (`~/.cache/lazycdripper/artwork/`) for responsive GUI cover presentation and seamless tagging embedding.
* **Motivation:**
  * Replaced bulky third-party wrapper libraries with targeted, resilient HTTP calls featuring rate-limit backoff (503 handling) and direct stream downloading.

### 2.3 `lazycdripper.ripper` (Extraction Engine)
* **Final Implementation:**
  * **Native Windows CDDA Ripper (`WindowsCddaRipper` - Production Default):**
    * Directly interacts with the optical drive handle via Win32 `DeviceIoControl` (`IOCTL_CDROM_RAW_READ`).
    * Reads raw 2,352-byte Red Book PCM sectors in 20-sector batches (~46 KB chunks).
    * Features sector-by-sector retry fallbacks (up to 3 re-reads per sector) and circuit-breaker aborts for disconnected drives.
    * Writes pristine 16-bit 44.1 kHz stereo PCM WAV files using Python's standard `wave` module.
  * **In-Memory Mock Ripper (`MockRipper` - Test Suite):**
    * Emulates realistic Red Book CDDA audio extraction in automated unit tests without requiring physical hardware.
* **Motivation:**
  * On modern Windows, legacy tools like `cdparanoia` are non-viable for general distribution due to legacy ASPI / Cygwin dependencies and lack of native Win32 direct sector extraction. Writing a native Win32 direct sector extraction backend in pure Python via `ctypes` delivers 100% out-of-the-box extraction with zero third-party drivers or installs.

### 2.4 `lazycdripper.encoder` (Transcoding Engine)
* **Final Implementation:**
  * Transcodes scratch WAV buffers into FLAC and MP3 using dedicated standalone CLI encoders.
  * **Encoding Parameters:**
    * **FLAC:** `flac.exe -8 --verify "<input.wav>" -o "<output.flac>"` (or `-compression_level 8 -verify` via fallback) — Lossless bit-perfect master archive.
    * **MP3:** `lame.exe -b 320 -q 0 "<input.wav>" "<output.mp3>"` (or `-b:a 320k -q:a 0` via fallback) — Constant Bitrate (CBR) 320 kbps with maximum psychoacoustic quality model (`-q 0`).
  * **Zero Console Window Execution (`CREATE_NO_WINDOW`):**
    * All encoder subprocesses on Windows are invoked with `creationflags=subprocess.CREATE_NO_WINDOW` (`0x08000000`). This completely eliminates console window flicker / black boxes, running encoders silently and invisibly in the background.
  * **Option A: Official Dedicated Standalone Binaries:**
    * Bundles official, lightweight, open-source binaries: Xiph.org `flac.exe` (~1.5 MB, BSD) and RareWares/LAME `lame.exe` (~800 KB, LGPL).
    * Total bundled binary footprint is **under 2.5 MB** (compared to ~80 MB for full FFmpeg).
    * Zero AAC or video codec code exists in either binary, guaranteeing 100% patent-free legal distribution.
* **Motivation:**
  * Dedicated standalone encoders (`flac.exe` and `lame.exe`) are the gold standard of the audiophile community (used by Exact Audio Copy and CUERipper). They drastically shrink the distributable archive size, completely insulate the project from AAC patent claims, and run with zero console flashing via `CREATE_NO_WINDOW`.

### 2.5 `lazycdripper.tagger` (Metadata & Artwork Embedding)
* **Final Implementation:**
  * Pure Python tagging via `mutagen`.
  * Writes Vorbis comment blocks and FLAC Picture block type 3 (Front Cover) to `.flac`.
  * Writes ID3v2.3 tags (`TIT2`, `TPE1`, `TPE2`, `TALB`, `TYER`, `TRCK`, `TPOS`, `TCON`, `TXXX:MusicBrainz DiscID`) and `APIC` frame (Cover Front, `image/jpeg`) to `.mp3`.
  * Emits companion `cover.jpg` directly inside the album root directory and inside each `Disc NN` subfolder for multi-disc sets.
* **Motivation:**
  * ID3v2.3 is universally recognized across Windows Explorer, Windows Media Player, car head units, Apple iOS, Android, and media servers. Manipulating tags directly in memory via `mutagen` guarantees atomic tag writes and instantaneous performance without spawning external CLI tagging tools.

### 2.6 `lazycdripper.gui` (User Interface)
* **Final Implementation:**
  * PySide6 / Qt 6 single-window console with boutique tube-amp / McIntosh dark rock aesthetic.
  * **Zero Settings / Zero Manual Selection:** No drive dropdowns or refresh buttons. Native Windows `WM_DEVICECHANGE` hotplug and background polling automatically detect optical drives, auto-lock onto whichever drive has an audio disc loaded, and seamlessly update status in the central metadata card (`No Optical Drive Detected` -> `Insert audio CD` -> `Fetching Metadata...` -> `Album Title`).
  * High-DPI supersampled raster/vector rendering for disc platter and jewel-case artwork to eliminate subpixel blur and chromatic fringing across Windows display scaling modes (100%, 125%, 150%, 200%).
  * Real-time ripping telemetry, rotating nostalgic music memory vignettes, and post-rip completion audit dialogs.

---

## 3. Data Flow & Sequence Diagram

```
User               GUI / Pipeline              Win32 CDDA Engine       MusicBrainz / CAA             Encoder / Tagger
 │                       │                            │                         │                            │
 ├─ Disc Inserted ──────►│                            │                         │                            │
 │                       ├─ Detect Disc & TOC ───────►│                         │                            │
 │                       │◄─ TOC & DiscID ────────────┤                         │                            │
 │                       │                                                      │                            │
 │                       ├─ Query DiscID ──────────────────────────────────────►│                            │
 │                       │◄─ Album Metadata & Artwork Manifest ─────────────────┤                            │
 │                       │                                                      │                            │
 │◄─ Display Metadata ───┤                                                      │                            │
 │   & Artwork Preview   │                                                      │                            │
 │                       │                                                      │                            │
 ├─ Click "Rip..." ─────►│                                                      │                            │
 │                       ├─ Extract Track to WAV ────►│                         │                            │
 │                       │◄─ Progress / Sectors ──────┤                         │                            │
 │                       │                                                                                   │
 │                       ├─ Transcode WAV -> FLAC/MP3 ──────────────────────────────────────────────────────►│
 │                       ├─ Write Tags & Embed Artwork ─────────────────────────────────────────────────────►│
 │                       │◄─ Track Completed ────────────────────────────────────────────────────────────────┤
 │                       │                                                                                   │
 │◄─ Completed! ─────────┤                                                                                   │
```

---

## 4. Testing Strategy

To maintain code reliability and eliminate regression bugs when adding features, we implement four layers of automated testing using Python's standard `unittest` framework (compatible with `pytest`):

| Test Type | Scope | How It's Executed |
| :--- | :--- | :--- |
| **Unit Tests** | Path sanitization, DiscID hashing, Vorbis/ID3v2 tag mapping, filename formatting. | Pure Python tests with standard library `unittest`, fast (< 1s), zero external dependencies. |
| **Integration Tests** | Metadata queries and cover art fetching against recorded responses (mock fixtures). | `unittest` with mocked HTTP responses simulating standard, multi-disc, and ambiguous releases. |
| **Audio Pipeline Tests** | WAV generation, FLAC/MP3 transcoding, and tag validation using test audio samples. | Synthetic 1-second WAV files generated in-memory, transcoded, and verified with `mutagen`. |
| **Mock Disc Tests** | Simulating optical drive states (no disc, audio disc, data disc, scratch error). | Mock classes implementing `MockRipper`. |
