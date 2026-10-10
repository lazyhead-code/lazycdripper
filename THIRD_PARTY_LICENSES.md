# Third-Party Software Licenses & Attributions

Lazy CD Ripper is open-source software licensed under the **GNU General Public License v3.0 (GPLv3)**.

To provide high-fidelity audio extraction, parallel FLAC/AAC transcoding, automated metadata tagging, and a native hardware-inspired user interface, Lazy CD Ripper incorporates or interacts with several third-party open-source libraries and tools.

This document details the licensing, copyrights, and source code availability for each third-party component.

---

## License Matrix

| Component | Role | License | Copyright / Authors | Project & Source Code |
| :--- | :--- | :--- | :--- | :--- |
| **FFmpeg** | Audio transcoding (FLAC & AAC) | **GNU GPLv3** | FFmpeg developers | [ffmpeg.org](https://ffmpeg.org) / [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) |
| **Mutagen** | Audio tagger & metadata embedding | **GNU GPLv2+** | Joe Wreschnig, Michael Urman, Christoph Reiter, et al. | [github.com/quodlibet/mutagen](https://github.com/quodlibet/mutagen) |
| **PySide6** | Qt 6 GUI bindings | **GNU LGPLv3** | The Qt Company Ltd. and Qt Project | [qt.io](https://www.qt.io) / [code.qt.io](https://code.qt.io/cgit/pyside/pyside-setup.git) |
| **Requests** | HTTP client for MusicBrainz API | **Apache 2.0** | Kenneth Reitz & Requests authors | [requests.readthedocs.io](https://requests.readthedocs.io) |
| **musicbrainzngs** | MusicBrainz WS2 client | **BSD 2-Clause** | Alastair Porter, Adrian Sampson, et al. | [github.com/alastair/python-musicbrainzngs](https://github.com/alastair/python-musicbrainzngs) |
| **Pillow** | Cover art processing & resizing | **HPND (MIT-like)** | Jeffrey A. Clark (Alex) and contributors | [python-pillow.org](https://python-pillow.org) |

---

## Source Code Availability & Written Offer (GPLv3 Section 6)

In accordance with Section 6 of the GNU General Public License version 3:

1. **Lazy CD Ripper Source Code:**
   The complete source code for Lazy CD Ripper is publicly available on GitHub at:  
   [https://github.com/lazyhead-code/lazycdripper](https://github.com/lazyhead-code/lazycdripper)

2. **FFmpeg Source Code:**
   The source code for the exact FFmpeg builds bundled with Lazy CD Ripper is available from:
   - Upstream FFmpeg: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Gyan.dev Windows builds: [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)

3. **Mutagen Source Code:**
   Available at: [https://github.com/quodlibet/mutagen](https://github.com/quodlibet/mutagen)

4. **PySide6 / Qt 6 Source Code:**
   Available at: [https://download.qt.io/official_releases/QtForPython/](https://download.qt.io/official_releases/QtForPython/)

---

## Individual Component Licenses

### 1. FFmpeg
- **License:** GNU General Public License v3.0 (GPLv3)
- **Copyright:** Copyright (c) 2000-2026 the FFmpeg developers.
- **Notice:** FFmpeg is a trademark of Fabrice Bellard, originator of the FFmpeg project.
The Windows standalone distribution of Lazy CD Ripper bundles pre-compiled FFmpeg binaries built by Gyan.dev with GPL features enabled (`--enable-gpl`). Therefore, the bundled `ffmpeg.exe` binary is distributed under the GNU General Public License v3.0. A complete copy of the GPLv3 license is provided in the root `LICENSE` file of this distribution and in `bin/ffmpeg-license.txt`.

### 2. Mutagen
- **License:** GNU General Public License v2.0 or later (GPL-2.0-or-later)
- **Copyright:**
  - Copyright (c) 2005-2009 Joe Wreschnig
  - Copyright (c) 2006-2009 Michael Urman
  - Copyright (c) 2009-2026 Christoph Reiter and contributors
- **Notice:** Mutagen is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

### 3. PySide6 (Qt for Python)
- **License:** GNU Lesser General Public License v3.0 (LGPLv3)
- **Copyright:** Copyright (C) 2026 The Qt Company Ltd. and other contributors.
- **Dynamic Linking Notice:** PySide6 and Qt 6 libraries are included as dynamically linked shared libraries (`.dll`). You have the right under LGPLv3 to replace these libraries with modified versions. Source code is available via the Qt Project.

### 4. Requests
- **License:** Apache License, Version 2.0
- **Copyright:** Copyright (c) 2019 Kenneth Reitz
- **Notice:**
  Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:
  http://www.apache.org/licenses/LICENSE-2.0

### 5. musicbrainzngs
- **License:** BSD 2-Clause "Simplified" License
- **Copyright:**
  - Copyright (c) 2011-2026 Alastair Porter, Adrian Sampson, and contributors.
- **Notice:**
  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
  1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

### 6. Pillow
- **License:** Historical Permission Notice and Disclaimer (HPND)
- **Copyright:**
  - Copyright (c) 2010-2026 by Jeffrey A. Clark (Alex) and contributors.
  - Copyright (c) 1995-2011 by Secret Labs AB.
  - Copyright (c) 1995-2011 by Fredrik Lundh.
- **Notice:**
  Permission to use, copy, modify, and distribute this software and its documentation for any purpose and without fee is hereby granted, provided that the above copyright notice appear in all copies and that both that copyright notice and this permission notice appear in supporting documentation.
