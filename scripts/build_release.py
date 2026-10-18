#!/usr/bin/env python3
"""
Cross-platform build and packaging script for Lazy CD Ripper.
Orchestrates PyInstaller standalone compilation, binary bundling, and archive creation.
"""

import argparse
import os
from pathlib import Path
import platform
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from lazycdripper import __version__ as VERSION
APP_NAME = "LazyCDRipper"


def run_cmd(cmd: list, cwd: Path = None):
    print(f"--> Running: {' '.join(str(c) for c in cmd)}")
    res = subprocess.run(cmd, cwd=cwd)
    if res.returncode != 0:
        print(f"Error: Command failed with exit code {res.returncode}")
        sys.exit(res.returncode)


def build_pyinstaller(project_root: Path):
    """Run PyInstaller with lazycdripper.spec."""
    print(f"\n[1/2] Building {APP_NAME} via PyInstaller...")
    spec_file = project_root / "lazycdripper.spec"
    if not spec_file.is_file():
        print(f"Error: Spec file {spec_file} does not exist.")
        sys.exit(1)

    pyinstaller_cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)]
    run_cmd(pyinstaller_cmd, cwd=project_root)

    import shutil
    dist_dir = project_root / "dist" / APP_NAME

    # Ensure bundled bin directory in dist contains standalone binaries (flac.exe, lame.exe, lame_enc.dll) if present in repo
    bin_dir = project_root / "bin"
    dist_bin = dist_dir / "bin"
    if bin_dir.is_dir():
        for b_file in bin_dir.iterdir():
            if b_file.is_file():
                dist_bin.mkdir(parents=True, exist_ok=True)
                shutil.copy2(b_file, dist_bin / b_file.name)
                print(f"Copied bundled binary {b_file.name} to {dist_bin / b_file.name}")

    # Copy legal documentation (GPLv3 & Third-Party Attributions)
    for lic_file in ["LICENSE", "THIRD_PARTY_LICENSES.md"]:
        lic_path = project_root / lic_file
        if lic_path.is_file():
            shutil.copy2(lic_path, dist_dir / lic_file)
            print(f"Copied {lic_file} to {dist_dir / lic_file}")

    print("PyInstaller build complete.")


def create_release_archive(project_root: Path):
    """Package dist/LazyCDRipper into a release zip archive."""
    print(f"\n[2/2] Creating release archive...")
    dist_dir = project_root / "dist"
    app_dist = dist_dir / APP_NAME

    if not app_dist.is_dir():
        print(f"Error: Distribution directory {app_dist} not found.")
        sys.exit(1)

    machine = platform.machine().lower()
    arch = "x64" if machine in ["amd64", "x86_64"] else ("arm64" if machine in ["arm64", "aarch64"] else machine)

    archive_name = f"{APP_NAME}-v{VERSION}-windows-{arch}-portable.zip"
    archive_path = dist_dir / archive_name
    print(f"Creating Windows zip archive: {archive_path}")
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(app_dist):
            for f in files:
                file_path = Path(root) / f
                arcname = Path(APP_NAME) / file_path.relative_to(app_dist)
                zf.write(file_path, arcname)

    print(f"Successfully generated archive: {archive_path}")


def main():
    parser = argparse.ArgumentParser(description=f"Build and package {APP_NAME}.")
    parser.add_argument("--skip-build", action="store_true", help="Skip PyInstaller build and only package archive.")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent

    if not args.skip_build:
        build_pyinstaller(project_root)

    create_release_archive(project_root)
    print(f"\nPackaging process completed successfully for {APP_NAME} v{VERSION}!")


if __name__ == "__main__":
    main()
