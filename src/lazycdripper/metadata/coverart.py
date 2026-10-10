import logging
from pathlib import Path
import time
from typing import List, Optional
import requests
from lazycdripper import __version__
from lazycdripper.core.models import ArtworkCandidate

logger = logging.getLogger(__name__)

USER_AGENT = f"LazyCDRipper/{__version__} ( lazyhead@fastmail.com )"
CAA_RELEASE_URL = "https://coverartarchive.org/release"
CAA_RELEASE_GROUP_URL = "https://coverartarchive.org/release-group"


def get_image_dimensions(path: Path) -> Optional[tuple]:
    """Inspect JPEG or PNG file header to extract pixel dimensions without heavy libraries."""
    try:
        data = path.read_bytes()
        # Fast JPEG SOF marker parser
        i = 0
        while i < len(data) - 8:
            if data[i] == 0xFF:
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2):
                    import struct
                    h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                    return (w, h)
                elif marker not in (0xD8, 0xD9, 0x00, 0xFF):
                    import struct
                    length = struct.unpack(">H", data[i + 2 : i + 4])[0]
                    i += 2 + length
                    continue
            i += 1
        # Fast PNG parser
        if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
            import struct
            w, h = struct.unpack(">II", data[16:24])
            return (w, h)
    except Exception:
        pass
    return None


class CoverArtClient:
    """Client for the Cover Art Archive (coverartarchive.org) API."""

    def __init__(self, session: Optional[requests.Session] = None, user_agent: str = USER_AGENT):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})

    def get_artwork_candidates(self, release_id: str) -> List[ArtworkCandidate]:
        """
        Fetch all available artwork candidates for a given MusicBrainz Release ID.
        Filters for front covers and sorts by optimal quality.
        Falls back to direct /front endpoint probe if manifest is unavailable.
        """
        if not release_id:
            return []
        url = f"{CAA_RELEASE_URL}/{release_id}"
        candidates = self._fetch_manifest(url, source="release")
        if not candidates:
            candidates = self._probe_direct_front(CAA_RELEASE_URL, release_id, source="release")
        return candidates

    def get_release_group_artwork(self, release_group_id: str) -> List[ArtworkCandidate]:
        """
        Fetch canonical artwork candidates for a MusicBrainz Release Group ID.
        Release groups contain the community-curated primary album artwork.
        Falls back to direct /front endpoint probe if manifest is unavailable.
        """
        if not release_group_id:
            return []
        url = f"{CAA_RELEASE_GROUP_URL}/{release_group_id}"
        candidates = self._fetch_manifest(url, source="release_group")
        if not candidates:
            candidates = self._probe_direct_front(CAA_RELEASE_GROUP_URL, release_group_id, source="release_group")
        return candidates

    def _probe_direct_front(self, base_url: str, mbid: str, source: str) -> List[ArtworkCandidate]:
        """
        Probe direct Cover Art Archive front endpoint (e.g. /release/{mbid}/front)
        via HTTP HEAD with redirect following disabled.
        When Archive.org's index.json manifest is down (e.g. 502 Bad Gateway),
        coverartarchive.org itself responds with a 307 redirect directly to the static image.
        """
        if not mbid:
            return []
        url = f"{base_url}/{mbid}/front"
        for attempt in range(2):
            try:
                resp = self.session.head(url, allow_redirects=False, timeout=6.0)
                if resp.status_code in (301, 302, 303, 307, 308):
                    target_url = resp.headers.get("Location")
                    if target_url:
                        image_id = None
                        try:
                            filename = target_url.rsplit("/", 1)[-1]
                            stem = filename.split(".", 1)[0]
                            parts = stem.split("-")
                            if parts and parts[-1].isdigit():
                                image_id = parts[-1]
                        except Exception:
                            pass
                        if not image_id:
                            image_id = f"{source}_{mbid[:8]}_front"

                        thumb_url = f"{base_url}/{mbid}/front-500"
                        logger.info("Direct front cover discovered for %s: %s", mbid, target_url)
                        return [
                            ArtworkCandidate(
                                image_id=image_id,
                                url=target_url,
                                thumbnail_url=thumb_url,
                                is_front=True,
                                width=1200,
                                height=1200,
                                comment="Direct Cover Art Archive Front",
                                types=["Front"],
                                source=source,
                            )
                        ]
                elif resp.status_code == 200:
                    return [
                        ArtworkCandidate(
                            image_id=f"{source}_{mbid[:8]}_front",
                            url=url,
                            thumbnail_url=f"{base_url}/{mbid}/front-500",
                            is_front=True,
                            width=1200,
                            height=1200,
                            comment="Direct Cover Art Archive Front",
                            types=["Front"],
                            source=source,
                        )
                    ]
                elif resp.status_code == 404:
                    return []
            except requests.RequestException as err:
                logger.debug("Direct front probe failed for %s (attempt %d): %s", url, attempt + 1, err)
                if attempt == 0:
                    time.sleep(0.5)
        return []

    def _fetch_manifest(self, url: str, source: str = "release") -> List[ArtworkCandidate]:
        """Query Cover Art Archive JSON manifest and convert items to ArtworkCandidate instances.
        Includes exponential backoff retries on transient network and archive.org gateway errors.
        """
        data = None
        for attempt in range(3):
            try:
                response = self.session.get(url, timeout=12.0)
                if response.status_code == 404:
                    logger.info("No cover art found at %s", url)
                    return []
                if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                    logger.debug(
                        "CAA transient status %d on %s; retry in %.1fs (attempt %d/3)",
                        response.status_code,
                        url,
                        0.8 * (attempt + 1),
                        attempt + 1,
                    )
                    time.sleep(0.8 * (attempt + 1))
                    continue
                response.raise_for_status()
                data = response.json()
                break
            except requests.RequestException as err:
                if attempt < 2:
                    time.sleep(0.8 * (attempt + 1))
                    continue
                logger.info("Cover art manifest unavailable from %s (%s); will attempt fallback endpoints", url, err)
                return []

        if not data:
            return []

        images = data.get("images", [])
        candidates: List[ArtworkCandidate] = []

        for item in images:
            image_id = str(item.get("id", ""))
            image_url = item.get("image", "")
            types = item.get("types", [])
            is_front = bool(item.get("front") or "Front" in types)
            comment = item.get("comment", "")

            # Extract best thumbnail URL
            thumbnails = item.get("thumbnails", {})
            thumb_url = (
                thumbnails.get("500")
                or thumbnails.get("large")
                or thumbnails.get("250")
                or thumbnails.get("small")
                or image_url
            )

            # Cover Art Archive provides optional dimensions or thumbnail presence indicators
            width = item.get("width")
            height = item.get("height")
            if not width and "1200" in thumbnails:
                width = 1200
                height = 1200
            elif not width and "500" in thumbnails:
                width = 500
                height = 500

            candidate = ArtworkCandidate(
                image_id=image_id,
                url=image_url,
                thumbnail_url=thumb_url,
                is_front=is_front,
                width=width,
                height=height,
                comment=comment,
                types=types,
                source=source,
            )
            candidates.append(candidate)

        # Sort candidates: canonical front covers first, then high-res fronts, then non-front scans
        candidates.sort(key=self._artwork_priority_key, reverse=True)
        return candidates

    @staticmethod
    def _artwork_priority_key(candidate: ArtworkCandidate) -> float:
        """
        Heuristic score for ranking artwork candidates.
        Prioritizes:
        1. Canonical front cover from Release Group (+4000)
        2. Front covers (+2000)
        3. Dimensions / resolution if known (+100 to +400)
        4. Aspect ratio (square vs non-square) (+200)
        5. Negative penalty for physical packaging/scan keywords in comments (-300)
        6. Positive bonus for digital master keywords in comments (+200)
        7. Newer MusicBrainz upload preference (tie-breaker based on numeric image ID)
        8. Non-front categories sorted after Fronts (Back=500, Booklet=200, Medium=50)
        """
        score = 0.0
        if candidate.is_front:
            score += 2000.0
            if candidate.source == "release_group":
                score += 2000.0  # Dominant bonus for canonical Release Group artwork
            elif candidate.source in ("itunes", "deezer"):
                score -= 200.0  # High-res digital master fallback
            if "Front" in candidate.types:
                score += 100.0
        else:
            # Demote non-fronts below all front covers
            if "Back" in candidate.types:
                score += 500.0
            elif "Booklet" in candidate.types:
                score += 200.0
            elif "Medium" in candidate.types:
                score += 50.0
            elif "Spine" in candidate.types or "Tray" in candidate.types:
                score += 100.0

        # Thumbnail / resolution preference
        if candidate.width:
            if 900 <= candidate.width <= 2500:
                score += 400.0
            elif candidate.width > 2500:
                score += 200.0
            elif candidate.width >= 500:
                score += 100.0
            else:
                score -= 100.0

            if candidate.height:
                diff = abs(candidate.width - candidate.height)
                if diff == 0:
                    score += 200.0  # Perfect square
                elif diff / max(candidate.width, candidate.height) <= 0.05:
                    score += 100.0  # Near square
                else:
                    score -= 100.0  # Oblong scan

        # Keyword heuristics from comment (penalize scans, reward digital masters)
        comment_lower = (candidate.comment or "").lower()
        if any(w in comment_lower for w in ("scan", "flatbed", "photo", "camera", "phone", "packaging", "digipak")):
            score -= 300.0
        if any(w in comment_lower for w in ("digital", "master", "web", "promo", "official", "qobuz", "tidal", "apple", "itunes", "deezer")):
            score += 200.0

        # Tie-breaker: prefer newer uploads in MusicBrainz (higher image IDs are newer replacements)
        if candidate.image_id and candidate.image_id.isdigit():
            score += float(int(candidate.image_id)) / 100_000_000_000.0

        return score

    def download_image(self, url: str, destination_path: Path) -> Optional[Path]:
        """
        Download an artwork image stream to disk safely via temporary file.
        Includes retries on transient errors and ensures atomic file replacement.
        """
        tmp_dest = destination_path.with_suffix(".tmp")
        for attempt in range(3):
            try:
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                with self.session.get(url, stream=True, timeout=15.0) as resp:
                    if resp.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                        time.sleep(1.0)
                        continue
                    resp.raise_for_status()
                    with open(tmp_dest, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            if chunk:
                                f.write(chunk)
                tmp_dest.replace(destination_path)
                return destination_path
            except requests.RequestException as err:
                if attempt < 2:
                    time.sleep(1.0)
                    continue
                logger.warning("Failed to download artwork from %s: %s", url, err)
                if tmp_dest.exists():
                    try:
                        tmp_dest.unlink()
                    except OSError:
                        pass
                return None
