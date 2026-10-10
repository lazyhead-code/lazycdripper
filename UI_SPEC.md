# Lazy CD Ripper — UI Design Specification & Architecture

> **Design Philosophy:** Boutique High-End Audio Craft  
> Inspired by the precision engineering and warm visual warmth of iconic audio equipment (McIntosh, Nagra, Braun, vintage Marantz) combined with modern minimalist typography and Apple/Google-level attention to detail.

---

## 1. Visual Language & Aesthetics

### 1.1 Palette & Materiality
* **Chassis Background & Ambient Texture:** Deep matte obsidian `#0D0D10` with subtle ambient radial glow and dark vignette. On the main console deck, the brand logo (`logo.jpg`) provides subtle audio equipment texture. During active ripping, the backdrop dynamically bursts into the album's high-resolution cover artwork, reverting back to the brand logo upon completion.
* **Surface Panels (Faceplate):** Translucent charcoal `#16161B` with subtle warm brushed-aluminum border (`1px solid rgba(255, 255, 255, 0.07)`).
* **Accent / Vacuum Tube Amber:** `#FF9E3B` (glow), `#FFAE57` (hover), `#E08528` (pressed).
* **Primary Text:** Warm parchment `#F2F1EC` (high contrast, non-fatiguing).
* **Secondary / Caption Text:** Muted silver/warm zinc `#8E8D96`.
* **Subtle Highlights:** Warm brass hairline `#C99700` (low opacity) and vintage green audit badge `#2ECC71`.

### 1.2 Typography & Spacing
* **Header / Brand:** Clean geometric sans-serif (Inter, Segoe UI, SF Pro Display), medium weight, letter-spacing +0.5px.
* **Manifesto / Body:** Generous line-height (1.6), elegant typography, non-cluttered reading width.
* **Telemetry / Track Numbers:** Monospace digits (Segoe UI / Consolas) with zero-padding (`01`, `02`).
* **Breathing Room:** Minimum 24px–32px outer padding. Zero cramming, zero utilitarian spreadsheet vibes.

### 1.3 Precision Rendering & High-DPI
* **Supersampled Vector Platter:** The CD disc platter and jewel-case preview render at $\ge 2\times$ supersampling with `setDevicePixelRatio` to guarantee razor-sharp typography (`COMPACT DISC DIGITAL AUDIO`, `RED BOOK • 44.1 kHz / 16-BIT PCM`) without ClearType subpixel smearing or bilinear resampling blur on Windows displays ($100\%$, $125\%$, $150\%$, $200\%$).
* **Floating Minimalist Scrollbars:** Vertical and horizontal scrollbars are inset by $14\text{px}$ as floating pill handles over transparent tracks, preventing square corner clipping across $12\text{px}$ rounded chassis corners.

---

## 2. Screen States & User Journey
 
### 2.1 Single Unified Console (No Page Toggling)
The application operates on a single unified master console:
* **No "Manifesto" page or tab:** All controls and master views live seamlessly on one screen.
* **Standby States (Clean Single-Point-of-Truth Status):**
  - **3-Tier Card Typography Rhythm:** Every state maintains the exact same 3-tier visual hierarchy:
    - *Tier 1 (Orange Eyebrow, 11px uppercase bold, `#FF9E3B`, letter-spacing 1.5px):* `OPTICAL DRIVE` (no drive) / `OPTICAL DRIVE READY` (disc tray empty) / `ARTIST NAME` (disc resolved).
    - *Tier 2 (Primary Title, 20px bold, `#F2F1EC`):* `No Optical Drive Detected` / `Insert audio CD` / `Fetching Metadata...` / `<Album Title>`.
    - *Tier 3 (Sub-telemetry, 11px medium, `#72717E`):* `Connect a USB optical drive to get started` / `[D:] <Model> ready` / `◌ Querying MusicBrainz & Cover Art Archive...` / `<Year> • <Tracks> • <Duration>`.
  - **Left Deck (Media & Controls — Integrated Hi-Fi Rack):**
    - Fixed 280px hardware column width (non-stretching).
    - **Integrated Brand Faceplate Plaque:** Architectural typography `LAZY CD RIPPER` (16px, bold 800, `#FF9E3B`, letter-spacing 2px) and audiophile manifesto `AN ALBUM IS AN EXPERIENCE, NOT A STREAM` (9px, 600, `#727180`, letter-spacing 1.2px) seated directly atop the rack. Eliminates horizontal top-bar overhead to reclaim ~56px of vertical space.
    - Machined circular anodized aluminum CD platter with concentric grooves and amber spindle diode (`TRAY READY • NO DISC`) / Jewel-case frame.
    - Master Rip Push Button: Constant label `"Rip to FLAC + AAC"`. Dimmed/grayed out in standby or during background queries; illuminates into radiant warm amber/orange glow when disc is loaded and ready.
    - Engineering policy note: Dual rip FLAC + AAC specification.
  - **Right Deck (Master Recording Roster):**
    - Metadata Header: Ultra-clean single point-of-truth card communicating clear hardware and media status, horizontally aligned with the brand faceplate on the left deck.
    - Track Table: Clean 4-column table (`#`, `Title`, `Artist`, `Time`), expanding to full vertical height to display 12–16 tracks at standard window size without scrolling.
* **Disc Detection & Query State (In-Flight Hardware Lock):**
  - Instant hardware TOC read (<10ms) immediately populates physical tracks in the table.
  - Header updates to `Fetching Metadata...` with an illuminated amber status badge (`◌  Querying MusicBrainz & Cover Art Archive...`).
  - Master Rip Button remains inactive in standby (grayed out) to prevent premature rips before metadata resolution.
* **Loaded State (Audio CD Metadata Resolved):**
  - Media chamber displays high-resolution cover art inside the jewel-case frame (with gentle 8px rounded corners and 1:1 auto-crop).
  - Metadata header updates with Artist tag (`#FF9E3B`), Album Title (`#F2F1EC`), and specs (Year • Tracks • Duration • Genre).
  - Provenance badge clearly communicates source: `Metadata: MusicBrainz • Artwork: Cover Art Archive` (or `Source: Optical CD TOC (Unindexed)` in offline mode).
  - Track Table smoothly populates with track numbers, titles, artists, and durations.
  - Master Rip Button lights up in rich vacuum tube amber (`Rip to FLAC + AAC`).
  - Clicking "Rip to FLAC + AAC" prompts the user for the destination directory on demand.

### 2.2 Active Ripping (Analog Deck)
* Switches to the Analog Ripping Deck during execution:
  - Dual precision progress bars (`Track` and `Album`).
  - Real-time telemetry indicators.
  - Rotating nostalgic music memories ticker.
* Upon completion, displays the Completion Audit Dialog and returns cleanly to the Master Console.

---

## 3. Component Hierarchy

```
MainWindow
├── BackgroundBackdropWidget (Ambient logo.jpg texture + dark radial vignette)
└── MainStack (QStackedWidget)
    ├── MasterConsoleDeck (QHBoxLayout)
    │   ├── LeftDeck (280px Fixed Width Integrated Hi-Fi Rack)
    │   │   ├── BrandFaceplatePlaque ("LAZY CD RIPPER" + "AN ALBUM IS AN EXPERIENCE, NOT A STREAM")
    │   │   ├── ArtworkCardWidget (Machined Platter / Jewel Case)
    │   │   ├── StretchSpacer
    │   │   ├── PrimaryRipButton ("Rip to FLAC + AAC")
    │   │   └── PolicyContainer
    │   │       ├── EngineeringPolicyNote ("Dual rip: [FLAC Master] + [AAC Mobile @ 256k]")
    │   │       └── ChassisVersionLabel ("v0.9.0 • Peace... Like a River • Credits" clickable laser-etched serial plate opening CreditsDialog)
    │   └── RightDeck (Master Recording Roster)
    │       ├── MetadataHeaderCard (Unified status: No Drive -> Insert audio CD -> Fetching Metadata -> Album Title)
    │       └── TrackTableWidget (4 Columns: #, Title, Artist, Time; borderless rows, full height)
    └── RippingViewWidget (Analog optical transport / dual progress meters)
```

---

## 4. Completed Design Highlights & Polish
* **Metadata & Artwork Provenance / Source Transparency (Completed):**
  - Provenance badge seamlessly displays source origins (`Metadata: MusicBrainz • Artwork: Cover Art Archive`).
  - Heuristic priority ranking automatically selects the canonical Release Group front cover without user configuration.
* **Machined Anodized Platter:** High-DPI supersampled raster/vector disc with laser spiral tracks, amber LED spindle, and Red Book engraved branding.

