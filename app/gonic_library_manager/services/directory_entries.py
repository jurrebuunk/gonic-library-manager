import sqlite3
from dataclasses import dataclass
from pathlib import Path

from gonic_library_manager.core.config import Settings, get_settings
from gonic_library_manager.repositories.tracks import get_track_by_rel_path
from gonic_library_manager.services.scanner import is_audio_file

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})


@dataclass(frozen=True)
class Breadcrumb:
    name: str
    rel_path: str


@dataclass(frozen=True)
class DirectoryEntry:
    name: str
    rel_path: str
    kind: str
    size_bytes: int | None
    extension: str | None
    track_id: int | None
    modified: float | None


def resolve_directory(root: Path, rel_path: str) -> Path:
    if rel_path in {"", ".", "/"}:
        return root.resolve()
    candidate = (root / rel_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Directory is outside the music library")
    if not candidate.exists() or not candidate.is_dir():
        raise ValueError("Directory does not exist")
    return candidate


def breadcrumbs_for(rel_path: str) -> list[Breadcrumb]:
    if rel_path in {"", ".", "/"}:
        return [Breadcrumb("Music", ".")]
    parts = Path(rel_path).parts
    crumbs = [Breadcrumb("Music", ".")]
    for index, part in enumerate(parts):
        crumbs.append(Breadcrumb(part, Path(*parts[: index + 1]).as_posix()))
    return crumbs


def list_directory_entries(
    connection: sqlite3.Connection,
    root: Path | None = None,
    current_dir: str = ".",
    settings: Settings | None = None,
    query: str = "",
) -> list[DirectoryEntry]:
    """List one directory level, not the whole tree.

    This matches the nested explorer design: folders are opened by navigating into
    them, while the table only shows the current directory's direct children.
    """

    settings = settings or get_settings()
    root = (root or settings.music_library_path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    directory = resolve_directory(root, current_dir)
    query_lower = query.lower().strip()
    entries: list[DirectoryEntry] = []

    def include(rel_path: str, name: str) -> bool:
        if not query_lower:
            return True
        return query_lower in rel_path.lower() or query_lower in name.lower()

    children = sorted(
        directory.iterdir(),
        key=lambda item: (not item.is_dir(), item.name.lower()),
    )
    for path in children:
        if path.name.startswith("."):
            continue
        rel_path = path.relative_to(root).as_posix()
        if not include(rel_path, path.name):
            continue

        if path.is_dir():
            entries.append(
                DirectoryEntry(
                    name=path.name,
                    rel_path=rel_path,
                    kind="Folder",
                    size_bytes=None,
                    extension=None,
                    track_id=None,
                    modified=path.stat().st_mtime,
                )
            )
            continue

        if is_audio_file(path, settings):
            track = get_track_by_rel_path(connection, rel_path)
            entries.append(
                DirectoryEntry(
                    name=path.name,
                    rel_path=rel_path,
                    kind="Audio",
                    size_bytes=path.stat().st_size,
                    extension=path.suffix.lower(),
                    track_id=track.id if track else None,
                    modified=path.stat().st_mtime,
                )
            )
            continue

        if path.suffix.lower() in IMAGE_EXTENSIONS:
            entries.append(
                DirectoryEntry(
                    name=path.name,
                    rel_path=rel_path,
                    kind="Image",
                    size_bytes=path.stat().st_size,
                    extension=path.suffix.lower(),
                    track_id=None,
                    modified=path.stat().st_mtime,
                )
            )

    return entries
