import sqlite3
from dataclasses import dataclass
from pathlib import Path

from gonic_library_manager.core.config import Settings, get_settings
from gonic_library_manager.repositories.tracks import get_track_by_rel_path
from gonic_library_manager.services.scanner import is_audio_file


@dataclass(frozen=True)
class DirectoryEntry:
    name: str
    rel_path: str
    kind: str
    size_bytes: int | None
    extension: str | None
    track_id: int | None
    modified: float | None
    depth: int


def list_directory_entries(
    connection: sqlite3.Connection,
    root: Path | None = None,
    settings: Settings | None = None,
    query: str = "",
) -> list[DirectoryEntry]:
    settings = settings or get_settings()
    root = (root or settings.music_library_path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    query_lower = query.lower().strip()
    entries: list[DirectoryEntry] = []

    def include(rel_path: str, name: str) -> bool:
        if not query_lower:
            return True
        return query_lower in rel_path.lower() or query_lower in name.lower()

    for path in sorted(root.rglob("*"), key=lambda item: (item.as_posix().lower())):
        relative_parts = path.relative_to(root).parts
        if path.name.startswith(".") or any(part.startswith(".") for part in relative_parts):
            continue
        rel_path = path.relative_to(root).as_posix()
        depth = len(relative_parts) - 1

        if path.is_dir():
            if include(rel_path, path.name):
                entries.append(
                    DirectoryEntry(
                        name=path.name,
                        rel_path=rel_path,
                        kind="Folder",
                        size_bytes=None,
                        extension=None,
                        track_id=None,
                        modified=path.stat().st_mtime,
                        depth=depth,
                    )
                )
            continue

        if not is_audio_file(path, settings):
            continue
        track = get_track_by_rel_path(connection, rel_path)
        if include(rel_path, path.name):
            entries.append(
                DirectoryEntry(
                    name=path.name,
                    rel_path=rel_path,
                    kind="Audio",
                    size_bytes=path.stat().st_size,
                    extension=path.suffix.lower(),
                    track_id=track.id if track else None,
                    modified=path.stat().st_mtime,
                    depth=depth,
                )
            )

    return entries
