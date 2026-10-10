"""Public external cover artwork resolvers (Apple iTunes and Deezer fallback services).

Provides high-availability, high-resolution album artwork when Cover Art Archive
manifests or Internet Archive storage servers experience gateway outages (e.g. 502 Bad Gateway)
or when MusicBrainz has no user-contributed artwork uploaded for a pressing.
"""

import difflib
import logging
import re
from typing import List, Optional
import urllib.parse
import requests
from lazycdripper import __version__
from lazycdripper.core.models import ArtworkCandidate

logger = logging.getLogger(__name__)

USER_AGENT = f"LazyCDRipper/{__version__} ( lazyhead@fastmail.com )"
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
DEEZER_SEARCH_URL = "https://api.deezer.com/search/album"


def _clean_title(text: str) -> str:
    """Normalize album or artist title for fuzzy matching."""
    if not text:
        return ""
    # Strip parenthesized or bracketed qualifiers like (Remastered), [Deluxe Edition]
    text = re.sub(r"[\(\[\{].*?[\)\]\}]", "", text)
    # Strip punctuation and collapse whitespace
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.lower().split())


def _titles_match(query: str, candidate: str) -> bool:
    """Determine if a queried album title reasonably matches a candidate result."""
    q = _clean_title(query)
    c = _clean_title(candidate)
    if not q or not c:
        return False
    if q == c or q in c or c in q:
        return True
    ratio = difflib.SequenceMatcher(None, q, c).ratio()
    return ratio >= 0.72


def search_itunes_artwork(
    artist: str,
    album_title: str,
    session: Optional[requests.Session] = None,
    timeout: float = 5.0,
) -> List[ArtworkCandidate]:
    """
    Query Apple iTunes Search API for official high-resolution album artwork.
    No authentication required. Images are hosted on Apple's global mzstatic CDN.
    """
    if not artist or not album_title or artist.lower() in ("unknown", "unknown artist"):
        return []

    client = session or requests
    query = f"{artist} {album_title}"
    params = {
        "term": query,
        "entity": "album",
        "limit": 4,
    }
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    try:
        resp = client.get(ITUNES_SEARCH_URL, params=params, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception as err:
        logger.debug("iTunes artwork search error for '%s - %s': %s", artist, album_title, err)
        return []

    candidates: List[ArtworkCandidate] = []
    for item in data.get("results", []):
        cand_title = item.get("collectionName", "")
        if not _titles_match(album_title, cand_title):
            continue

        raw_art = item.get("artworkUrl100", "")
        if not raw_art:
            continue

        # Apple CDN dynamically scales images by replacing dimensions in the URL
        hi_res_url = raw_art.replace("100x100bb", "1200x1200bb")
        thumb_url = raw_art.replace("100x100bb", "600x600bb")
        collection_id = str(item.get("collectionId", "itunes"))

        candidate = ArtworkCandidate(
            image_id=f"itunes_{collection_id}",
            url=hi_res_url,
            thumbnail_url=thumb_url,
            is_front=True,
            width=1200,
            height=1200,
            comment=f"Apple Music / iTunes ({cand_title})",
            types=["Front"],
            source="itunes",
        )
        candidates.append(candidate)
        break  # Primary match is sufficient

    return candidates


def search_deezer_artwork(
    artist: str,
    album_title: str,
    session: Optional[requests.Session] = None,
    timeout: float = 5.0,
) -> List[ArtworkCandidate]:
    """
    Query Deezer public search API for official high-resolution album artwork.
    No authentication required. Images are hosted on Deezer's dzcdn CDN.
    """
    if not artist or not album_title or artist.lower() in ("unknown", "unknown artist"):
        return []

    client = session or requests
    query = f"{artist} {album_title}"
    url = f"{DEEZER_SEARCH_URL}?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    try:
        resp = client.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception as err:
        logger.debug("Deezer artwork search error for '%s - %s': %s", artist, album_title, err)
        return []

    candidates: List[ArtworkCandidate] = []
    for item in data.get("data", []):
        cand_title = item.get("title", "")
        if not _titles_match(album_title, cand_title):
            continue

        # Deezer provides cover_xl (1000x1000) and cover_big (500x500)
        cover_url = item.get("cover_xl") or item.get("cover_big")
        thumb_url = item.get("cover_big") or item.get("cover_medium") or cover_url
        if not cover_url:
            continue

        album_id = str(item.get("id", "deezer"))
        candidate = ArtworkCandidate(
            image_id=f"deezer_{album_id}",
            url=cover_url,
            thumbnail_url=thumb_url,
            is_front=True,
            width=1000,
            height=1000,
            comment=f"Deezer Hi-Res ({cand_title})",
            types=["Front"],
            source="deezer",
        )
        candidates.append(candidate)
        break

    return candidates


def get_external_artwork_candidates(
    artist: str,
    album_title: str,
    session: Optional[requests.Session] = None,
) -> List[ArtworkCandidate]:
    """
    Query high-availability public CD cover art providers (iTunes and Deezer).
    Returns deduplicated front cover candidates.
    """
    results: List[ArtworkCandidate] = []
    # 1. Try iTunes (1200x1200px)
    itunes_results = search_itunes_artwork(artist, album_title, session=session)
    results.extend(itunes_results)

    # 2. Try Deezer (1000x1000px) if iTunes returned nothing
    if not results:
        deezer_results = search_deezer_artwork(artist, album_title, session=session)
        results.extend(deezer_results)

    return results
