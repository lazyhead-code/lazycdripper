"""MusicBrainz API client for disc identification and release metadata fetching."""

import logging
import re
import time
from typing import Any, Dict, List, Optional
import requests
from lazycdripper import __version__
from lazycdripper.core.models import AlbumInfo, TrackInfo

logger = logging.getLogger(__name__)

USER_AGENT = f"LazyCDRipper/{__version__} ( lazyhead@fastmail.com )"
BASE_URL = "https://musicbrainz.org/ws/2"


class MusicBrainzClient:
    """Client for interacting with the MusicBrainz JSON Web Service (WS2)."""

    def __init__(self, session: Optional[requests.Session] = None, user_agent: str = USER_AGENT):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})

    def lookup_disc_id(
        self,
        disc_id: str,
        toc: Optional[str] = None,
        expected_track_count: Optional[int] = None,
    ) -> List[AlbumInfo]:
        """
        Query MusicBrainz for releases matching a 28-character DiscID.
        If toc string is provided, MusicBrainz performs exact DiscID lookup
        and automatically falls back to fuzzy TOC matching if the exact DiscID is not attached.
        """
        url = f"{BASE_URL}/discid/{disc_id}"
        params = {
            "fmt": "json",
            "inc": "recordings+artist-credits+genres+release-groups",
        }
        if toc:
            params["toc"] = toc

        data = None
        for attempt in range(2):
            try:
                response = self.session.get(url, params=params, timeout=10.0)
                if response.status_code == 404:
                    logger.info("DiscID %s not found in MusicBrainz database", disc_id)
                    return []
                if response.status_code == 503 and attempt == 0:
                    logger.info("MusicBrainz rate-limited (503); pausing 1.2s before retry...")
                    time.sleep(1.2)
                    continue
                response.raise_for_status()
                data = response.json()
                break
            except requests.RequestException as err:
                if attempt == 0 and hasattr(err, "response") and err.response is not None and err.response.status_code == 503:
                    time.sleep(1.2)
                    continue
                logger.error("Failed to query MusicBrainz for DiscID %s: %s", disc_id, err)
                return []

        if not data:
            return []

        releases = data.get("releases", [])
        results: List[AlbumInfo] = []
        for release_data in releases:
            album = self._parse_release(
                release_data,
                default_disc_id=disc_id,
                expected_track_count=expected_track_count,
            )
            if album:
                results.append(album)

        if results and expected_track_count:
            results.sort(
                key=lambda a: self._rank_album_candidate(a, expected_track_count),
                reverse=True,
            )

        return results

    def lookup_by_toc(
        self,
        toc: str,
        expected_track_count: Optional[int] = None,
    ) -> List[AlbumInfo]:
        """
        Query MusicBrainz using fuzzy TOC matching directly ('/ws/2/discid/-?toc=...').
        Used when the exact DiscID yields 0 results or to find alternative pressings.
        """
        return self.lookup_disc_id("-", toc=toc, expected_track_count=expected_track_count)

    def search_by_text(
        self,
        artist: str,
        album: str,
        expected_track_count: Optional[int] = None,
    ) -> List[AlbumInfo]:
        """
        Fallback search for an album using artist and album title keywords.
        """
        clean_artist = artist.strip()
        clean_album = album.strip()
        query = f'artist:"{clean_artist}" AND release:"{clean_album}"'

        url = f"{BASE_URL}/release"
        params = {
            "query": query,
            "fmt": "json",
            "limit": 5,
        }

        try:
            response = self.session.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as err:
            logger.error("Failed to search MusicBrainz for %s - %s: %s", artist, album, err)
            return []

        releases = data.get("releases", [])
        results: List[AlbumInfo] = []
        for item in releases:
            # Need full recordings detail for each release
            rel_id = item.get("id")
            if rel_id:
                detailed = self.get_release_by_id(
                    rel_id,
                    expected_track_count=expected_track_count,
                )
                if detailed:
                    results.append(detailed)
        return results

    def get_release_by_id(
        self,
        release_id: str,
        default_disc_id: str = "",
        expected_track_count: Optional[int] = None,
    ) -> Optional[AlbumInfo]:
        """
        Fetch full release details, tracklist, and media info for a given MusicBrainz Release ID (MBID).
        """
        url = f"{BASE_URL}/release/{release_id}"
        params = {
            "fmt": "json",
            "inc": "recordings+artist-credits+genres+release-groups+media+discids",
        }

        try:
            response = self.session.get(url, params=params, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            return self._parse_release(
                data,
                default_disc_id=default_disc_id,
                expected_track_count=expected_track_count,
            )
        except requests.RequestException as err:
            logger.error("Failed to fetch release %s: %s", release_id, err)
            return None

    def _parse_release(
        self,
        data: Dict[str, Any],
        default_disc_id: str = "",
        expected_track_count: Optional[int] = None,
    ) -> Optional[AlbumInfo]:
        """Parse a MusicBrainz release JSON payload into our AlbumInfo domain model."""
        release_id = data.get("id", "")
        title = data.get("title", "Unknown Album")

        # Parse artist credit
        artist_credits = data.get("artist-credit", [])
        artist_name = self._format_artist_credits(artist_credits) or "Unknown Artist"

        # Parse release year
        year = self._parse_year(data.get("date"))

        # Parse media / discs
        media_list = data.get("media", [])
        total_discs = len(media_list) or 1

        # Match specific medium for multi-disc releases
        chosen_medium: Optional[Dict[str, Any]] = None
        if len(media_list) > 1:
            # 1. Match by DiscID if physical disc has an attached DiscID
            if default_disc_id and default_disc_id != "-":
                for medium in media_list:
                    discs = medium.get("discs", [])
                    for d in discs:
                        if d.get("id") == default_disc_id:
                            chosen_medium = medium
                            break
                    if chosen_medium:
                        break

            # 2. Match by track count if TOC track count is known
            if not chosen_medium and expected_track_count:
                candidates = [
                    m for m in media_list
                    if m.get("track-count") == expected_track_count or len(m.get("tracks", [])) == expected_track_count
                ]
                if len(candidates) == 1:
                    chosen_medium = candidates[0]

            # 3. Fallback to first medium if undetermined
            if not chosen_medium and media_list:
                chosen_medium = media_list[0]
        elif media_list:
            chosen_medium = media_list[0]

        disc_number = int(chosen_medium.get("position", 1)) if chosen_medium else 1

        # Determine genre
        genres = data.get("genres", [])
        primary_genre = genres[0].get("name") if genres else None

        # Build tracks strictly for the selected physical disc / medium
        tracks: List[TrackInfo] = []
        target_media = [chosen_medium] if chosen_medium else media_list

        for medium in target_media:
            disc_tracks = medium.get("tracks", [])
            for track_data in disc_tracks:
                pos = track_data.get("position", len(tracks) + 1)
                t_title = track_data.get("title") or track_data.get("recording", {}).get("title", f"Track {pos}")

                # Track artist credit (fallback to album artist if identical)
                t_artist_credits = track_data.get("artist-credit", [])
                t_artist = self._format_artist_credits(t_artist_credits) or artist_name

                # Length in milliseconds -> seconds
                length_ms = track_data.get("length") or track_data.get("recording", {}).get("length", 0)
                duration = float(length_ms) / 1000.0 if length_ms else 0.0

                tracks.append(
                    TrackInfo(
                        track_number=int(pos),
                        title=t_title,
                        artist=t_artist,
                        duration_seconds=duration,
                        disc_number=disc_number,
                        genre=primary_genre,
                    )
                )

        # Parse release group
        release_group = data.get("release-group") or {}
        release_group_id = release_group.get("id")

        return AlbumInfo(
            title=title,
            artist=artist_name,
            album_artist=artist_name,
            year=year,
            total_tracks=len(tracks),
            disc_number=disc_number,
            total_discs=total_discs,
            disc_id=default_disc_id,
            musicbrainz_release_id=release_id,
            musicbrainz_release_group_id=release_group_id,
            genre=primary_genre,
            tracks=tracks,
        )

    def get_release_group_releases(self, release_group_id: str, limit: int = 5) -> List[str]:
        """
        Fetch release IDs associated with a MusicBrainz Release Group ID.
        Used to aggregate cover art candidates across all pressings of an album.
        """
        if not release_group_id:
            return []
        url = f"{BASE_URL}/release-group/{release_group_id}"
        params = {"inc": "releases", "fmt": "json"}
        try:
            response = self.session.get(url, params=params, timeout=10.0)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            releases = data.get("releases", [])
            # Prioritize Official releases with earliest dates
            def _rel_sort_key(r: Dict[str, Any]) -> tuple:
                is_official = 1 if r.get("status") == "Official" else 0
                date = str(r.get("date") or "9999")
                return (is_official, -len(date), date)
            releases.sort(key=_rel_sort_key, reverse=True)
            return [r.get("id") for r in releases if r.get("id")][:limit]
        except requests.RequestException as err:
            logger.warning("Failed to fetch releases for release group %s: %s", release_group_id, err)
            return []

    @staticmethod
    def _rank_album_candidate(album: AlbumInfo, expected_track_count: Optional[int] = None) -> tuple:
        """
        Ranking key for ordering release candidates:
        1. Exact match on track count (1 if matched, 0 otherwise)
        2. Single disc preference if disc_number is 1 (prefer 1-disc standard releases over multi-disc sets)
        3. Has release year
        """
        track_match = 1 if (expected_track_count and album.total_tracks == expected_track_count) else 0
        single_disc = 1 if (album.disc_number == 1 and album.total_discs == 1) else 0
        has_year = 1 if album.year else 0
        return (track_match, single_disc, has_year)

    @staticmethod
    def _format_artist_credits(credits: List[Dict[str, Any]]) -> str:
        """Combine artist credit list into a single human-readable name string."""
        if not credits:
            return ""
        parts = []
        for credit in credits:
            name = credit.get("name") or credit.get("artist", {}).get("name", "")
            joinphrase = credit.get("joinphrase", "")
            parts.append(f"{name}{joinphrase}")
        return "".join(parts).strip()

    @staticmethod
    def _parse_year(date_str: Optional[str]) -> Optional[int]:
        """Extract a 4-digit year from date strings like '1973-03-01' or '1973'."""
        if not date_str:
            return None
        match = re.search(r"\b(19\d\d|20\d\d)\b", str(date_str))
        if match:
            return int(match.group(1))
        return None
