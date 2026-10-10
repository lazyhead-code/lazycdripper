"""Unit tests for binary resolution and discovery subsystem."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from lazycdripper.core.binaries import (
    _is_executable_file,
    find_binary,
    get_binary_search_paths,
    is_binary_available,
)


class TestBinaries(unittest.TestCase):
    """Test cross-platform binary resolution for bundled tools."""

    def test_is_executable_file_nonexistent(self):
        bogus = Path("/nonexistent/path/to/binary_1234567")
        self.assertFalse(_is_executable_file(bogus))

    def test_is_executable_file_on_sys_executable(self):
        py_exe = Path(sys.executable)
        self.assertTrue(_is_executable_file(py_exe))

    def test_is_executable_file_on_directory(self):
        temp_dir = Path(tempfile.gettempdir())
        self.assertFalse(_is_executable_file(temp_dir))

    def test_get_binary_search_paths_default(self):
        paths = get_binary_search_paths()
        self.assertIsInstance(paths, list)
        self.assertTrue(len(paths) > 0)
        # Should include cwd / bin
        cwd_bin = Path.cwd() / "bin"
        self.assertTrue(any(p == cwd_bin for p in paths))

    def test_get_binary_search_paths_frozen(self):
        with tempfile.TemporaryDirectory() as fake_meipass:
            with patch.object(sys, "frozen", True, create=True), \
                 patch.object(sys, "_MEIPASS", fake_meipass, create=True):
                paths = get_binary_search_paths()
                mei_path = Path(fake_meipass)
                self.assertTrue(any(p == mei_path / "bin" or p == mei_path for p in paths))

    def test_find_binary_with_custom_existing_path(self):
        py_exe = sys.executable
        found = find_binary("custom_tool", custom_path=py_exe)
        self.assertEqual(Path(found).resolve(), Path(py_exe).resolve())

    def test_find_binary_with_bundled_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_bin_dir = tmp_path / "bin"
            fake_bin_dir.mkdir()
            fake_tool = fake_bin_dir / "my_custom_tool"
            fake_tool.write_text("#!/bin/sh\necho hi")
            fake_tool.chmod(0o755)

            with patch("lazycdripper.core.binaries.get_binary_search_paths", return_value=[fake_bin_dir]):
                found = find_binary("my_custom_tool")
                self.assertEqual(Path(found).resolve(), fake_tool.resolve())

    def test_find_binary_fallback_to_name(self):
        with patch("shutil.which", return_value=None):
            found = find_binary("definitely_nonexistent_binary_xyz987")
            self.assertEqual(found, "definitely_nonexistent_binary_xyz987")

    def test_find_binary_uses_system_path_when_not_bundled(self):
        with patch("lazycdripper.core.binaries.get_binary_search_paths", return_value=[]), \
             patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            found = find_binary("ffmpeg")
            self.assertEqual(found, "/usr/bin/ffmpeg")

    def test_find_binary_prefers_bundled_over_system_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            bundled_bin_dir = Path(tmp_dir) / "bin"
            bundled_bin_dir.mkdir()
            bundled_tool = bundled_bin_dir / "ffmpeg"
            bundled_tool.write_text("#!/bin/sh\necho bundled")
            bundled_tool.chmod(0o755)

            with patch("lazycdripper.core.binaries.get_binary_search_paths", return_value=[bundled_bin_dir]), \
                 patch("shutil.which", return_value="/usr/bin/ffmpeg"):
                found = find_binary("ffmpeg")
                self.assertEqual(Path(found).resolve(), bundled_tool.resolve())

    def test_is_binary_available_real(self):
        self.assertTrue(is_binary_available(sys.executable))

    def test_is_binary_available_false(self):
        with patch("shutil.which", return_value=None):
            self.assertFalse(is_binary_available("nonexistent_binary_9999"))


if __name__ == "__main__":
    unittest.main()
