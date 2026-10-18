"""Unit tests for the audio encoding engine (standalone FLAC and LAME binaries)."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from lazycdripper.encoder import AudioEncoder, MockEncoder


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
            self.assertTrue(flac_out.read_bytes().startswith(b"fLaC"))
            self.assertTrue(mp3_out.read_bytes().startswith(b"ID3"))

    @patch("subprocess.run")
    def test_encode_flac_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("lazycdripper.encoder.encoder.is_binary_available", side_effect=lambda p: "flac" in str(p)):
            encoder = AudioEncoder(flac_path="/usr/bin/flac", lame_path="/usr/bin/lame")
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
    def test_encode_mp3_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("lazycdripper.encoder.encoder.is_binary_available", side_effect=lambda p: "lame" in str(p)):
            encoder = AudioEncoder(flac_path="/usr/bin/flac", lame_path="/usr/bin/lame")
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
    def test_subprocess_create_no_window_flag(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("lazycdripper.encoder.encoder.is_binary_available", return_value=True):
            encoder = AudioEncoder(flac_path="/usr/bin/flac", lame_path="/usr/bin/lame")
            with tempfile.TemporaryDirectory() as temp_dir:
                wav_file = Path(temp_dir) / "in.wav"
                flac_file = Path(temp_dir) / "out.flac"
                with patch("lazycdripper.encoder.encoder.os.name", "nt"):
                    encoder.encode_flac(wav_file, flac_file)
                    self.assertIn("creationflags", mock_run.call_args[1])
                    self.assertEqual(mock_run.call_args[1]["creationflags"], 0x08000000)

    def test_is_available_when_both_present(self):
        with patch("lazycdripper.encoder.encoder.is_binary_available", return_value=True):
            encoder = AudioEncoder(flac_path="/usr/bin/flac", lame_path="/usr/bin/lame")
            self.assertTrue(encoder.is_available)

    def test_is_available_false_when_one_missing(self):
        with patch("lazycdripper.encoder.encoder.is_binary_available", side_effect=lambda p: "flac" in str(p)):
            encoder = AudioEncoder(flac_path="/usr/bin/flac", lame_path="/usr/bin/lame")
            self.assertFalse(encoder.is_available)

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
    def test_get_version(self, mock_run):
        def fake_run(cmd, *args, **kwargs):
            if "flac" in cmd[0]:
                return MagicMock(returncode=0, stdout="flac 1.4.3\nCopyright (C) ...")
            elif "lame" in cmd[0]:
                return MagicMock(returncode=0, stdout="LAME 64bits version 4.0 (http://lame.sf.net)")
            return MagicMock(returncode=1, stdout="")

        mock_run.side_effect = fake_run
        with patch("lazycdripper.encoder.encoder.is_binary_available", return_value=True):
            encoder = AudioEncoder(flac_path="/usr/bin/flac", lame_path="/usr/bin/lame")
            version = encoder.get_version()
            self.assertIn("FLAC 1.4.3", version)
            self.assertIn("LAME 4.0", version)


if __name__ == "__main__":
    unittest.main()
