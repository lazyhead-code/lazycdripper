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
    - Master Rip Push Button: Constant label `"Rip to FLAC + MP3"`. Dimmed/grayed out in standby or during background queries; illuminates into radiant warm amber/orange glow when disc is loaded and ready.
    - Engineering policy note: Dual rip FLAC + MP3 specification.
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
  - Master Rip Button lights up in rich vacuum tube amber (`Rip to FLAC + MP3`).
  - Clicking "Rip to FLAC + MP3" prompts the user for the destination directory on demand.

### 2.2 Active Ripping & In-Screen Completion Deck
The application transitions seamlessly in-place from the Master Console to the central Ripping View without opening detached modal dialogs:
* **Active Extraction Deck:**
  - Animated Hi-Fi optical transport disc (200×200) with spinning laser sled and spindle LED.
  - Symmetrical vertical spacing: 8px from spec badge to transport, 8px from transport to headline status row.
  - Centered phase indicator and 20px track progress bar (`track_label` + `track_bar`, 8px fixed spacing).
  - Centered album progress indicator and 20px progress bar (`overall_label` + `overall_bar`, 22px inter-meter separation).
  - Dual real-time hardware telemetry pills: `🟢 Retries: 0` and `🟢 Errors: 0`, updating cumulatively across the entire album in real time.
  - Nostalgic audio memory ticker card: 72px fixed height card rotating wholesome physical CD and music memories every 90 seconds.
  - **Layout Clamping (246px Fixed Height):** The entire active progress container is clamped to 246px with generous breathing room so that elements never stretch or drift apart when the window is enlarged or maximized.
* **In-Screen Completion Summary (Replaces Active Container on Done):**
  - Smoothly transitions in-place: stops disc animation and reveals the high-fidelity 3D metallic rock sloth mascot medallion (200×200).
  - **Audited Mood Medallions:**
    - *Happy Sloth (Thumbs Up):* Pristine bit-perfect rips and multi-pass recovered discs.
    - *Sad Sloth (Thumbs Down):* Discs with unrecoverable surface damage or read failures.
  - Centered clean headline with anti-aliased status LED (Green `#10B981`, Amber `#F59E0B`, Crimson `#EF4444`).
  - Centered multi-line summary breakdown bullets (`human_readable_summary`).
  - Output Sister Directories Card: Centered card displaying clean human-readable output folder paths:
    - `📁  Artist - Album (Year) [FLAC] - Perfect CD copy (X.X MB)`
    - `📁  Artist - Album (Year) [MP3] - Compressed but still great (Y.Y MB)`
  - Centered action buttons: `Open Rip Folder` and `Done` (returns to Master Console).

### 2.3 Style & Layout Design System Reference
For the complete technical layout tokens, vertical alignment rules, anti-drift spacing matrices, and window geometry constraints, see [STYLE_GUIDE.md](file:///home/nduhovnijs/projects/lazycdripper/STYLE_GUIDE.md).

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
    │   │   ├── PrimaryRipButton ("Rip to FLAC + MP3")
    │   │   └── PolicyContainer
    │   │       ├── EngineeringPolicyNote ("Dual rip: [FLAC Master] + [MP3 320k]")
    │   │       └── ChassisVersionLabel ("v0.9.4 • Peace... Like a River • Credits" clickable serial plate)
    │   └── RightDeck (Master Recording Roster)
    │       ├── MetadataHeaderCard (Unified status: No Drive -> Insert audio CD -> Fetching Metadata -> Album Title)
    │       └── TrackTableWidget (4 Columns: #, Title, Artist, Time; borderless rows, full height)
    └── RippingViewWidget (Analog optical transport / dual progress meters / in-screen completion deck)
        ├── VisualFrame (Spec badge, 200x200 optical disc / sloth medallion, status headline, LED, subtitle)
        ├── ActiveContainer (Clamped 246px: dual progress meters, telemetry pills, memories card)
        └── CompletionContainer (Clamped output sister directories card, action buttons)
```

---

## 4. Completed Design Highlights & Polish
* **Central-Axis Symmetrical Alignment:** All elements on the active and completion decks align to `Qt.AlignCenter` along a unified vertical axis.
* **Anti-Drift Sizing Clamping:** Elements stick together with fixed spacing when the window is enlarged or maximized.
* **Window Size Preservation:** Window dimensions are strictly preserved across all page transitions (never resets to 1020×700 on navigation).
* **Metadata & Artwork Provenance / Source Transparency:** Provenance badge displays source origins (`Metadata: MusicBrainz • Artwork: Cover Art Archive`). Canonical front covers selected via Release Group heuristic ranking.
* **Tactile Mascot Medallions:** Cast pewter and dark gunmetal 3D rock sloth mascot medallions (Happy thumbs-up and Sad thumbs-down) framed in a machined knurled bezel with 0.96 scale factor to prevent edge clipping.
* **Human-Readable Quality Terminology:** FLAC labeled as `Perfect CD copy` and MP3 labeled as `Compressed but still great`, keeping technical parameters available for audiophiles who care.


