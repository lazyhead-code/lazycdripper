"""Master pipeline orchestrator uniting disc extraction, dual-encoding, tagging, and audit reporting."""

import logging
from pathlib import Path
import tempfile
import time
from typing import Callable, Optional
from lazycdripper.core.models import (
    AlbumInfo,
    AlbumRipReport,
    AudioFormat,
    RipProgress,
    TrackRipReport,
)
from lazycdripper.core.sanitizer import (
    format_album_directory_name,
    get_target_track_path,
)
from lazycdripper.encoder.ffmpeg import FFmpegEncoder
from lazycdripper.ripper import get_default_ripper
from lazycdripper.tagger.tagger import AudioTagger

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[RipProgress], None]


class RipPipelineOrchestrator:
    """Coordinates the entire CD ripping lifecycle from optical disc to finished FLAC and AAC libraries."""

    def __init__(
        self,
        ripper=None,
        encoder=None,
        tagger=None,
    ):
        self.ripper = ripper or get_default_ripper()
        if encoder is not None:
            self.encoder = encoder
        else:
            ffmpeg_enc = FFmpegEncoder()
            if not ffmpeg_enc.is_available:
                try:
                    from lazycdripper.core.binaries import ensure_ffmpeg
                    ensure_ffmpeg()
                    ffmpeg_enc = FFmpegEncoder()
                except Exception as err:
                    logger.warning("Could not automatically prepare FFmpeg: %s", err)
            self.encoder = ffmpeg_enc
        self.tagger = tagger or AudioTagger()

    def execute_rip(
        self,
        album: AlbumInfo,
        base_output_dir: Path,
        device: Optional[str] = None,
        include_track_number: bool = True,
        include_artist: bool = False,
        on_progress: Optional[ProgressCallback] = None,
    ) -> AlbumRipReport:
        """
        Execute full album extraction, dual-encoding (FLAC + AAC), and tagging.
        Returns a comprehensive AlbumRipReport audit.
        """
        if not getattr(self.encoder, "is_available", False):
            raise RuntimeError(
                "FFmpeg is required to encode audio files to FLAC and AAC, but was not found. "
                "Please ensure FFmpeg is available or internet access is enabled for automatic setup."
            )

        start_time = time.time()
        base_output_dir = Path(base_output_dir)

        # 1. Establish sister destination directories
        flac_album_dir = base_output_dir / format_album_directory_name(
            album.artist, album.title, album.year, AudioFormat.FLAC
        )
        aac_album_dir = base_output_dir / format_album_directory_name(
            album.artist, album.title, album.year, AudioFormat.AAC
        )
        flac_album_dir.mkdir(parents=True, exist_ok=True)
        aac_album_dir.mkdir(parents=True, exist_ok=True)

        # 2. Save companion cover.jpg if artwork is cached
        cover_path = album.selected_artwork.local_cache_path if album.selected_artwork else None
        if cover_path and cover_path.exists():
            self.tagger.save_companion_cover(flac_album_dir, cover_path)
            self.tagger.save_companion_cover(aac_album_dir, cover_path)

        track_reports = []
        total_tracks = len(album.tracks)
        overall_jitter = 0
        overall_retries = 0
        overall_errors = 0

        # 3. Scratch directory for intermediate 16-bit WAV audio
        with tempfile.TemporaryDirectory() as scratch_temp:
            scratch_dir = Path(scratch_temp)

            for idx, track in enumerate(album.tracks, start=1):
                scratch_wav = scratch_dir / f"track_{track.track_number:02d}_scratch.wav"

                # Setup track-level progress tracking
                current_track_progress = RipProgress(
                    current_track=track.track_number,
                    total_tracks=total_tracks,
                    track_percent=0.0,
                    overall_percent=((idx - 1) / total_tracks) * 100.0,
                    status_message="Extracting track...",
                    track_title=track.title,
                )
                if on_progress:
                    on_progress(current_track_progress)

                def ripper_callback(p: RipProgress):
                    nonlocal current_track_progress
                    current_track_progress = p
                    if not p.track_title:
                        p.track_title = track.title
                    completed = idx - 1
                    current_contrib = p.track_percent / 100.0
                    p.overall_percent = ((completed + current_contrib) / total_tracks) * 100.0
                    if on_progress:
                        on_progress(p)

                # A. Extract track from optical CD to WAV
                rip_ok = self.ripper.rip_track(
                    track_number=track.track_number,
                    output_wav_path=scratch_wav,
                    device=device,
                    total_tracks=total_tracks,
                    on_progress=ripper_callback,
                )

                # Accumulate error telemetry
                overall_jitter += current_track_progress.jitter_corrections
                overall_retries += current_track_progress.read_retries
                overall_errors += current_track_progress.unrecoverable_errors

                # Determine track-level integrity status
                if not rip_ok or not scratch_wav.exists():
                    track_status = "failed"
                    if current_track_progress.unrecoverable_errors == 0:
                        current_track_progress.unrecoverable_errors = 1
                        overall_errors += 1
                elif current_track_progress.unrecoverable_errors > 0:
                    track_status = "damaged"
                elif current_track_progress.read_retries > 0:
                    track_status = "recovered"
                else:
                    track_status = "pristine"

                flac_dest = get_target_track_path(
                    base_output_dir=base_output_dir,
                    artist=album.artist,
                    album=album.title,
                    year=album.year,
                    audio_format=AudioFormat.FLAC,
                    track_number=track.track_number,
                    track_title=track.title,
                    disc_number=track.disc_number,
                    total_discs=album.total_discs,
                    include_track_number=include_track_number,
                    include_artist=include_artist,
                    track_artist=track.artist,
                )

                aac_dest = get_target_track_path(
                    base_output_dir=base_output_dir,
                    artist=album.artist,
                    album=album.title,
                    year=album.year,
                    audio_format=AudioFormat.AAC,
                    track_number=track.track_number,
                    track_title=track.title,
                    disc_number=track.disc_number,
                    total_discs=album.total_discs,
                    include_track_number=include_track_number,
                    include_artist=include_artist,
                    track_artist=track.artist,
                )

                if rip_ok and scratch_wav.exists():
                    # Notify UI: Dual-encoding started
                    if on_progress:
                        current_track_progress.track_percent = 100.0
                        current_track_progress.overall_percent = (idx / total_tracks) * 100.0
                        current_track_progress.status_message = (
                            "Transcoding: Lossless FLAC + 256k AAC..."
                        )
                        current_track_progress.current_speed = ""
                        current_track_progress.track_title = track.title
                        on_progress(current_track_progress)

                    # B. Parallel Dual-Transcode (FLAC + AAC)
                    flac_ok, aac_ok = self.encoder.encode_dual(
                        input_wav=scratch_wav,
                        output_flac=flac_dest,
                        output_aac=aac_dest,
                    )

                    flac_valid = (
                        flac_ok
                        and flac_dest.exists()
                        and flac_dest.stat().st_size > 4096
                    )
                    aac_valid = (
                        aac_ok
                        and aac_dest.exists()
                        and aac_dest.stat().st_size > 4096
                    )

                    if not flac_valid or not aac_valid:
                        logger.error(
                            "Encoding failed for Track %d: FLAC valid=%s, AAC valid=%s",
                            track.track_number,
                            flac_valid,
                            aac_valid,
                        )
                        track_status = "failed"
                        current_track_progress.unrecoverable_errors += 1
                        overall_errors += 1
                        if on_progress:
                            current_track_progress.status_message = (
                                f"Encoding failed for Track {track.track_number}"
                            )
                            current_track_progress.track_title = track.title
                            on_progress(current_track_progress)

                    # C. Metadata & Artwork Tagging (only for valid files)
                    if flac_valid or aac_valid:
                        if on_progress:
                            current_track_progress.status_message = (
                                "Embedding metadata & cover art..."
                            )
                            current_track_progress.current_speed = ""
                            current_track_progress.track_title = track.title
                            on_progress(current_track_progress)

                    if flac_valid:
                        self.tagger.tag_track(
                            file_path=flac_dest,
                            track=track,
                            album=album,
                            audio_format=AudioFormat.FLAC,
                            cover_image_path=cover_path,
                        )
                    if aac_valid:
                        self.tagger.tag_track(
                            file_path=aac_dest,
                            track=track,
                            album=album,
                            audio_format=AudioFormat.AAC,
                            cover_image_path=cover_path,
                        )

                    if on_progress:
                        current_track_progress.status_message = (
                            f"Track {track.track_number} complete"
                        )
                        on_progress(current_track_progress)

                    # D. Delete scratch WAV immediately to conserve disk space
                    try:
                        scratch_wav.unlink(missing_ok=True)
                    except Exception:
                        pass

                track_reports.append(
                    TrackRipReport(
                        track_number=track.track_number,
                        title=track.title,
                        status=track_status,
                        jitter_corrections=current_track_progress.jitter_corrections,
                        read_retries=current_track_progress.read_retries,
                        unrecoverable_errors=current_track_progress.unrecoverable_errors,
                        flac_path=flac_dest if flac_dest.exists() else None,
                        aac_path=aac_dest if aac_dest.exists() else None,
                    )
                )

        # 4. Compute overall album health status
        successful_tracks = sum(
            1 for t in track_reports
            if t.flac_path is not None and t.flac_path.exists() and t.status != "failed"
        )
        if successful_tracks == 0 and total_tracks > 0:
            overall_status = "failed"
        elif overall_errors > 0 or successful_tracks < total_tracks:
            overall_status = "damaged"
        elif overall_retries > 0:
            overall_status = "recovered"
        else:
            overall_status = "pristine"

        # Calculate library directory sizes
        flac_size = sum(f.stat().st_size for f in flac_album_dir.rglob("*") if f.is_file()) if flac_album_dir.exists() else 0
        aac_size = sum(f.stat().st_size for f in aac_album_dir.rglob("*") if f.is_file()) if aac_album_dir.exists() else 0

        elapsed = time.time() - start_time

        return AlbumRipReport(
            album_title=album.title,
            artist=album.artist,
            year=album.year,
            total_tracks=total_tracks,
            overall_status=overall_status,
            total_jitter=overall_jitter,
            total_retries=overall_retries,
            total_errors=overall_errors,
            duration_seconds=elapsed,
            destination_directory=base_output_dir if successful_tracks > 0 else None,
            flac_directory=flac_album_dir if successful_tracks > 0 else None,
            aac_directory=aac_album_dir if successful_tracks > 0 else None,
            flac_size_bytes=flac_size,
            aac_size_bytes=aac_size,
            track_reports=track_reports,
        )
