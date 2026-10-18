"""Unit tests for the audio encoding engine (FLAC / LAME standalone and FFmpeg fallback)."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from lazycdripper.encoder.ffmpeg import AudioEncoder, FFmpegEncoder, MockEncoder


class TestAudioEncoder(unittest.TestCase):
    def test_mock_encoder_creates_flac_and_mp3_files(self):
        encoder = MockEncoder()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            wav_file = temp_path / "test.wav"
            wav_file.write_bytes(b"dummy wav content")

            flac_out = temp_path / "test.flac"
            mp3_out = temp_path / "test.mp3"

            flac_ok, mp3_ok = encoder.encode_dual(wav_file, flac_out, mp3_out)

            self.assertTrue(flac_ok)
            self.assertTrue(mp3_ok)
            self.assertTrue(flac_out.exists())
            self.assertTrue(mp3_out.exists())
            self.assertTrue(mp3_out.read_bytes().startswith(b"ID3"))

    def test_mock_encoder_backward_compatible_aac(self):
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
            self.assertTrue(aac_out.exists())

    @patch("subprocess.run")
    def test_standalone_encode_flac_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("lazycdripper.encoder.ffmpeg.is_binary_available", side_effect=lambda p: "flac" in str(p)):
            encoder = FFmpegEncoder(flac_path="/usr/bin/flac")
            with tempfile.TemporaryDirectory() as temp_dir:
                wav_file = Path(temp_dir) / "in.wav"
                flac_file = Path(temp_dir) / "out.flac"

                ok = encoder.encode_flac(wav_file, flac_file)
                self.assertTrue(ok)

                mock_run.assert_called_once()
                called_cmd = mock_run.call_args[0][0]
                self.assertEqual(called_cmd[0], "/usr/bin/flac")
                self.assertIn("-8", called_cmd)
                self.assertIn("--verify", called_cmd)
                self.assertIn("-f", called_cmd)
                self.assertIn("-o", called_cmd)

    @patch("subprocess.run")
    def test_standalone_encode_mp3_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("lazycdripper.encoder.ffmpeg.is_binary_available", side_effect=lambda p: "lame" in str(p)):
            encoder = FFmpegEncoder(lame_path="/usr/bin/lame")
            with tempfile.TemporaryDirectory() as temp_dir:
                wav_file = Path(temp_dir) / "in.wav"
                mp3_file = Path(temp_dir) / "out.mp3"

                ok = encoder.encode_mp3(wav_file, mp3_file)
                self.assertTrue(ok)

                mock_run.assert_called_once()
                called_cmd = mock_run.call_args[0][0]
                self.assertEqual(called_cmd[0], "/usr/bin/lame")
                self.assertIn("-b", called_cmd)
                self.assertIn("320", called_cmd)
                self.assertIn("-q", called_cmd)
                self.assertIn("0", called_cmd)

    @patch("subprocess.run")
    def test_ffmpeg_fallback_flac_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        # Standalone flac is not available, only ffmpeg
        with patch("lazycdripper.encoder.ffmpeg.is_binary_available", side_effect=lambda p: "ffmpeg" in str(p)):
            encoder = FFmpegEncoder(binary_path="/usr/bin/ffmpeg", flac_path="nonexistent_flac")

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
    def test_ffmpeg_fallback_mp3_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        # Standalone lame is not available, only ffmpeg
        with patch("lazycdripper.encoder.ffmpeg.is_binary_available", side_effect=lambda p: "ffmpeg" in str(p)):
            encoder = FFmpegEncoder(binary_path="/usr/bin/ffmpeg", lame_path="nonexistent_lame")

            with tempfile.TemporaryDirectory() as temp_dir:
                wav_file = Path(temp_dir) / "in.wav"
                mp3_file = Path(temp_dir) / "out.mp3"

                ok = encoder.encode_mp3(wav_file, mp3_file)
                self.assertTrue(ok)

                called_cmd = mock_run.call_args[0][0]
                self.assertEqual(called_cmd[0], "/usr/bin/ffmpeg")
                self.assertIn("-c:a", called_cmd)
                self.assertIn("libmp3lame", called_cmd)
                self.assertIn("-b:a", called_cmd)
                self.assertIn("320k", called_cmd)
                self.assertIn("-q:a", called_cmd)
                self.assertIn("0", called_cmd)

    @patch("subprocess.run")
    def test_ffmpeg_encode_aac_legacy_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        encoder = FFmpegEncoder(binary_path="/usr/bin/ffmpeg")
        encoder._has_fdk_aac = False

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

    @patch("subprocess.run")
    def test_subprocess_create_no_window_flag(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        encoder = FFmpegEncoder(binary_path="/usr/bin/ffmpeg")
        with tempfile.TemporaryDirectory() as temp_dir:
            wav_file = Path(temp_dir) / "in.wav"
            flac_file = Path(temp_dir) / "out.flac"
            with patch("lazycdripper.encoder.ffmpeg.os.name", "nt"), \
                 patch("lazycdripper.encoder.ffmpeg.is_binary_available", return_value=True):
                encoder.encode_flac(wav_file, flac_file)
                self.assertIn("creationflags", mock_run.call_args[1])
                self.assertEqual(mock_run.call_args[1]["creationflags"], 0x08000000)

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
        self.assertIn("audio encoder", str(ctx.exception).lower())

    @patch("subprocess.run")
    def test_ffmpeg_get_version(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ffmpeg version 7.1-essentials_build-www.gyan.dev Copyright (c) 2000-2024 the FFmpeg developers",
        )
        with patch("lazycdripper.encoder.ffmpeg.is_binary_available", side_effect=lambda p: "ffmpeg" in str(p)):
            encoder = FFmpegEncoder(binary_path="/usr/bin/ffmpeg", lame_path="nonexistent_lame")
            version = encoder.get_version()
            self.assertEqual(version, "FFmpeg 7.1")


if __name__ == "__main__":
    unittest.main()
