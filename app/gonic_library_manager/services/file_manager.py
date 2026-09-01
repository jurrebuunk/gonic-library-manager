import shutil
from pathlib import Path

from gonic_library_manager.core.config import Settings, get_settings
from gonic_library_manager.models import Track


def ensure_inside_library(path: Path, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    root = settings.music_library_path.resolve()
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("Path is outside the music library")
    return resolved


def delete_track_file(track: Track, settings: Settings | None = None) -> Path:
    path = ensure_inside_library(track.path, settings)
    if path.exists() and path.is_file():
        path.unlink()
    return path


def delete_album_files(tracks: list[Track], settings: Settings | None = None) -> set[Path]:
    if not tracks:
        return set()

    paths = {ensure_inside_library(track.path, settings) for track in tracks}
    parent_dirs = {path.parent for path in paths}

    # For normal gonic structure (Artist/Album/tracks + cover.jpg), remove the
    # album directory too so folder artwork disappears with the album. If tracks
    # from this metadata album are spread across folders, delete only the files.
    if len(parent_dirs) == 1:
        album_dir = next(iter(parent_dirs))
        shutil.rmtree(album_dir)
        return paths

    for path in paths:
        if path.exists() and path.is_file():
            path.unlink()
    return paths
