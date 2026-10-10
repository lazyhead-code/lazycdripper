# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification for Lazy CD Ripper.
Builds standalone executable package for Windows.
"""

import os
from pathlib import Path
import sys

block_cipher = None

# Base directories
project_root = Path(SPECPATH).resolve()
src_dir = project_root / "src"
assets_dir = project_root / "assets"

# Data files to bundle inside the application
datas = []
for img_name in ["logo.jpg", "logo.ico", "icon.png"]:
    img_file = assets_dir / "images" / img_name
    if img_file.is_file():
        datas.append((str(img_file), "assets/images"))

# Windows application icon
icon_path = None
ico = assets_dir / "images" / "logo.ico"
if ico.is_file():
    icon_path = str(ico)

# Bundled binaries (if present in assets/bin or bin)
binaries = []
for b_dir in [assets_dir / "bin", project_root / "bin"]:
    if b_dir.is_dir():
        for f in b_dir.iterdir():
            if f.is_file():
                binaries.append((str(f), "bin"))

# Hidden imports needed by PySide6, mutagen, requests, musicbrainzngs, discid
hiddenimports = [
    "lazycdripper",
    "lazycdripper.core",
    "lazycdripper.core.binaries",
    "lazycdripper.core.models",
    "lazycdripper.core.sanitizer",
    "lazycdripper.disc",
    "lazycdripper.disc.drive",
    "lazycdripper.disc.toc",
    "lazycdripper.encoder",
    "lazycdripper.encoder.ffmpeg",
    "lazycdripper.gui",
    "lazycdripper.gui.main",
    "lazycdripper.gui.main_window",
    "lazycdripper.gui.memories",
    "lazycdripper.gui.platform_windows",
    "lazycdripper.gui.theme",
    "lazycdripper.gui.widgets",
    "lazycdripper.gui.widgets.artwork_card",
    "lazycdripper.gui.widgets.completion_dialog",
    "lazycdripper.gui.widgets.credits_dialog",
    "lazycdripper.gui.widgets.liner_notes_dialog",
    "lazycdripper.gui.widgets.ripping_view",
    "lazycdripper.gui.widgets.track_table",
    "lazycdripper.metadata",
    "lazycdripper.metadata.coverart",
    "lazycdripper.metadata.musicbrainz",
    "lazycdripper.metadata.service",
    "lazycdripper.pipeline",
    "lazycdripper.pipeline.orchestrator",
    "lazycdripper.ripper",
    "lazycdripper.ripper.cdparanoia",
    "lazycdripper.ripper.mock",
    "lazycdripper.ripper.windows",
    "lazycdripper.tagger",
    "lazycdripper.tagger.tagger",
    "mutagen.flac",
    "mutagen.mp4",
    "mutagen.id3",
    "musicbrainzngs",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "requests",
]

# Exclude unnecessary heavy dependencies to keep distribution bundle lean
excludes = [
    "tkinter",
    "matplotlib",
    "scipy",
    "numpy",
    "pandas",
    "pytest",
    "unittest",
]

a = Analysis(
    [str(src_dir / "lazycdripper" / "gui" / "main.py")],
    pathex=[str(src_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LazyCDRipper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LazyCDRipper",
)
