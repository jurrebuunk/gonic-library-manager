import sqlite3
from dataclasses import dataclass
from pathlib import Path

from gonic_library_manager.core.config import Settings, get_settings
from gonic_library_manager.models import Track
from gonic_library_manager.repositories.tracks import delete_missing_tracks, upsert_track
from gonic_library_manager.services.metadata import read_metadata


@dataclass(frozen=True)
class ScanResult:
    scanned: int
    failed: int
    removed: int


def is_audio_file(path: Path, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    return path.is_file() and path.suffix.lower() in settings.library_extensions


def iter_audio_files(root: Path | None = None, settings: Settings | None = None) -> list[Path]:
    settings = settings or get_settings()
    root = (root or settings.music_library_path).resolve()
    if not root.exists():
        return []
    return sorted(
        path.resolve()
        for path in root.rglob("*")
        if is_audio_file(path, settings)
        and not any(part.startswith(".") for part in path.relative_to(root).parts)
    )


def build_track(path: Path, settings: Settings | None = None) -> Track:
    settings = settings or get_settings()
    path = path.resolve()
    stat = path.stat()
    return Track(
        id=None,
        path=path,
        rel_path=path.relative_to(settings.music_library_path.resolve()).as_posix(),
        filename=path.name,
        extension=path.suffix.lower(),
        size_bytes=stat.st_size,
        mtime=stat.st_mtime,
        metadata=read_metadata(path),
    )


def scan_library(connection: sqlite3.Connection, settings: Settings | None = None) -> ScanResult:
    settings = settings or get_settings()
    files = iter_audio_files(settings.music_library_path, settings)
    scanned = 0
    failed = 0

    for path in files:
        try:
            upsert_track(connection, build_track(path, settings))
            scanned += 1
        except Exception:
            failed += 1

    removed = delete_missing_tracks(connection, set(files))
    connection.commit()
    return ScanResult(scanned=scanned, failed=failed, removed=removed)
