# Lazy CD Ripper 💿

<p align="center">
  <img src="assets/images/screenshot.png" alt="Lazy CD Ripper Interface" width="640" />
</p>

---

**Download the latest portable release archive from** **[GitHub Releases](https://github.com/lazyhead-code/lazycdripper/releases)**.

---

The audio CD ripper for Windows 11 with zero settings. Defaults are great. Just press the button!
- **Both Formats in One Pass:** Never choose between archival quality and mobile convenience. You always get both:
  - **FLAC Lossless (Perfect CD copy):** Bit-perfect original CD (16-bit / 44.1 kHz) master with Level 8 archival compression and MD5 stream verification.
  - **MP3 Lossy (Compressed but still great):** Audiophile LAME Constant Bitrate (320 kbps CBR, `-q 0` in `.mp3`), 100% patent-free worldwide, compatible with every vehicle, smartphone, and stereo in existence.
- **Automatic Metadata & High-Res Artwork:** MusicBrainz disc ID lookup + canonical front covers from the Cover Art Archive embedded in every track, plus a companion `cover.jpg` for media servers.
- **Sensible Organization:** Clean, zero-padded filenames in dedicated folders (`Artist - Album (Year) [FLAC]/` and `[MP3]/`).

---

## Why This Exists

> We've gained so much with music streaming services.  
> We've lost so much as well.  
> 
> Buying a music CD and listening to the whole album brings back the magic.  
> 
> We don't have CD drives in cars and laptops anymore. But we can rip music for ourselves (all it takes is an external drive), copy it to our phone, and have the exact same experience.  
> 
> This application is opinionated AF, but it rips to virtually the best options: high-quality MP3 (320 kbps CBR) and FLAC. Why MP3 instead of other lossy formats? Because MP3 is 100% patent-free worldwide, universally supported by every car, stereo, and device on Earth, and at 320 kbps CBR it is perceptually transparent. Why FLAC? Because it's a picture-perfect copy of your CD—highest possible quality. We may not really hear the difference much, but I'm glad to surrender to an illusion :)  
> 
> Have fun and welcome back to the magical world of music!  
> 
> Yours truly,  
> **Lazyhead Code 💿**

---

## Release Notes

### v0.9.4 — *"Peace... Like a River"* (October 2026)
- **Standalone Dedicated Encoders (FLAC + MP3):** Replaced monolithic FFmpeg dependency with high-performance standalone `flac.exe` and `lame.exe` (LAME 4.0 q4-patched with companion DLLs), switching lossy compression to patent-free MP3 CBR 320 kbps with zero external codecs or system dependencies required.
- **Refined Windows Store Mascot Icon:** Updated store app icons (`store_icon.jpg` and `store_icon_tight.jpg`) with sleek dark-tinted aviator lenses, realistic glass depth, and warm vacuum-tube amber lighting matching the completion medallion palette.
- **Ergonomic Capsule Progress Meters & Scrollbars:** Implemented mathematically seamless rounded capsule geometry across all progress bars and scrollbars (`border-radius: 10px` on progress container, `9px` on chunk; `12px` wide scrollbar with `6px` radius on track and handle).
- **Ripping View Decompression & 960px Wide Containers:** Expanded active ripping containers to 960px with relaxed 20px progress bars and 22px inter-meter separation, ensuring nostalgic quotes fit comfortably without multi-line wrapping.
- **Visual Polish & Layout Realignment:** Aligned completion output folder links and diagnostic bullet points to the left, matched overall progress labels to crisp white `#F3F4F6`, and fixed Credits dialog vertical height clamping to prevent text clipping.

### v0.9.3 — *"Peace... Like a River"* (October 2026)
- **Human-Friendly Quality Clarifications:** Clarified codec selections for everyday audiophiles—FLAC Lossless labeled as *"Perfect CD copy"* and MP3 Lossy as *"Compressed but still great"*—while preserving exact encoder flags and bitrates for those who care.
- **Central-Axis Alignment & Layout Clamping:** Centered all active ripping and completion screens along a strict vertical axis (`Qt.AlignCenter`), eliminated element drift when expanding or maximizing the window, and guaranteed custom window dimensions persist seamlessly across all screen transitions.
- **Tactile 3D Mascot Medallions:** Added crafted 3D pewter and gunmetal rock sloth medallions with a knurled bezel for completion states (Happy thumbs-up for bit-perfect/recovered rips, and Sad thumbs-down for scratched disc surface damage), rendered at 0.96 scale factor to prevent edge clipping.
- **Session-Wide Error Telemetry:** Unified real-time sector error and retry tracking across individual tracks and final verdict summaries with three-state LED status signaling (Pristine Green, Amber Warning, Crimson Error).
- **Windows Store Mascot Icon Assets:** Designed high-contrast 1024×1024 metallic rock sloth mascot icon (`store_icon_tight.jpg`) featuring holographic rainbow CD reflections across his sunglasses, optimized for high visibility at small store tile sizes.
- **Design System Style Guide:** Published comprehensive UI specification and layout rules in `STYLE_GUIDE.md`.

### v0.9.2 — *"Peace... Like a River"* (October 2026)
- **Real-Time Drive Speed:** Wired up dynamic sector-rate speed measurement (75 sectors/sec) in the Windows extraction engine, actively signaling drive read speed (`Reading disc  •  14.2x`).
- **Telemetry Cleanup:** Removed obsolete 1990s "Jitter Align" telemetry badge in favor of clean, reassuring sector error and retry monitoring.
- **Fidelity Terminology:** Simplified all "Red Book Audio" jargon to clear, everyday audiophile fidelity (`AUDIO CD • 16-BIT / 44.1 kHz`).
- **Native In-Screen Completion:** Replaced the floating popup dialog with an elegant in-screen completion summary directly inside the ripping deck, displaying the bit-perfect verdict, defect diagnostics (if any), library folder paths with sizes, and single-click folder access.
- **Windows Subprocess Unicode Fix:** Explicitly set UTF-8 stream encoding and fallback error replacement on all encoder and drive subprocess readers, preventing Windows CP1252 charmap decode crashes on non-ASCII metadata.

### v0.9.1 — *"Peace... Like a River (Update)"* (October 2026)
- **Cover Art Gateway Resilience:** Added direct `/front` endpoint fallback and public high-res artwork resolution via Apple iTunes and Deezer when Internet Archive / Cover Art Archive experiences `502 Bad Gateway` outages.
- **UI Typography Polish:** Fixed clipping and wrapping of nostalgic memory vignettes in the ripping progress ticker.

### v0.9.0 — *"Peace... Like a River"* (October 2026)
> *This is the initial release of Lazy CD Ripper. Opinionated AF way to extract music from your CDs. Zero choices to make because the defaults are great! It works, I've tested it on quite a bunch of my music discs already. I will use it for some more time (and will share with friends) before releasing 1.0. Some minor polishing is likely to be done.*

---

## Architecture Overview

1. **Hardware & TOC:** Direct Win32 `IOCTL_CDROM_READ_TOC` and SCSI storage property queries.
2. **Ripper Engine:** Native Win32 sector-by-sector CDDA extraction with hardware buffer alignment, gap padding, and retry recovery (`windows.py`).
3. **Metadata Client:** MusicBrainz WS2 JSON API + Cover Art Archive image ranking.
4. **Encoding Pipeline:** Parallel lossless FLAC and LAME MP3 (320 kbps CBR) encoding via standalone `flac.exe` and `lame.exe` binaries (< 2.5 MB total footprint, executed silently via `CREATE_NO_WINDOW`).
5. **Tagging:** Mutagen handles Vorbis comment blocks and ID3v2.3 tags with high-res cover art embedding.

---

## Acknowledgments & Credits

Lazy CD Ripper is proudly built on open-source technologies:
- **FLAC (Xiph.org)** & **LAME** — Official standalone audio encoding engines (FLAC & MP3)
- **Mutagen** — Audio metadata tagger & cover art embedder
- **Qt 6 / PySide6** — Hi-DPI desktop GUI framework
- **MusicBrainz WS2** — Global acoustic CD metadata discovery via `musicbrainzngs`
- **Pillow** — Digital cover art optimization

Crafted in pair programming with **Antigravity** (Google DeepMind).

For detailed third-party software licenses and source links, see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

---

## License

GNU General Public License v3.0 (GPLv3). Copyright (c) 2026 Lazyhead Code <lazyhead@fastmail.com>.  
See [LICENSE](LICENSE) for full project license terms.

---

<p align="center">
  <img src="assets/images/banner.jpg" alt="Lazy CD Ripper" width="850" />
</p>
