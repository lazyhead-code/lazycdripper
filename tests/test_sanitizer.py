"""Unit tests for path and filename sanitization."""

import unittest
from pathlib import Path
from lazycdripper.core.models import AudioFormat
from lazycdripper.core.sanitizer import (
    format_album_directory_name,
    format_track_filename,
    generate_naming_preview,
    get_target_track_path,
    sanitize_filename,
)


class TestSanitizer(unittest.TestCase):
    def test_sanitize_filename_basic(self):
        self.assertEqual(sanitize_filename("The Dark Side of the Moon"), "The Dark Side of the Moon")

    def test_sanitize_filename_illegal_characters(self):
        # Slashes become hyphens, colons become ' - ', quotes stripped, question marks stripped
        self.assertEqual(sanitize_filename('AC/DC: Who Made Who? "Live"'), "AC-DC - Who Made Who Live")
        self.assertEqual(sanitize_filename("<Dangerous> *Star* | Track ?"), "Dangerous Star - Track")

    def test_sanitize_filename_preserves_hyphenated_words(self):
        self.assertEqual(sanitize_filename("Self-Titled Album"), "Self-Titled Album")
        self.assertEqual(sanitize_filename("Jay-Z"), "Jay-Z")

    def test_sanitize_filename_empty_and_spaces(self):
        self.assertEqual(sanitize_filename("   "), "Unknown")
        self.assertEqual(sanitize_filename("..."), "Unknown")
        self.assertEqual(sanitize_filename("  Track Name .  "), "Track Name")

    def test_sanitize_filename_windows_reserved(self):
        self.assertEqual(sanitize_filename("CON"), "CON_")
        self.assertEqual(sanitize_filename("aux"), "aux_")
        self.assertEqual(sanitize_filename("NUL"), "NUL_")
        self.assertEqual(sanitize_filename("COM1"), "COM1_")

    def test_format_album_directory_name(self):
        flac_dir = format_album_directory_name("Pink Floyd", "Animals", 1977, AudioFormat.FLAC)
        self.assertEqual(flac_dir, "Pink Floyd - Animals (1977) [FLAC]")

        mp3_dir = format_album_directory_name("Miles Davis", "Kind of Blue", 1959, AudioFormat.MP3)
        self.assertEqual(mp3_dir, "Miles Davis - Kind of Blue (1959) [MP3]")

        aac_dir = format_album_directory_name("Miles Davis", "Kind of Blue", 1959, AudioFormat.AAC)
        self.assertEqual(aac_dir, "Miles Davis - Kind of Blue (1959) [AAC]")

        # Without year
        no_year = format_album_directory_name("Artist", "Self-Titled", None, AudioFormat.FLAC)
        self.assertEqual(no_year, "Artist - Self-Titled [FLAC]")

    def test_format_track_filename_defaults(self):
        self.assertEqual(format_track_filename(1, "Speak to Me", AudioFormat.FLAC), "01 - Speak to Me.flac")
        self.assertEqual(format_track_filename(2, "Breathe", AudioFormat.MP3), "02 - Breathe.mp3")
        self.assertEqual(format_track_filename(12, "Brain Damage", AudioFormat.AAC), "12 - Brain Damage.m4a")

    def test_format_track_filename_with_artist(self):
        name = format_track_filename(
            track_number=1,
            title="Speak to Me",
            audio_format=AudioFormat.FLAC,
            include_track_number=True,
            include_artist=True,
            artist="Pink Floyd",
        )
        self.assertEqual(name, "01 - Pink Floyd - Speak to Me.flac")

    def test_format_track_filename_without_track_number(self):
        name = format_track_filename(
            track_number=1,
            title="Speak to Me",
            audio_format=AudioFormat.FLAC,
            include_track_number=False,
            include_artist=False,
        )
        self.assertEqual(name, "Speak to Me.flac")

        with_artist = format_track_filename(
            track_number=1,
            title="Speak to Me",
            audio_format=AudioFormat.FLAC,
            include_track_number=False,
            include_artist=True,
            artist="Pink Floyd",
        )
        self.assertEqual(with_artist, "Pink Floyd - Speak to Me.flac")

    def test_generate_naming_preview(self):
        # Default: number=True, artist=False
        preview_default = generate_naming_preview(
            artist="Pink Floyd",
            album="The Dark Side of the Moon",
            year=1973,
            track_number=1,
            track_title="Speak to Me",
            audio_format=AudioFormat.FLAC,
            include_track_number=True,
            include_artist=False,
        )
        self.assertEqual(
            preview_default,
            "Pink Floyd - The Dark Side of the Moon (1973) [FLAC]/01 - Speak to Me.flac",
        )

        # With artist toggle active:
        preview_with_artist = generate_naming_preview(
            artist="Pink Floyd",
            album="The Dark Side of the Moon",
            year=1973,
            track_number=1,
            track_title="Speak to Me",
            audio_format=AudioFormat.FLAC,
            include_track_number=True,
            include_artist=True,
        )
        self.assertEqual(
            preview_with_artist,
            "Pink Floyd - The Dark Side of the Moon (1973) [FLAC]/01 - Pink Floyd - Speak to Me.flac",
        )

    def test_get_target_track_path_single_disc(self):
        base = Path("/Music")
        path = get_target_track_path(
            base_output_dir=base,
            artist="Metallica",
            album="Master of Puppets",
            year=1986,
            audio_format=AudioFormat.FLAC,
            track_number=2,
            track_title="Master of Puppets",
            disc_number=1,
            total_discs=1,
        )
        expected = base / "Metallica - Master of Puppets (1986) [FLAC]" / "02 - Master of Puppets.flac"
        self.assertEqual(path, expected)

    def test_get_target_track_path_multi_disc(self):
        base = Path("/Music")
        path = get_target_track_path(
            base_output_dir=base,
            artist="The Smashing Pumpkins",
            album="Mellon Collie and the Infinite Sadness",
            year=1995,
            audio_format=AudioFormat.AAC,
            track_number=1,
            track_title="Tonight, Tonight",
            disc_number=1,
            total_discs=2,
        )
        expected = (
            base
            / "The Smashing Pumpkins - Mellon Collie and the Infinite Sadness (1995) [AAC]"
            / "Disc 01"
            / "01 - Tonight, Tonight.m4a"
        )
        self.assertEqual(path, expected)

    def test_get_target_track_path_multi_disc_mp3(self):
        base = Path("/Music")
        path = get_target_track_path(
            base_output_dir=base,
            artist="The Smashing Pumpkins",
            album="Mellon Collie and the Infinite Sadness",
            year=1995,
            audio_format=AudioFormat.MP3,
            track_number=1,
            track_title="Tonight, Tonight",
            disc_number=1,
            total_discs=2,
        )
        expected = (
            base
            / "The Smashing Pumpkins - Mellon Collie and the Infinite Sadness (1995) [MP3]"
            / "Disc 01"
            / "01 - Tonight, Tonight.mp3"
        )
        self.assertEqual(path, expected)


if __name__ == "__main__":
    unittest.main()
