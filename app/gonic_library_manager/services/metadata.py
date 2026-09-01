from pathlib import Path
from typing import Any

from gonic_library_manager.models import TrackMetadata

COVER_FILENAMES = (
    "cover.jpg",
    "cover.jpeg",
    "folder.jpg",
    "folder.jpeg",
    "front.jpg",
    "front.jpeg",
)


def _first(values: Any) -> str | None:
    if not values:
        return None
    if isinstance(values, (list, tuple)):
        return str(values[0]) if values else None
    return str(values)


def _number(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(str(value).split("/")[0])
    except ValueError:
        return None


def _folder_has_cover(path: Path) -> bool:
    return any((path.parent / cover_name).exists() for cover_name in COVER_FILENAMES)


def read_metadata(path: Path) -> TrackMetadata:
    """Read tags from an audio file.

    Mutagen is used when installed and the file is valid audio. If metadata cannot
    be read yet, return empty metadata instead of failing the whole scan. This keeps
    the scanner testable and lets the UI still show unknown/new files.
    """

    try:
        from mutagen import File
    except ModuleNotFoundError:
        return TrackMetadata(has_cover=_folder_has_cover(path))

    try:
        easy_audio = File(path, easy=True)
        raw_audio = File(path)
    except Exception:
        return TrackMetadata(has_cover=_folder_has_cover(path))

    tags = easy_audio.tags if easy_audio and easy_audio.tags else {}
    info = getattr(raw_audio or easy_audio, "info", None)
    duration = getattr(info, "length", None)

    return TrackMetadata(
        title=_first(tags.get("title")),
        artist=_first(tags.get("artist")),
        album=_first(tags.get("album")),
        album_artist=_first(tags.get("albumartist") or tags.get("album_artist")),
        genre=_first(tags.get("genre")),
        date=_first(tags.get("date")),
        track_number=_number(_first(tags.get("tracknumber"))),
        disc_number=_number(_first(tags.get("discnumber"))),
        duration_seconds=duration,
        bitrate=getattr(info, "bitrate", None),
        sample_rate=getattr(info, "sample_rate", None),
        channels=getattr(info, "channels", None),
        has_cover=_has_embedded_cover(raw_audio) or _folder_has_cover(path),
    )


def _has_embedded_cover(audio: Any) -> bool:
    if not audio:
        return False
    if getattr(audio, "pictures", None):
        return True
    tags = getattr(audio, "tags", None)
    if not tags:
        return False
    try:
        if any(str(key).startswith("APIC") for key in tags.keys()):
            return True
    except Exception:
        return False
    return "covr" in tags or "metadata_block_picture" in tags
