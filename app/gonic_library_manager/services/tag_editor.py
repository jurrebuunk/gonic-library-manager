from pathlib import Path

from gonic_library_manager.models import TrackMetadata

EDITABLE_TAGS = {
    "title": "title",
    "artist": "artist",
    "album": "album",
    "album_artist": "albumartist",
    "genre": "genre",
    "date": "date",
    "track_number": "tracknumber",
    "disc_number": "discnumber",
}


def update_tags(path: Path, updates: TrackMetadata) -> None:
    """Write editable tags to an audio file with Mutagen.

    The SQLite index is updated by rescanning after this service succeeds.
    """

    try:
        from mutagen import File
    except ModuleNotFoundError as exc:
        raise RuntimeError("Mutagen is required for tag editing") from exc

    audio = File(path, easy=True)
    if audio is None:
        raise ValueError(f"Unsupported audio file: {path}")
    if audio.tags is None:
        audio.add_tags()

    values: dict[str, str | int | None] = {
        "title": updates.title,
        "artist": updates.artist,
        "album": updates.album,
        "album_artist": updates.album_artist,
        "genre": updates.genre,
        "date": updates.date,
        "track_number": updates.track_number,
        "disc_number": updates.disc_number,
    }

    for public_key, tag_key in EDITABLE_TAGS.items():
        value = values[public_key]
        if value is None or value == "":
            audio.tags.pop(tag_key, None)
        else:
            audio.tags[tag_key] = [str(value)]

    audio.save()
