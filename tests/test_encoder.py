"""Unit tests for the FFmpeg audio encoding engine."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from lazycdripper.encoder.ffmpeg import FFmpegEncoder, MockEncoder


class TestFFmpegEncoder(unittest.TestCase):
    def test_mock_encoder_creates_files(self):
        encoder = MockEncoder()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            wav_file = temp_path / "test.wav"
            wav_file.write_bytes(b"dummy wav content")

            flac_out = temp_path / "test.flac"
            aac_out = temp_path / "test.m4a"

            flac_ok, aac_ok = encoder.encode_dual(wav_file, flac_out, aac_out)

            self.assertTrue(flac_ok)
            self.assertTrue(aac_ok)
            self.assertTrue(flac_out.exists())
            self.assertTrue(aac_out.exists())

    @patch("subprocess.run")
    def test_ffmpeg_encode_flac_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        encoder = FFmpegEncoder(binary_path="/usr/bin/ffmpeg")

        with tempfile.TemporaryDirectory() as temp_dir:
            wav_file = Path(temp_dir) / "in.wav"
            flac_file = Path(temp_dir) / "out.flac"

            ok = encoder.encode_flac(wav_file, flac_file)
            self.assertTrue(ok)

            mock_run.assert_called_once()
            called_cmd = mock_run.call_args[0][0]
            self.assertEqual(called_cmd[0], "/usr/bin/ffmpeg")
            self.assertIn("-c:a", called_cmd)
            self.assertIn("flac", called_cmd)
            self.assertIn("-compression_level", called_cmd)
            self.assertIn("8", called_cmd)

    @patch("subprocess.run")
    def test_ffmpeg_encode_aac_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        encoder = FFmpegEncoder(binary_path="/usr/bin/ffmpeg")
        encoder._has_fdk_aac = False  # Test standard fallback

        with tempfile.TemporaryDirectory() as temp_dir:
            wav_file = Path(temp_dir) / "in.wav"
            aac_file = Path(temp_dir) / "out.m4a"

            ok = encoder.encode_aac(wav_file, aac_file)
            self.assertTrue(ok)

            called_cmd = mock_run.call_args[0][0]
            self.assertIn("-c:a", called_cmd)
            self.assertIn("aac", called_cmd)
            self.assertIn("-b:a", called_cmd)
            self.assertIn("256k", called_cmd)

    def test_ensure_ffmpeg_already_found(self):
        from lazycdripper.core.binaries import ensure_ffmpeg
        with patch("lazycdripper.core.binaries.find_binary", return_value="/usr/bin/ffmpeg"), \
             patch("lazycdripper.core.binaries.is_binary_available", return_value=True):
            result = ensure_ffmpeg()
            self.assertEqual(result, "/usr/bin/ffmpeg")

    def test_ffmpeg_encoder_discovers_system_path(self):
        with patch("lazycdripper.encoder.ffmpeg.find_binary", return_value="/usr/bin/ffmpeg"), \
             patch("lazycdripper.encoder.ffmpeg.is_binary_available", return_value=True):
            encoder = FFmpegEncoder()
            self.assertEqual(encoder.binary_path, "/usr/bin/ffmpeg")
            self.assertTrue(encoder.is_available)

    def test_orchestrator_raises_when_encoder_unavailable(self):
        from lazycdripper.pipeline.orchestrator import RipPipelineOrchestrator
        from lazycdripper.core.models import AlbumInfo

        mock_unavailable_encoder = MagicMock()
        mock_unavailable_encoder.is_available = False

        orchestrator = RipPipelineOrchestrator(
            encoder=mock_unavailable_encoder,
        )
        album = AlbumInfo(title="Test", artist="Artist", album_artist="Artist", year=2024, tracks=[])
        with self.assertRaises(RuntimeError) as ctx:
            orchestrator.execute_rip(album=album, base_output_dir=Path("/tmp"))
        self.assertIn("FFmpeg is required", str(ctx.exception))

    @patch("subprocess.run")
    def test_ffmpeg_get_version(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ffmpeg version 7.1-essentials_build-www.gyan.dev Copyright (c) 2000-2024 the FFmpeg developers",
        )
        with patch("lazycdripper.encoder.ffmpeg.is_binary_available", return_value=True):
            encoder = FFmpegEncoder(binary_path="/usr/bin/ffmpeg")
            version = encoder.get_version()
            self.assertEqual(version, "7.1")


if __name__ == "__main__":
    unittest.main()
