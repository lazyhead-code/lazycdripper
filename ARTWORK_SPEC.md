# Lazy CD Ripper — Branding & Artwork Specifications

This document defines the visual identity, generative prompts, and design specifications for all brand assets, promotional artwork, and application icons used in **Lazy CD Ripper**.

---

## 1. Visual Identity & Brand Concept

* **Brand Philosophy:** High-fidelity audio craft with zero fuss. Built for audiophiles who appreciate physical CD media, premium analog hardware, and modern digital convenience without menu bloat.
* **Hardware Emblem:** A custom circular audiophile hardware medallion uniting physical music mediums and boutique electronics:
  * **The Compact Disc (CD):** Vivid iridescent rainbow refraction and precision spindle hub.
  * **The Vacuum Tube (Valve):** Warm, amber thermionic glow and illuminated filament.
  * **The Vinyl Record:** Concentric micro-grooves and satin vinyl sheen.
* **Aesthetic Palette:** Deep obsidian (`#0A0A0D`), warm vacuum tube amber (`#FF9E3B`), brushed gunmetal/titanium, and analog VU meter parchment.

---

## 2. Master Artwork & App Background (`assets/images/logo.jpg`)

* **Dimensions:** 1024 × 1024 px.
* **Usage:** Application ambient chassis background (`BackgroundBackdropWidget`), GitHub repository hero section, and release banners.

### Generative Prompt

```text
A detailed, high-quality, cinematic photograph of a custom 3D metallic emblem resting on a dark workbench inside a vintage, gritty analog audio studio.

STYLE: A realistic, tactile 35mm photo with rich contrast, subtle film grain, and natural warm ambient lighting. The scene looks physically real, with tangible textures—weathered metal, glowing glass, braided cables, and worn workbench surfaces. Square 1:1 format.

MAIN SUBJECT (CENTRAL EMBLEM):
A large, heavy circular metallic casing/medallion sitting upright on the workbench:
- LEFT HALF: Features a standard-sized Compact Disc (CD) showing a vibrant, natural iridescent rainbow reflection. The circular hub at the exact center of this CD has sharp, perfectly circular text printed in a curve: "LAZY CD RIPPER" along the circular hub path.
- TOP-RIGHT SEGMENT: A warmly glowing orange vacuum tube / valve (amber audiophile tube glow, illuminated filament) nestled neatly into an angled cutout recess.
- BOTTOM-RIGHT SEGMENT: Deep black vinyl record grooves with realistic sheen and fine concentric micro-ridges.
- OUTER BEZEL: Thick, distressed brushed gunmetal and titanium circular rim with precision hex screws and fasteners.

TEXT & LOGO (TOP OF FRAME):
Directly above the emblem, centered, is the title "LAZY CD RIPPER". It is rendered in a bold, heavily textured, off-white, distressed vintage block font standing out against the dark, moody background.

BACKGROUND:
Cluttered, richly detailed analog audio studio equipment with a large illuminated analog VU meter with red needle and "VB" insignia on the left, vintage knobs, audio dials, audio cables, and warm glowing vacuum tubes on rack units.
```

---

## 3. README Hero Banner (`assets/images/banner.jpg`)

* **Dimensions:** 1024 × 571 px (16:9 widescreen format).
* **Usage:** GitHub repository header banner displayed at the top of `README.md`.

### Generative Prompt

```text
A detailed, high-quality, cinematic photograph of a custom 3D metallic emblem and tech accessories resting on a cluttered, weathered dark wooden workbench inside a vintage, gritty analog audio studio. 

STYLE: A realistic, tactile 35mm photo with rich contrast, subtle film grain, and natural, slightly warm ambient lighting. The scene must look physically real, with tangible textures—weathered metal, natural plastic, braided cables, worn wood surfaces. Landscape format (16:9 widescreen aspect ratio).

MAIN SUBJECT (CENTRAL EMBLEM): 
A large, heavy, circular metallic casing or shield (roughly 40% of the frame) sits upright on the wooden workbench, angled slightly to the left to show its depth. The thick, outer metallic ring of the casing has a heavily distressed, aged look with natural scratches, scuffs, and perfectly circular industrial rivets and fasteners. 
- LEFT HALF: Features a standard-sized, semi-exposed Compact Disc (CD) showing a vibrant, natural iridescent rainbow reflection. The circular hub at the exact center of this CD must show sharp, tiny, perfectly circular text printed twice in a curve: "LAZY CD RIPPER" running along both the top and bottom of the small circular path. The text must be crisp, readable, and without distortion.
- TOP-RIGHT QUADRANT: A 3D metallic and fur relief of a rock-and-roll sloth, wearing sunglasses and a leather jacket, lounge-resting on an integrated shelf and making a "sign of the horns" hand gesture (\m/). 
- BOTTOM-RIGHT QUADRANT: Behind/underneath the overlapping layers of the sloth's metal platform and the CD's central edge, there is a visible quarter of a dark, circular speaker driver and grille. The top-left of the speaker is completely obscured, making it look as though it is nested beneath the other parts. Only its dark, textured cone, its outer ribbed surround, and its circular metal frame with tiny mounting screws are visible on the bottom-right. No other plates, badging, or text appear on the right half.

TEXT & LOGO (TOP OF FRAME): 
Directly above the emblem, centered, is the title "LAZY CD RIPPER". It is rendered in a bold, heavily textured, off-white, distressed, vintage block font that looks naturally hand-painted or aged, standing out against the dark, out-of-focus background.

FOREGROUND & ACCESSORIES: 
- BOTTOM RIGHT: A modern, sleek Android smartphone (distinctly non-Samsung, with uniform thin bezels and a centered tiny punch-hole front camera) lies flat on its back, angled toward the camera. A braided USB-C cable is clearly plugged into its bottom port, with the cable snaking naturally across the workbench toward the left. The phone screen is face-up, softly showing a dark Android lock screen with a digital clock and subtle UI elements, catching natural reflections.
- BOTTOM LEFT: Dual heavy-duty, metallic 1/4-inch audio jack connectors attached to braided cables lie loosely on the workbench, leading toward the gear on the left. 
- MIDDLE RIGHT: A slightly messy stack of clear, plastic CD jewel cases sits behind/beside the smartphone, showing natural plastic glints and scratches.

BACKGROUND: 
The background is cluttered, richly detailed, and slightly out of focus (natural depth of field) with aged, heavy-duty analog studio equipment, featuring a large illuminated VU meter with red needles and a "VB" logo on the left, an array of vintage dials, knobs, PEAK/SIGNAL indicators, and vents on metallic rack-mounted units.

CAMERA & LIGHTING: 
Shot at a natural eye-level perspective from a workbench viewpoint. Warm, natural studio light catches the edges of the metallic emblem, the iridescence of the CD, the phone’s glass, and the grit of the worn surfaces. Shadows are deep, creating a tangible 3D quality without looking artificial or CGI. No text distortion, glitches, or AI artifacts.
```

---

## 4. Application Icon Specification (`icon.png` & `logo.ico`)

### Audiophile Emblem Design

Desktop application icons are rendered across a wide range of compact display sizes:
* **Windows Taskbar:** 24 × 24, 32 × 32, 48 × 48 px.
* **Windows Explorer (Tile / List / Small Icon):** 16 × 16, 32 × 32 px.
* **Desktop & Start Menu:** 48 × 48, 64 × 64, 128 × 128, 256 × 256 px.

The official application icon features the clean, tactile audiophile hardware medallion:

1. **Outer Bezel & Framing:**
   * Sleek brushed gunmetal / titanium circular rim with precision hex screws.
   * Smooth anti-aliased transparency in the four corners (`RGBA` alpha masking) ensuring seamless rendering on Windows taskbars, Start menu tiles, and dark/light themes.
2. **Left Half (The Compact Disc):**
   * Luminous, iridescent Compact Disc (CD) with realistic rainbow holographic refraction and central metallic spindle hub.
3. **Top-Right Quadrant (The Vacuum Tube):**
   * Warmly glowing orange vacuum tube / valve with illuminated amber filament.
4. **Bottom-Right Quadrant (The Vinyl Record):**
   * Deep black vinyl record grooves with realistic sheen and concentric micro-ridges.
5. **Zero Text & Zero Clutter:**
   * Pure iconographic symbol without text or extraneous labels for maximum visual punch.

### Generative Prompt for Icon

```text
A professional, high-contrast Windows application desktop icon centered on an isolated transparent background. Square 1:1 framing.

SUBJECT: A circular audiophile hardware motif framed by a sleek brushed titanium and gunmetal circular rim with precision screws:
- LEFT HALF: A luminous, iridescent Compact Disc (CD) with realistic rainbow holographic refraction and a metallic central spindle hub.
- TOP RIGHT SEGMENT: A warmly glowing orange vacuum tube / valve (amber audiophile tube glow, illuminated filament).
- BOTTOM RIGHT SEGMENT: Deep black vinyl record grooves with realistic sheen and concentric micro-ridges.
- STYLE: Clean silhouette, sharp details, tactile 3D metallic textures, punchy contrast, transparent corners outside the circular bezel. NO text or labels inside the icon (pure iconographic symbol).
```

### Icon Asset Delivery Formats

| File | Target Resolutions | Format | Purpose |
| :--- | :--- | :--- | :--- |
| `assets/images/icon.png` | 256 × 256 px | PNG (32-bit RGBA, transparent corners) | High-DPI UI, Linux packaging, web previews |
| `assets/images/logo.ico` | 256, 128, 64, 48, 32, 24, 16 px | Windows Multi-Resolution `.ico` (32-bit RGBA) | Windows executable icon, taskbar, Explorer |

---

## 5. Building & Updating Icon Binaries

When a new master icon source image is generated (e.g. `icon_master.png` at 1024 × 1024), compile the full multi-resolution icon set using Python and Pillow:

```python
from PIL import Image

# Load master 1024x1024 transparent RGBA image
master = Image.open("icon_master.png").convert("RGBA")

# Generate 256x256 PNG
master.resize((256, 256), Image.Resampling.LANCZOS).save("assets/images/icon.png", format="PNG")

# Generate Windows multi-resolution .ico containing all standard sizes
icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
master.save("assets/images/logo.ico", format="ICO", sizes=icon_sizes)
```
