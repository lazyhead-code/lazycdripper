# Lazy CD Ripper — UI Style Guide & Design System

> **Design Philosophy:** Boutique High-End Audio Craft  
> Inspired by the precision engineering, tactile warmth, and understated luxury of iconic hi-fi audio equipment (McIntosh, Nagra, Braun, vintage Marantz) combined with clean modern typography and Apple/Google-level layout discipline.

---

## 1. Core Visual Tokens & Palette

### 1.1 Color Palette
| Token | Hex | Usage |
| :--- | :--- | :--- |
| **Chassis Obsidian** | `#0D0D10` / `#121214` | Main window background, letterbox margin, deep dark canvas |
| **Faceplate Charcoal** | `#16161B` / `#1A1A22` | Component cards, telemetry pills, deck panels |
| **Panel Border** | `#2C2C34` / `rgba(255, 255, 255, 0.08)` | Tactile brushed metal seams and panel edges |
| **Vacuum Tube Amber** | `#FF9E3B` | Primary highlights, glowing brand accents, active buttons |
| **Amber Hover / Glow** | `#FFAE5B` / `#FFAE57` | Button hover state, radiant tube filaments |
| **Status Green (Pristine)** | `#10B981` | 100% bit-perfect integrity, zero read errors, nominal state |
| **Status Amber (Recovered)**| `#F59E0B` | Multi-pass sector retries, recovered with zero data loss |
| **Status Crimson (Damaged)**| `#EF4444` | Unrecoverable sector read skips, surface damage, failures |
| **Primary Text** | `#F2F1EC` / `#F3F4F6` | High-contrast, non-fatiguing warm white parchment |
| **Secondary Text** | `#9CA3AF` / `#8E8D96` | Technical subtitles, secondary metadata, track artists |
| **Muted Metadata** | `#727180` / `#72717E` | Audiophile manifesto, serial labels, inactive captions |

### 1.2 Status LED Indicators
- **Form:** 15px/18px circular indicators with 1.5px anti-aliasing edge padding (rendering at 12–15px interior radius to prevent square bounding-box clipping).
- **Colors:** Green (`#10B981`), Amber (`#F59E0B`), Crimson (`#EF4444`).
- **Placement:** Symmetrically placed directly adjacent to centered headline text rows with 8px spacing.

---

## 2. Central-Axis Symmetry ("Align Vertical" Rules)

On the active ripping screen and both completion screens (success and failure), **all UI elements align strictly along a unified central vertical axis (`Qt.AlignCenter`)**. Asymmetric left-aligned text blocks floating against centered banners are strictly prohibited.

```text
               ┌─────────────────────────────────────┐
               │     AUDIO CD • 16-BIT / 44.1 kHz    │  <-- Centered spec badge
               │                                     │
               │            [ 200×200 ]              │  <-- Centered emblem (disc / mascot)
               │          Optical / Mascot           │
               │                                     │
               │       ● Surface Damage Detected     │  <-- Centered LED + headline
               │   • Tracks Extracted: 3/4 (2m 57s)  │
               │   • Sector Retries: 42 recovered    │  <-- Centered summary bullets
               │   • Unrecoverable Skips: 20 sector  │
               └─────────────────────────────────────┘
                                  │
                                16px (Fixed spacing)
                                  │
               ┌─────────────────────────────────────┐
               │    📁 [FLAC] - Perfect CD copy      │  <-- Centered sister folder
               │ 📁 [MP3] - Compressed but still great│  <-- Centered sister folder
               └─────────────────────────────────────┘
                                  │
                                16px (Fixed spacing)
                                  │
                       [ Open Folder ]   [ Done ]       <-- Centered action buttons
```

### 2.1 Central Axis Checklist
- [x] **Hardware Spec Top Badge (`spec_badge`):** Centered inside `visual_frame`.
- [x] **Visual Emblem (`emblem_container`):** Centered (200×200 transport disc or sloth mascot).
- [x] **Headline Status Row (`headline_row`):** Centered with LED indicator.
- [x] **Summary / Subtitle (`status_sub`):** Centered horizontally (`Qt.AlignCenter`) across all lines.
- [x] **Phase Indicators (`track_label`):** Centered above the track progress bar (`Qt.AlignCenter`).
- [x] **Album Progress Label (`overall_label`):** Centered above the overall progress bar (`Qt.AlignCenter`).
- [x] **Progress Bars (`track_bar`, `overall_bar`):** Centered with percentage text centered inside the bar.
- [x] **Telemetry Pills (`badge_retries`, `badge_errors`):** Centered in horizontal row.
- [x] **Memories Ticker Card (`memory_card`):** Centered text with italicized warm amber styling.
- [x] **Sister Directories Card (`output_card`):** Inner layout centered; both FLAC and MP3 labels set to `Qt.AlignCenter`.
- [x] **Action Buttons (`comp_btn_row`):** Centered horizontally side-by-side.

---

## 3. Layout Clamping & Anti-Drift Spacing System

### 3.1 The "Stick Together" Principle
When the user enlarges or maximizes the application window, **UI elements must stick together as a tight, cohesive hardware deck in the center of the screen**. Distances between progress bars, labels, and badges must NEVER stretch or expand into empty space.

### 3.2 Sizing & Spacing Rhythm (Active Ripping Screen)
| Element | Height | Spacing to Next Element | Policy / Behavior |
| :--- | :--- | :--- | :--- |
| **`track_label`** | 18px | 8px | Fixed height, `Qt.AlignCenter` |
| **`track_bar`** | 20px | 22px | Fixed height analog progress meter |
| **`overall_label`** | 18px | 8px | Fixed height, `Qt.AlignCenter`, `#F3F4F6` |
| **`overall_bar`** | 20px | 18px | Fixed height analog progress meter |
| **`telemetry_row`** | 24px | 18px | Fixed height badges (`Retries: N`, `Errors: N`) |
| **`memory_card`** | 72px | — | Fixed height preview card |
| **`active_container`** | **246px** | — | **`setFixedHeight(246)`**, `QSizePolicy.Fixed` vertical |
| **`visual_frame`** | ~340px | 16px | `QSizePolicy.Fixed` vertical |
| **`main_layout`** | — | 16px | `Qt.AlignCenter`, centered in window |

### 3.3 Sizing & Spacing Rhythm (Completion / Succession Screen)
| Element | Height | Spacing to Next Element | Policy / Behavior |
| :--- | :--- | :--- | :--- |
| **`visual_frame`** | ~340–380px | 16px | `QSizePolicy.Fixed` vertical |
| **`output_card`** | ~80px | 16px | `Qt.AlignCenter`, padding 16px |
| **`comp_btn_row`** | ~38px | — | Fixed height buttons (`Open Rip Folder`, `Done`) |
| **`completion_container`**| ~134px | — | `QSizePolicy.Fixed` vertical |

---

## 4. Window Geometry & Transition Sizing Discipline

1. **Default Startup Size:** Exactly **1020 × 700 px**.
2. **Hard Minimum Size Limit:** Exactly **1020 × 700 px** (`setMinimumSize(1020, 700)`). The window cannot be resized smaller than this to prevent clipping the 280px left hardware deck, 200px mascots, or track rosters.
3. **Window Size Preservation Across Screen Transitions:**
   The window must **NEVER resize itself back down to default dimensions** when navigating between screens.
   $$\text{Main Deck Screen} \;\longleftrightarrow\; \text{Active Ripping Screen} \;\longleftrightarrow\; \text{Completion Screen (Success / Failure)}$$
   Whatever custom dimensions the user sets (e.g. 1400×900, 1080p, or maximized) must be **strictly preserved across all page transitions**.

---

## 5. Mascot & Visual Emblem System

### 5.1 Center Visual Emblems (200 × 200 px)
- **Active Ripping:** Animated vector/raster optical transport disc with rotating laser pickup sled, iridescent rainbow sheen, and LED spindle.
- **Symmetrical Vertical Spacing:** Exactly 8px above the emblem (to spec badge) and 8px below the emblem (to headline row).

### 5.2 Completion Rock Sloth Medallions
- **Dimensions:** 200 × 200 px framed in precision-machined knurled dark gunmetal and titanium bezel with hex bolts.
- **Centering:** Exact geometric center at $(x=50\%, y=50\%)$ on solid pitch-black background (`#000000`).
- **Scale Factor:** Rendered with a **0.96 scale factor** inside the 200×200 container to guarantee zero outer bolt or bezel clipping.
- **Mood Variants:**
  - **Happy Sloth (Success / Pristine / Recovered):** Confident smile, dark sunglasses, leather motorcycle jacket, thumbs-up claw gesture.
  - **Sad Sloth (Degraded / Damaged / Failed):** Visibly sorrowful frown, dark sunglasses tipped down looking up with sympathetic eyes, thumbs-down claw gesture.

### 5.3 Windows Store App Icon (`assets/images/store_icon_tight.jpg`)
- **Composition:** Extreme close-up bust focusing tightly on the heavy metal sloth mascot's face and upper torso to maximize recognition at small tile sizes (48×48 to 150×150 px).
- **Hero Features:**
  - Sculpted cast pewter and brushed silver metal fur with polished chrome highlights.
  - Dark aviator rock sunglasses with radiant, iridescent rainbow Compact Disc holographic spectral reflections mirrored across both lenses.
  - Metallic claw hand holding a brilliant rainbow holographic Compact Disc right next to his rock smirk.
  - Classic vintage motorcycle leather jacket with metallic studs and warm subtle vacuum-tube amber rim lighting (`#FF9E3B`).
  - Pure solid black background (`#000000`) for seamless app icon masking and store packaging.
- **File Asset Paths:**
  - Tight Close-up (Primary Store Icon): [`assets/images/store_icon_tight.jpg`](file:///home/nduhovnijs/projects/lazycdripper/assets/images/store_icon_tight.jpg)
  - Full Bust Portrait (Alternative Asset): [`assets/images/store_icon.jpg`](file:///home/nduhovnijs/projects/lazycdripper/assets/images/store_icon.jpg)

---

## 6. Audiophile Terminology Standards

Plain English for regular human clarity combined with precision technical parameters for audiophiles who care:

| Audio Format | Full UI Title | Subtitle / Specification Wording |
| :--- | :--- | :--- |
| **FLAC Lossless** | **`FLAC LOSSLESS (Perfect CD copy)`** | Audio CD 16-bit / 44.1 kHz bit-perfect master.<br>Archival compression (Level 8) with MD5 stream verify. |
| **MP3 Lossy** | **`MP3 LOSSY (Compressed but still great)`** | LAME Constant Bitrate (CBR 320 kbps, `-q:a 0`).<br>100% patent-free worldwide, universal automotive and device compatibility. |

### 6.1 Output Sister Folder Naming Standard
```text
📁  Artist - Album (Year) [FLAC] - Perfect CD copy (383.7 MB)
📁  Artist - Album (Year) [MP3] - Compressed but still great (106.4 MB)
```

---

## 7. Real-Time Telemetry & Error Signaling Architecture

1. **Cumulative Session Totals in GUI:**
   - Error and retry counters in the UI (`🟢 Retries: 0`, `🟢 Errors: 0`) track cumulative totals across the entire album session.
   - If Track 3 encounters unrecoverable sector errors, the `🔴 Errors: N` badge lights up immediately and **never resets to 0** during subsequent tracks or transcoding phases.
2. **Real-Time Emission on Hardware Faults:**
   - In the hardware ripper (e.g. `windows.py`), `on_progress` is pulsed immediately on every batch fallback, single-sector retry, and sector failure so the user sees errors instantly in the progress bar.
3. **Audit Integrity:**
   - Track-level accuracy is maintained inside each `TrackRipReport` (e.g. Track 1: 0 errors; Track 3: 20 errors; Track 4: 0 errors).
   - Album-level report (`AlbumRipReport`) aggregates the true full-session statistics for final display.

