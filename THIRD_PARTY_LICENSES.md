# Third-Party Software Licenses & Attributions

Lazy CD Ripper is open-source software licensed under the **GNU General Public License v3.0 (GPLv3)**.

To provide high-fidelity audio extraction, parallel FLAC/MP3 transcoding, automated metadata tagging, and a native hardware-inspired user interface, Lazy CD Ripper incorporates or interacts with several third-party open-source libraries and tools.

This document details the licensing, copyrights, and source code availability for each third-party component.

---

## License Matrix

| Component | Role | License | Copyright / Authors | Project & Source Code |
| :--- | :--- | :--- | :--- | :--- |
| **FLAC** | Lossless audio encoder (`flac.exe`) | **BSD 3-Clause / GNU GPLv2** | Xiph.Org Foundation & Josh Coalson | [xiph.org/flac](https://xiph.org/flac/) |
| **LAME** | MP3 audio encoder (`lame.exe`, `lame_enc.dll`) | **GNU LGPLv2+** | The LAME Project | [lame.sourceforge.io](https://lame.sourceforge.io/) |
| **mpg123** | Audio decoding library (`libmpg123-0.dll`) | **GNU LGPLv2.1** | Michael Hipp, Thomas Orgis, et al. | [mpg123.org](https://mpg123.org/) |
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

2. **FLAC, LAME & mpg123 Source Code:**
   The source code for the standalone binaries and libraries bundled with Lazy CD Ripper is available from:
   - FLAC: [https://xiph.org/flac/download.html](https://xiph.org/flac/download.html) / [github.com/xiph/flac](https://github.com/xiph/flac)
   - LAME: [https://lame.sourceforge.io/download.php](https://lame.sourceforge.io/download.php) / [sourceforge.net/projects/lame](https://sourceforge.net/projects/lame/)
   - mpg123: [https://mpg123.org/download.shtml](https://mpg123.org/download.shtml)

3. **Mutagen Source Code:**
   Available at: [https://github.com/quodlibet/mutagen](https://github.com/quodlibet/mutagen)

4. **PySide6 / Qt 6 Source Code:**
   Available at: [https://download.qt.io/official_releases/QtForPython/](https://download.qt.io/official_releases/QtForPython/)

---

## Individual Component Licenses

### 1. FLAC (Free Lossless Audio Codec)
- **License:** BSD 3-Clause (libFLAC) / GNU General Public License v2.0 (flac CLI executable)
- **Copyright:** Copyright (c) 2000-2009 Josh Coalson, 2011-2026 Xiph.Org Foundation.
- **Notice:** FLAC is an open, royalty-free audio format and reference encoder developed by the Xiph.Org Foundation.

### 2. LAME (LAME Ain't an MP3 Encoder)
- **License:** GNU Lesser General Public License v2.0 or later (LGPL-2.0-or-later)
- **Copyright:** Copyright (c) 1999-2026 The LAME Project developers and contributors.
- **Notice:** All patents covering the MP3 format expired worldwide in April/May 2017. LAME is distributed as a patent-free audio encoder under the GNU LGPL.

### 3. mpg123
- **License:** GNU Lesser General Public License v2.1 (LGPL-2.1)
- **Copyright:** Copyright (c) 1995-2026 Michael Hipp, Thomas Orgis, and the mpg123 project.
- **Notice:** Bundled as `libmpg123-0.dll` accompanying LAME for decoding support under LGPLv2.1.

### 4. Mutagen
- **License:** GNU General Public License v2.0 or later (GPL-2.0-or-later)
- **Copyright:**
  - Copyright (c) 2005-2009 Joe Wreschnig
  - Copyright (c) 2006-2009 Michael Urman
  - Copyright (c) 2009-2026 Christoph Reiter and contributors
- **Notice:** Mutagen is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

### 5. PySide6 (Qt for Python)
- **License:** GNU Lesser General Public License v3.0 (LGPLv3)
- **Copyright:** Copyright (C) 2026 The Qt Company Ltd. and other contributors.
- **Dynamic Linking Notice:** PySide6 and Qt 6 libraries are included as dynamically linked shared libraries (`.dll`). You have the right under LGPLv3 to replace these libraries with modified versions. Source code is available via the Qt Project.

### 6. Requests
- **License:** Apache License, Version 2.0
- **Copyright:** Copyright (c) 2019 Kenneth Reitz
- **Notice:**
  Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:
  http://www.apache.org/licenses/LICENSE-2.0

### 7. musicbrainzngs
- **License:** BSD 2-Clause "Simplified" License
- **Copyright:**
  - Copyright (c) 2011-2026 Alastair Porter, Adrian Sampson, and contributors.
- **Notice:**
  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
  1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

### 8. Pillow
- **License:** Historical Permission Notice and Disclaimer (HPND)
- **Copyright:**
  - Copyright (c) 2010-2026 by Jeffrey A. Clark (Alex) and contributors.
  - Copyright (c) 1995-2011 by Secret Labs AB.
  - Copyright (c) 1995-2011 by Fredrik Lundh.
- **Notice:**
  Permission to use, copy, modify, and distribute this software and its documentation for any purpose and without fee is hereby granted, provided that the above copyright notice appear in all copies and that both that copyright notice and this permission notice appear in supporting documentation.
