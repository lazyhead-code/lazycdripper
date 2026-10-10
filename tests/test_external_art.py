"""Unit tests for the external artwork fallback service (iTunes and Deezer)."""

import unittest
from unittest.mock import MagicMock
from lazycdripper.metadata.external_art import (
    _clean_title,
    _titles_match,
    get_external_artwork_candidates,
    search_deezer_artwork,
    search_itunes_artwork,
)


class TestExternalArtwork(unittest.TestCase):
    def test_clean_title(self):
        self.assertEqual(_clean_title("Peace... Like a River"), "peace like a river")
        self.assertEqual(
            _clean_title("The Dark Side of the Moon (2023 Remaster)"),
            "the dark side of the moon",
        )
        self.assertEqual(
            _clean_title("OK Computer [Collector's Edition]"),
            "ok computer",
        )

    def test_titles_match(self):
        self.assertTrue(_titles_match("Peace... Like a River", "Peace...Like A River"))
        self.assertTrue(
            _titles_match(
                "The Dark Side of the Moon",
                "The Dark Side Of The Moon (Live at Wembley)",
            )
        )
        self.assertTrue(_titles_match("Back in Black", "Back In Black (Remastered)"))
        self.assertFalse(_titles_match("The Dark Side of the Moon", "The Wall"))
        self.assertFalse(_titles_match("", "Some Album"))

    def test_search_itunes_artwork_success(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "resultCount": 1,
            "results": [
                {
                    "collectionId": 123456,
                    "collectionName": "Peace...Like A River",
                    "artistName": "Gov't Mule",
                    "artworkUrl100": "https://is1-ssl.mzstatic.com/image/thumb/abc/100x100bb.jpg",
                }
            ],
        }
        mock_session.get.return_value = mock_resp

        candidates = search_itunes_artwork("Gov't Mule", "Peace... Like a River", session=mock_session)
        self.assertEqual(len(candidates), 1)
        c = candidates[0]
        self.assertEqual(c.image_id, "itunes_123456")
        self.assertEqual(c.url, "https://is1-ssl.mzstatic.com/image/thumb/abc/1200x1200bb.jpg")
        self.assertEqual(c.thumbnail_url, "https://is1-ssl.mzstatic.com/image/thumb/abc/600x600bb.jpg")
        self.assertEqual(c.width, 1200)
        self.assertEqual(c.height, 1200)
        self.assertTrue(c.is_front)
        self.assertEqual(c.source, "itunes")

    def test_search_itunes_artwork_ignores_unmatched_album(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "resultCount": 1,
            "results": [
                {
                    "collectionId": 999,
                    "collectionName": "Totally Different Album",
                    "artworkUrl100": "https://is1-ssl.mzstatic.com/image/thumb/xyz/100x100bb.jpg",
                }
            ],
        }
        mock_session.get.return_value = mock_resp

        candidates = search_itunes_artwork("Pink Floyd", "The Dark Side of the Moon", session=mock_session)
        self.assertEqual(candidates, [])

    def test_search_deezer_artwork_success(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {
                    "id": 7890,
                    "title": "Peace... Like a River",
                    "cover_xl": "https://cdn-images.dzcdn.net/images/cover/xl.jpg",
                    "cover_big": "https://cdn-images.dzcdn.net/images/cover/big.jpg",
                }
            ]
        }
        mock_session.get.return_value = mock_resp

        candidates = search_deezer_artwork("Gov't Mule", "Peace... Like a River", session=mock_session)
        self.assertEqual(len(candidates), 1)
        c = candidates[0]
        self.assertEqual(c.image_id, "deezer_7890")
        self.assertEqual(c.url, "https://cdn-images.dzcdn.net/images/cover/xl.jpg")
        self.assertEqual(c.thumbnail_url, "https://cdn-images.dzcdn.net/images/cover/big.jpg")
        self.assertEqual(c.width, 1000)
        self.assertEqual(c.source, "deezer")

    def test_get_external_artwork_candidates_priority(self):
        mock_session = MagicMock()
        mock_itunes_resp = MagicMock()
        mock_itunes_resp.status_code = 200
        mock_itunes_resp.json.return_value = {
            "resultCount": 1,
            "results": [
                {
                    "collectionId": 111,
                    "collectionName": "Album One",
                    "artworkUrl100": "https://is1-ssl.mzstatic.com/image/thumb/111/100x100bb.jpg",
                }
            ],
        }
        mock_session.get.return_value = mock_itunes_resp

        results = get_external_artwork_candidates("Artist", "Album One", session=mock_session)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source, "itunes")


if __name__ == "__main__":
    unittest.main()
