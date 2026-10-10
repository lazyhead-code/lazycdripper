"""High-level metadata coordinator service uniting MusicBrainz and Cover Art Archive."""

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, List, Optional
from lazycdripper.core.models import AlbumInfo, ArtworkCandidate
from lazycdripper.metadata.coverart import CoverArtClient, get_image_dimensions
from lazycdripper.metadata.external_art import get_external_artwork_candidates
from lazycdripper.metadata.musicbrainz import MusicBrainzClient

logger = logging.getLogger(__name__)


class MetadataService:
    """Coordinates metadata lookups and artwork candidate acquisition across MusicBrainz and CD-Text."""

    def __init__(
        self,
        mb_client: Optional[MusicBrainzClient] = None,
        caa_client: Optional[CoverArtClient] = None,
    ):
        self.mb_client = mb_client or MusicBrainzClient()
        self.caa_client = caa_client or CoverArtClient()

    def resolve_album_metadata(
        self,
        disc_id: Optional[str] = None,
        toc: Optional[Any] = None,
        artist: Optional[str] = None,
        album_title: Optional[str] = None,
    ) -> Optional[AlbumInfo]:
        """
        Identify and hydrate album metadata via MusicBrainz and Cover Art Archive:
        1. Attempt MusicBrainz exact DiscID + Fuzzy TOC lookup.
        2. Fall back to pure MusicBrainz fuzzy TOC matching.
        3. Fall back to text search if artist & album keywords are provided.
        4. Acquire and aggregate cover artwork candidates from Release Group and matching pressings.
        """
        candidates: List[AlbumInfo] = []
        toc_mb_str = getattr(toc, "musicbrainz_toc_string", None)
        expected_track_count = len(toc.tracks) if (toc and hasattr(toc, "tracks") and toc.tracks) else None

        # Tier 1: MusicBrainz Exact DiscID + Fuzzy TOC
        if disc_id:
            logger.info("Looking up album metadata by DiscID: %s (toc=%s)", disc_id, bool(toc_mb_str))
            candidates = self.mb_client.lookup_disc_id(
                disc_id,
                toc=toc_mb_str,
                expected_track_count=expected_track_count,
            )

        # Tier 2: MusicBrainz Pure Fuzzy TOC
        if not candidates and toc_mb_str:
            logger.info("Falling back to MusicBrainz pure fuzzy TOC lookup")
            candidates = self.mb_client.lookup_by_toc(
                toc_mb_str,
                expected_track_count=expected_track_count,
            )

        # Tier 3: Manual text search keywords
        if not candidates and artist and album_title:
            logger.info("Falling back to text search for '%s - %s'", artist, album_title)
            candidates = self.mb_client.search_by_text(artist, album_title)

        if not candidates:
            logger.warning("No metadata matches found in MusicBrainz")
            return None

        # Select primary candidate
        chosen_album = candidates[0]

        # Aggregate artwork candidates across the Release Group and candidate pressings
        art_candidates = self._fetch_aggregated_artwork(candidates)
        chosen_album.artwork_candidates = art_candidates

        # Auto-select the top-priority front cover and cache locally
        if art_candidates:
            chosen_album.selected_artwork = art_candidates[0]
            self.cache_selected_artwork(chosen_album)

        return chosen_album

    def _fetch_aggregated_artwork(self, candidates: List[AlbumInfo]) -> List[ArtworkCandidate]:
        """
        Fetch and deduplicate artwork candidates from:
        1. The community-curated MusicBrainz Release Group canonical artwork.
        2. All matching release candidates for this disc.
        3. Other prominent pressings within the same release group.
        """
        if not candidates:
            return []

        # Find Release Group ID
        rg_id = candidates[0].musicbrainz_release_group_id or next(
            (c.musicbrainz_release_group_id for c in candidates if c.musicbrainz_release_group_id),
            None,
        )

        release_ids: List[str] = []
        seen_rids = set()
        for c in candidates:
            if c.musicbrainz_release_id and c.musicbrainz_release_id not in seen_rids:
                seen_rids.add(c.musicbrainz_release_id)
                release_ids.append(c.musicbrainz_release_id)

        # Optionally query Release Group for other release pressings
        if rg_id and hasattr(self.mb_client, "get_release_group_releases"):
            try:
                rg_rids = self.mb_client.get_release_group_releases(rg_id, limit=4)
                for rid in rg_rids:
                    if rid not in seen_rids:
                        seen_rids.add(rid)
                        release_ids.append(rid)
            except Exception as err:
                logger.debug("Failed to query release group releases: %s", err)

        # Limit to max 5 releases to prevent excessive network calls
        release_ids = release_ids[:5]

        all_candidates: List[ArtworkCandidate] = []

        def _fetch_rg() -> List[ArtworkCandidate]:
            if rg_id and hasattr(self.caa_client, "get_release_group_artwork"):
                try:
                    return self.caa_client.get_release_group_artwork(rg_id)
                except Exception as err:
                    logger.debug("Failed to fetch release group artwork for %s: %s", rg_id, err)
            return []

        def _fetch_release(rid: str) -> List[ArtworkCandidate]:
            try:
                return self.caa_client.get_artwork_candidates(rid)
            except Exception as err:
                logger.debug("Failed to fetch artwork candidates for release %s: %s", rid, err)
            return []

        workers = max(1, min(6, len(release_ids) + (1 if rg_id else 0)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            rg_future = executor.submit(_fetch_rg)
            rel_futures = [executor.submit(_fetch_release, rid) for rid in release_ids]

            all_candidates.extend(rg_future.result())
            for fut in rel_futures:
                all_candidates.extend(fut.result())

        # Deduplicate by image ID (preserving release_group origin if present)
        seen_image_ids = set()
        deduped: List[ArtworkCandidate] = []
        for cand in all_candidates:
            if not cand.image_id:
                continue
            if cand.image_id in seen_image_ids:
                for existing in deduped:
                    if existing.image_id == cand.image_id and cand.source == "release_group":
                        existing.source = "release_group"
                continue
            seen_image_ids.add(cand.image_id)
            deduped.append(cand)

        # If no front cover candidates found via Cover Art Archive, query external providers (iTunes & Deezer)
        if not any(cand.is_front for cand in deduped):
            primary = candidates[0]
            if primary.artist and primary.title:
                try:
                    ext_candidates = get_external_artwork_candidates(
                        primary.artist,
                        primary.title,
                        session=getattr(self.caa_client, "session", None),
                    )
                    for ext_cand in ext_candidates:
                        if ext_cand.image_id not in seen_image_ids:
                            seen_image_ids.add(ext_cand.image_id)
                            deduped.append(ext_cand)
                except Exception as err:
                    logger.debug("External artwork fallback lookup failed: %s", err)

        # Sort: canonical Release Group front first, then high-res square fronts, then scans
        deduped.sort(key=CoverArtClient._artwork_priority_key, reverse=True)
        return deduped

    def cache_selected_artwork(self, album: AlbumInfo, destination_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Download the chosen album artwork candidate into a local cache file.
        Returns the path to the cached JPEG file and updates candidate dimensions.
        Includes automatic fallback to alternative candidates or external services
        if primary download fails (e.g. during an Archive.org storage outage).
        """
        if not album.selected_artwork or not album.selected_artwork.url:
            return None

        if destination_dir is None:
            destination_dir = Path.home() / ".cache" / "lazycdripper" / "artwork"

        try:
            destination_dir.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            logger.warning("Could not create artwork cache directory %s: %s", destination_dir, err)
            return None

        rel_id = album.musicbrainz_release_id or "release"
        img_id = album.selected_artwork.image_id or "cover"
        target_file = destination_dir / f"{rel_id}_{img_id}.jpg"

        # Check if this exact image ID is already cached under this or any other release
        if not target_file.exists() or target_file.stat().st_size == 0:
            existing_matches = list(destination_dir.glob(f"*_{img_id}.jpg"))
            if existing_matches and existing_matches[0].stat().st_size > 0:
                target_file = existing_matches[0]

        if target_file.exists() and target_file.stat().st_size > 0:
            album.selected_artwork.local_cache_path = target_file
            dims = get_image_dimensions(target_file)
            if dims:
                album.selected_artwork.width, album.selected_artwork.height = dims
            return target_file

        cached_path = self.caa_client.download_image(album.selected_artwork.url, target_file)

        # If primary candidate download failed (e.g. Archive.org 502/timeout), try alternate candidates
        if not cached_path and album.artwork_candidates:
            for alt_cand in album.artwork_candidates:
                if alt_cand == album.selected_artwork or not alt_cand.url:
                    continue
                alt_img_id = alt_cand.image_id or "alt_cover"
                alt_target = destination_dir / f"{rel_id}_{alt_img_id}.jpg"
                alt_cached = self.caa_client.download_image(alt_cand.url, alt_target)
                if alt_cached:
                    album.selected_artwork = alt_cand
                    cached_path = alt_cached
                    break

        # If still not cached and artist/title available, query external services dynamically
        if not cached_path and album.artist and album.title:
            try:
                ext_candidates = get_external_artwork_candidates(
                    album.artist, album.title, session=getattr(self.caa_client, "session", None)
                )
                for ext_cand in ext_candidates:
                    ext_target = destination_dir / f"{rel_id}_{ext_cand.image_id}.jpg"
                    ext_cached = self.caa_client.download_image(ext_cand.url, ext_target)
                    if ext_cached:
                        album.selected_artwork = ext_cand
                        if album.artwork_candidates is not None:
                            album.artwork_candidates.append(ext_cand)
                        cached_path = ext_cached
                        break
            except Exception as err:
                logger.debug("Dynamic fallback artwork download failed: %s", err)

        if cached_path:
            album.selected_artwork.local_cache_path = cached_path
            dims = get_image_dimensions(cached_path)
            if dims:
                album.selected_artwork.width, album.selected_artwork.height = dims
        return cached_path
