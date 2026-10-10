"""Unit and mock integration tests for the MusicBrainz and Cover Art Archive subsystem."""

import unittest
from unittest.mock import MagicMock, patch
from lazycdripper.core.models import AlbumInfo, ArtworkCandidate
from lazycdripper.metadata.coverart import CoverArtClient
from lazycdripper.metadata.musicbrainz import MusicBrainzClient
from lazycdripper.metadata.service import MetadataService

MOCK_MUSICBRAINZ_DISCID_RESPONSE = {
    "releases": [
        {
            "id": "mbid-release-12345",
            "title": "The Dark Side of the Moon",
            "date": "1973-03-01",
            "artist-credit": [
                {"name": "Pink Floyd", "joinphrase": ""}
            ],
            "genres": [{"name": "Progressive Rock"}],
            "media": [
                {
                    "position": 1,
                    "tracks": [
                        {
                            "position": 1,
                            "title": "Speak to Me",
                            "length": 65000,
                            "artist-credit": [{"name": "Pink Floyd"}],
                        },
                        {
                            "position": 2,
                            "title": "Breathe (In the Air)",
                            "length": 169000,
                            "artist-credit": [{"name": "Pink Floyd"}],
                        },
                    ],
                }
            ],
        }
    ]
}

MOCK_CAA_RESPONSE = {
    "images": [
        {
            "id": 1001,
            "front": True,
            "types": ["Front"],
            "image": "https://coverartarchive.org/release/mbid-release-12345/1001.jpg",
            "thumbnails": {
                "250": "https://coverartarchive.org/release/mbid-release-12345/1001-250.jpg",
                "500": "https://coverartarchive.org/release/mbid-release-12345/1001-500.jpg",
            },
            "width": 1200,
            "height": 1200,
            "comment": "Original UK Vinyl gatefold",
        },
        {
            "id": 1002,
            "front": False,
            "types": ["Back"],
            "image": "https://coverartarchive.org/release/mbid-release-12345/1002.jpg",
            "thumbnails": {},
            "comment": "Back cover",
        },
    ]
}


class TestMusicBrainzClient(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.client = MusicBrainzClient(session=self.mock_session)

    def test_lookup_disc_id_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_MUSICBRAINZ_DISCID_RESPONSE
        self.mock_session.get.return_value = mock_resp

        results = self.client.lookup_disc_id("test_disc_id_123")

        self.assertEqual(len(results), 1)
        album = results[0]
        self.assertEqual(album.title, "The Dark Side of the Moon")
        self.assertEqual(album.artist, "Pink Floyd")
        self.assertEqual(album.year, 1973)
        self.assertEqual(album.genre, "Progressive Rock")
        self.assertEqual(len(album.tracks), 2)
        self.assertEqual(album.tracks[0].title, "Speak to Me")
        self.assertEqual(album.tracks[0].track_number, 1)
        self.assertAlmostEqual(album.tracks[0].duration_seconds, 65.0)

    def test_lookup_disc_id_not_found(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        self.mock_session.get.return_value = mock_resp

        results = self.client.lookup_disc_id("unknown_disc_id")
        self.assertEqual(results, [])

    def test_parse_year(self):
        self.assertEqual(MusicBrainzClient._parse_year("1973-03-01"), 1973)
        self.assertEqual(MusicBrainzClient._parse_year("2024"), 2024)
        self.assertIsNone(MusicBrainzClient._parse_year(None))
        self.assertIsNone(MusicBrainzClient._parse_year("Unknown"))

    def test_lookup_disc_id_with_toc(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_MUSICBRAINZ_DISCID_RESPONSE
        self.mock_session.get.return_value = mock_resp

        results = self.client.lookup_disc_id("test_disc_id_123", toc="1 2 20925 150 4050")

        self.assertEqual(len(results), 1)
        self.mock_session.get.assert_called_once()
        called_params = self.mock_session.get.call_args[1]["params"]
        self.assertEqual(called_params["toc"], "1 2 20925 150 4050")
        self.assertEqual(called_params["inc"], "recordings+artist-credits+genres+release-groups")
        self.assertNotIn("media", called_params["inc"])
        self.assertNotIn("discids", called_params["inc"])

    @patch("time.sleep", return_value=None)
    def test_lookup_disc_id_retry_on_503(self, mock_sleep):
        mock_503 = MagicMock()
        mock_503.status_code = 503
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = MOCK_MUSICBRAINZ_DISCID_RESPONSE

        self.mock_session.get.side_effect = [mock_503, mock_200]

        results = self.client.lookup_disc_id("test_disc_id_123")
        self.assertEqual(len(results), 1)
        self.assertEqual(self.mock_session.get.call_count, 2)
        mock_sleep.assert_called_once_with(1.2)

    def test_lookup_by_toc(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_MUSICBRAINZ_DISCID_RESPONSE
        self.mock_session.get.return_value = mock_resp

        results = self.client.lookup_by_toc("1 2 20925 150 4050")

        self.assertEqual(len(results), 1)
        called_url = self.mock_session.get.call_args[0][0]
        self.assertTrue(called_url.endswith("/discid/-"))

    def test_lookup_disc_id_multidisc_by_discid(self):
        multidisc_response = {
            "releases": [
                {
                    "id": "mbid-wall-1979",
                    "title": "The Wall",
                    "date": "1979-11-30",
                    "artist-credit": [{"name": "Pink Floyd"}],
                    "media": [
                        {
                            "position": 1,
                            "discs": [{"id": "disc_one_id"}],
                            "tracks": [
                                {"position": 1, "title": "In the Flesh?", "length": 196000},
                                {"position": 2, "title": "The Thin Ice", "length": 147000},
                            ],
                        },
                        {
                            "position": 2,
                            "discs": [{"id": "disc_two_id"}],
                            "tracks": [
                                {"position": 1, "title": "Hey You", "length": 280000},
                                {"position": 2, "title": "Is There Anybody Out There?", "length": 164000},
                            ],
                        },
                    ],
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = multidisc_response
        self.mock_session.get.return_value = mock_resp

        results = self.client.lookup_disc_id("disc_two_id")
        self.assertEqual(len(results), 1)
        album = results[0]
        self.assertEqual(album.title, "The Wall")
        self.assertEqual(album.disc_number, 2)
        self.assertEqual(album.total_discs, 2)
        self.assertEqual(len(album.tracks), 2)
        self.assertEqual(album.tracks[0].title, "Hey You")
        self.assertEqual(album.tracks[0].disc_number, 2)

    def test_lookup_disc_id_multidisc_by_track_count(self):
        multidisc_response = {
            "releases": [
                {
                    "id": "mbid-boxset-999",
                    "title": "Anthology",
                    "date": "2000",
                    "artist-credit": [{"name": "The Band"}],
                    "media": [
                        {
                            "position": 1,
                            "track-count": 2,
                            "tracks": [
                                {"position": 1, "title": "Song 1"},
                                {"position": 2, "title": "Song 2"},
                            ],
                        },
                        {
                            "position": 2,
                            "track-count": 3,
                            "tracks": [
                                {"position": 1, "title": "Song 3"},
                                {"position": 2, "title": "Song 4"},
                                {"position": 3, "title": "Song 5"},
                            ],
                        },
                    ],
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = multidisc_response
        self.mock_session.get.return_value = mock_resp

        results = self.client.lookup_disc_id("-", expected_track_count=3)
        self.assertEqual(len(results), 1)
        album = results[0]
        self.assertEqual(album.disc_number, 2)
        self.assertEqual(album.total_discs, 2)
        self.assertEqual(len(album.tracks), 3)
        self.assertEqual(album.tracks[0].title, "Song 3")


class TestCoverArtClient(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.client = CoverArtClient(session=self.mock_session)

    def test_get_artwork_candidates_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_CAA_RESPONSE
        self.mock_session.get.return_value = mock_resp

        candidates = self.client.get_artwork_candidates("mbid-release-12345")

        self.assertEqual(len(candidates), 2)
        # Front cover should be ranked first
        top_art = candidates[0]
        self.assertTrue(top_art.is_front)
        self.assertEqual(top_art.image_id, "1001")
        self.assertEqual(top_art.thumbnail_url, "https://coverartarchive.org/release/mbid-release-12345/1001-500.jpg")
        self.assertEqual(top_art.width, 1200)

    def test_get_artwork_candidates_not_found(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        self.mock_session.get.return_value = mock_resp

        candidates = self.client.get_artwork_candidates("non_existent_mbid")
        self.assertEqual(candidates, [])

    @patch("time.sleep", return_value=None)
    def test_fetch_manifest_retries_on_500_and_succeeds(self, mock_sleep):
        mock_500 = MagicMock()
        mock_500.status_code = 500
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = MOCK_CAA_RESPONSE

        self.mock_session.get.side_effect = [mock_500, mock_200]
        candidates = self.client.get_artwork_candidates("mbid-flaky-archive-org")

        self.assertEqual(len(candidates), 2)
        self.assertEqual(self.mock_session.get.call_count, 2)
        mock_sleep.assert_called_once_with(0.8)

    @patch("time.sleep", return_value=None)
    def test_get_artwork_candidates_manifest_502_falls_back_to_direct_front_probe(self, mock_sleep):
        import requests
        # Manifest requests repeatedly fail with 502 Bad Gateway
        mock_502 = MagicMock()
        mock_502.status_code = 502
        mock_502.raise_for_status.side_effect = requests.HTTPError("502 Server Error: Bad Gateway")
        self.mock_session.get.return_value = mock_502

        # Direct /front probe returns 307 redirect directly to the image
        mock_307 = MagicMock()
        mock_307.status_code = 307
        mock_307.headers = {
            "Location": "https://archive.org/download/mbid-test-id/mbid-test-id-35431399103.jpg"
        }
        self.mock_session.head.return_value = mock_307

        candidates = self.client.get_artwork_candidates("mbid-test-id")

        self.assertEqual(len(candidates), 1)
        cand = candidates[0]
        self.assertTrue(cand.is_front)
        self.assertEqual(cand.image_id, "35431399103")
        self.assertEqual(cand.url, "https://archive.org/download/mbid-test-id/mbid-test-id-35431399103.jpg")
        self.assertEqual(cand.thumbnail_url, "https://coverartarchive.org/release/mbid-test-id/front-500")
        self.assertEqual(cand.source, "release")
        self.mock_session.head.assert_called_once_with(
            "https://coverartarchive.org/release/mbid-test-id/front",
            allow_redirects=False,
            timeout=6.0,
        )

    def test_probe_direct_front_404(self):
        mock_404 = MagicMock()
        mock_404.status_code = 404
        self.mock_session.head.return_value = mock_404

        candidates = self.client._probe_direct_front("https://coverartarchive.org/release", "mbid-404", "release")
        self.assertEqual(candidates, [])

    def test_artwork_priority_penalizes_scans_and_favors_newer_uploads(self):
        scan_cand = ArtworkCandidate(
            image_id="36012811899",
            url="http://example.com/scan.jpg",
            thumbnail_url="",
            is_front=True,
            width=1200,
            height=1200,
            source="release",
            types=["Front"],
            comment="digipak packaging scan",
        )
        digital_cand = ArtworkCandidate(
            image_id="38104822287",
            url="http://example.com/digital.jpg",
            thumbnail_url="",
            is_front=True,
            width=1200,
            height=1200,
            source="release",
            types=["Front"],
            comment="official digital artwork",
        )

        score_scan = CoverArtClient._artwork_priority_key(scan_cand)
        score_digital = CoverArtClient._artwork_priority_key(digital_cand)

        # Digital should vastly outrank scan
        self.assertGreater(score_digital, score_scan)

    def test_download_image_atomic_tmp_replace(self):
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "cover.jpg"
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.iter_content.return_value = [b"fake_jpeg_bytes"]
            self.mock_session.get.return_value.__enter__.return_value = mock_resp

            result = self.client.download_image("http://example.com/img.jpg", dest)
            self.assertEqual(result, dest)
            self.assertTrue(dest.exists())
            self.assertEqual(dest.read_bytes(), b"fake_jpeg_bytes")
            # Ensure .tmp file is cleaned up / replaced
            self.assertFalse(dest.with_suffix(".tmp").exists())



class TestMetadataService(unittest.TestCase):
    def setUp(self):
        self.mock_mb = MagicMock(spec=MusicBrainzClient)
        self.mock_caa = MagicMock(spec=CoverArtClient)
        self.mock_caa.session = MagicMock()
        self.service = MetadataService(
            mb_client=self.mock_mb,
            caa_client=self.mock_caa,
        )

    def test_resolve_album_metadata_by_disc_id(self):
        # Setup mock album from MB
        mock_album = MagicMock()
        mock_album.musicbrainz_release_id = "mbid-123"
        self.mock_mb.lookup_disc_id.return_value = [mock_album]

        # Setup mock artwork candidate
        mock_candidate = ArtworkCandidate(
            image_id="1",
            url="https://example.com/cover.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            is_front=True,
        )
        self.mock_caa.get_artwork_candidates.return_value = [mock_candidate]

        result = self.service.resolve_album_metadata(disc_id="valid_disc_id")

        self.assertIsNotNone(result)
        self.assertEqual(result.artwork_candidates, [mock_candidate])
        self.assertEqual(result.selected_artwork, mock_candidate)

    def test_resolve_album_metadata_fallback_to_text(self):
        # DiscID returns empty
        self.mock_mb.lookup_disc_id.return_value = []

        mock_album = MagicMock()
        mock_album.musicbrainz_release_id = "mbid-456"
        self.mock_mb.search_by_text.return_value = [mock_album]
        self.mock_caa.get_artwork_candidates.return_value = []

        result = self.service.resolve_album_metadata(
            disc_id="missing_disc",
            artist="Led Zeppelin",
            album_title="IV",
        )

        self.assertIsNotNone(result)
        self.mock_mb.search_by_text.assert_called_once_with("Led Zeppelin", "IV")

    def test_cache_selected_artwork(self):
        from pathlib import Path
        import tempfile

        mock_candidate = ArtworkCandidate(
            image_id="42",
            url="https://example.com/cover42.jpg",
            thumbnail_url="https://example.com/thumb42.jpg",
            is_front=True,
        )
        mock_album = MagicMock()
        mock_album.musicbrainz_release_id = "release-abc"
        mock_album.selected_artwork = mock_candidate

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir)
            expected_target = dest / "release-abc_42.jpg"
            self.mock_caa.download_image.return_value = expected_target

            cached = self.service.cache_selected_artwork(mock_album, destination_dir=dest)
            self.assertEqual(cached, expected_target)
            self.assertEqual(mock_album.selected_artwork.local_cache_path, expected_target)
            self.mock_caa.download_image.assert_called_once_with("https://example.com/cover42.jpg", expected_target)

    def test_artwork_aggregation_with_release_group(self):
        # Candidate 1: Deluxe release with booklet scan
        album_deluxe = MagicMock()
        album_deluxe.musicbrainz_release_id = "mbid-deluxe"
        album_deluxe.musicbrainz_release_group_id = "rg-mule"

        # Candidate 2: Standard release
        album_standard = MagicMock()
        album_standard.musicbrainz_release_id = "mbid-standard"
        album_standard.musicbrainz_release_group_id = "rg-mule"

        self.mock_mb.lookup_disc_id.return_value = [album_deluxe, album_standard]
        self.mock_mb.get_release_group_releases.return_value = ["mbid-deluxe", "mbid-standard"]

        # Canonical artwork from release-group
        canonical_art = ArtworkCandidate(
            image_id="38104822287",
            url="https://example.com/rg_cover.jpg",
            thumbnail_url="https://example.com/rg_thumb.jpg",
            is_front=True,
            width=1500,
            height=1500,
            source="release_group",
        )
        self.mock_caa.get_release_group_artwork.return_value = [canonical_art]

        # Scan artwork from deluxe release
        scan_art = ArtworkCandidate(
            image_id="36012811899",
            url="https://example.com/scan.jpg",
            thumbnail_url="https://example.com/scan_thumb.jpg",
            is_front=True,
            width=599,
            height=536,
            source="release",
        )
        self.mock_caa.get_artwork_candidates.side_effect = lambda rid: (
            [scan_art] if rid == "mbid-deluxe" else [canonical_art]
        )

        result = self.service.resolve_album_metadata(disc_id="test_mule_discid")

        self.assertIsNotNone(result)
        # Should have both unique candidates (canonical deduplicated)
        self.assertEqual(len(result.artwork_candidates), 2)
        # Canonical high-res release-group front must be ranked #1
        self.assertEqual(result.artwork_candidates[0].image_id, "38104822287")
        self.assertEqual(result.selected_artwork.image_id, "38104822287")

    @patch("lazycdripper.metadata.service.get_external_artwork_candidates")
    def test_artwork_fallback_to_external_when_caa_empty(self, mock_get_ext):
        mock_album = MagicMock()
        mock_album.musicbrainz_release_id = "mbid-rare-cd"
        mock_album.musicbrainz_release_group_id = None
        mock_album.artist = "Gov't Mule"
        mock_album.title = "Peace... Like a River"
        self.mock_mb.lookup_disc_id.return_value = [mock_album]

        # CAA returns no artwork
        self.mock_caa.get_artwork_candidates.return_value = []
        self.mock_caa.get_release_group_artwork.return_value = []

        # External fallback returns Apple/iTunes candidate
        ext_cand = ArtworkCandidate(
            image_id="itunes_999",
            url="https://is1-ssl.mzstatic.com/image/thumb/1200x1200bb.jpg",
            thumbnail_url="https://is1-ssl.mzstatic.com/image/thumb/600x600bb.jpg",
            is_front=True,
            source="itunes",
        )
        mock_get_ext.return_value = [ext_cand]

        result = self.service.resolve_album_metadata(disc_id="rare_disc_id")
        self.assertIsNotNone(result)
        self.assertEqual(len(result.artwork_candidates), 1)
        self.assertEqual(result.selected_artwork.image_id, "itunes_999")
        self.assertEqual(result.selected_artwork.source, "itunes")
        mock_get_ext.assert_called_once_with("Gov't Mule", "Peace... Like a River", session=self.mock_caa.session)

    def test_cache_selected_artwork_recovers_via_alternative_candidate(self):
        from pathlib import Path
        import tempfile

        primary_cand = ArtworkCandidate(
            image_id="primary_bad",
            url="https://archive.org/download/bad_502.jpg",
            is_front=True,
        )
        alt_cand = ArtworkCandidate(
            image_id="alt_good",
            url="https://is1-ssl.mzstatic.com/image/good.jpg",
            is_front=True,
        )
        mock_album = MagicMock()
        mock_album.musicbrainz_release_id = "rel-123"
        mock_album.selected_artwork = primary_cand
        mock_album.artwork_candidates = [primary_cand, alt_cand]

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir)
            good_target = dest / "rel-123_alt_good.jpg"

            # Primary fails (returns None), alternative succeeds
            self.mock_caa.download_image.side_effect = [None, good_target]

            cached = self.service.cache_selected_artwork(mock_album, destination_dir=dest)
            self.assertEqual(cached, good_target)
            self.assertEqual(mock_album.selected_artwork, alt_cand)

    def test_candidate_ranking_single_disc_preference(self):
        deluxe = AlbumInfo(
            title="Peace",
            artist="Gov't Mule",
            album_artist="Gov't Mule",
            year=2023,
            total_tracks=12,
            disc_number=1,
            total_discs=2,
            musicbrainz_release_id="mbid-2disc",
        )
        standard = AlbumInfo(
            title="Peace",
            artist="Gov't Mule",
            album_artist="Gov't Mule",
            year=2023,
            total_tracks=12,
            disc_number=1,
            total_discs=1,
            musicbrainz_release_id="mbid-1disc",
        )

        rank_deluxe = MusicBrainzClient._rank_album_candidate(deluxe, expected_track_count=12)
        rank_standard = MusicBrainzClient._rank_album_candidate(standard, expected_track_count=12)

        # Standard 1-disc release should have higher rank than 2-disc release
        self.assertGreater(rank_standard, rank_deluxe)

    def test_cover_art_priority_canonical_over_scan(self):
        canonical = ArtworkCandidate(
            image_id="1",
            url="http://example.com/1.jpg",
            thumbnail_url="http://example.com/1_t.jpg",
            is_front=True,
            width=1500,
            height=1500,
            source="release_group",
            types=["Front"],
        )
        scan = ArtworkCandidate(
            image_id="2",
            url="http://example.com/2.jpg",
            thumbnail_url="http://example.com/2_t.jpg",
            is_front=True,
            width=599,
            height=536,
            source="release",
            types=["Front"],
        )
        back = ArtworkCandidate(
            image_id="3",
            url="http://example.com/3.jpg",
            thumbnail_url="http://example.com/3_t.jpg",
            is_front=False,
            types=["Back"],
        )

        score_canonical = CoverArtClient._artwork_priority_key(canonical)
        score_scan = CoverArtClient._artwork_priority_key(scan)
        score_back = CoverArtClient._artwork_priority_key(back)

        self.assertGreater(score_canonical, score_scan)
        self.assertGreater(score_scan, score_back)

    def test_user_agent_format(self):
        from lazycdripper import __version__
        from lazycdripper.metadata.musicbrainz import USER_AGENT as MB_UA
        from lazycdripper.metadata.coverart import USER_AGENT as CAA_UA

        self.assertEqual(MB_UA, f"LazyCDRipper/{__version__} ( lazyhead@fastmail.com )")
        self.assertEqual(CAA_UA, f"LazyCDRipper/{__version__} ( lazyhead@fastmail.com )")


if __name__ == "__main__":
    unittest.main()
