import base64
from pathlib import Path
from typing import Any

from gonic_library_manager.services.metadata import COVER_FILENAMES


def find_folder_cover(path: Path) -> Path | None:
    for cover_name in COVER_FILENAMES:
        candidate = path.parent / cover_name
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def read_cover_art(path: Path) -> tuple[bytes, str] | None:
    """Return cover image bytes and MIME type, if available.

    This supports the design now and is isolated so the future cover editor can
    build on the same service.
    """

    try:
        from mutagen import File
    except ModuleNotFoundError:
        return _read_folder_cover(path)

    try:
        audio = File(path)
    except Exception:
        return _read_folder_cover(path)

    for candidate in (
        _read_flac_picture(audio),
        _read_mp3_picture(audio),
        _read_mp4_picture(audio),
        _read_metadata_block_picture(audio),
    ):
        if candidate and _looks_like_browser_image(*candidate):
            return candidate

    return _read_folder_cover(path)


def _looks_like_browser_image(data: bytes, mime: str) -> bool:
    if mime == "image/jpeg":
        return data.startswith(b"\xff\xd8")
    if mime == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if mime == "image/gif":
        return data.startswith((b"GIF87a", b"GIF89a"))
    if mime == "image/webp":
        return data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    return True


def _read_flac_picture(audio: Any) -> tuple[bytes, str] | None:
    pictures = getattr(audio, "pictures", None)
    if pictures:
        picture = pictures[0]
        return picture.data, picture.mime or "image/jpeg"
    return None


def _read_mp3_picture(audio: Any) -> tuple[bytes, str] | None:
    tags = getattr(audio, "tags", None)
    if not tags:
        return None
    try:
        for key in tags.keys():
            if str(key).startswith("APIC"):
                frame = tags[key]
                return frame.data, frame.mime or "image/jpeg"
    except Exception:
        return None
    return None


def _read_mp4_picture(audio: Any) -> tuple[bytes, str] | None:
    tags = getattr(audio, "tags", None)
    if not tags or "covr" not in tags:
        return None
    cover = tags["covr"][0]
    image_format = getattr(cover, "imageformat", None)
    mime = "image/png" if image_format == 14 else "image/jpeg"
    return bytes(cover), mime


def write_album_folder_cover(track_paths: list[Path], image: bytes, mime: str) -> Path:
    if not track_paths:
        raise ValueError("Album has no tracks")

    parent_dirs = {path.parent.resolve() for path in track_paths}
    album_dir = (
        next(iter(parent_dirs))
        if len(parent_dirs) == 1
        else track_paths[0].parent.resolve()
    )

    for cover_name in COVER_FILENAMES:
        candidate = album_dir / cover_name
        if candidate.exists() and candidate.is_file():
            candidate.unlink()

    extension = ".png" if mime == "image/png" else ".jpg"
    target = album_dir / f"cover{extension}"
    target.write_bytes(image)
    return target


def write_cover_art(path: Path, image: bytes, mime: str) -> None:
    """Write cover art.

    FLAC and MP3 get embedded artwork. Other formats fall back to album-folder
    `cover.jpg`/`cover.png`, which gonic also understands well.
    """

    suffix = path.suffix.lower()
    if suffix == ".flac":
        from mutagen.flac import FLAC, Picture

        audio = FLAC(path)
        audio.clear_pictures()
        picture = Picture()
        picture.data = image
        picture.mime = mime
        picture.type = 3
        audio.add_picture(picture)
        audio.save()
        return

    if suffix == ".mp3":
        from mutagen.id3 import APIC
        from mutagen.mp3 import MP3

        audio = MP3(path)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.delall("APIC")
        audio.tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=image))
        audio.save()
        return

    extension = ".png" if mime == "image/png" else ".jpg"
    (path.parent / f"cover{extension}").write_bytes(image)


def _read_metadata_block_picture(audio: Any) -> tuple[bytes, str] | None:
    tags = getattr(audio, "tags", None)
    if not tags or "metadata_block_picture" not in tags:
        return None
    try:
        from mutagen.flac import Picture

        value = tags["metadata_block_picture"]
        encoded = value[0] if isinstance(value, list) else value
        picture = Picture(base64.b64decode(str(encoded)))
        return picture.data, picture.mime or "image/jpeg"
    except Exception:
        return None


def _read_folder_cover(path: Path) -> tuple[bytes, str] | None:
    cover = find_folder_cover(path)
    if not cover:
        return None
    mime = "image/png" if cover.suffix.lower() == ".png" else "image/jpeg"
    data = cover.read_bytes()
    if not _looks_like_browser_image(data, mime):
        return None
    return data, mime
