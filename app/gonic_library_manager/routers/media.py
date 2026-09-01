import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from gonic_library_manager.dependencies import get_db
from gonic_library_manager.repositories.tracks import get_track
from gonic_library_manager.services.cover_art import read_cover_art

router = APIRouter(prefix="/media", tags=["media"])

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, max-age=0, must-revalidate",
    "Pragma": "no-cache",
}

PLACEHOLDER_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
<rect width="128" height="128" rx="8" fill="#201f1f"/>
<circle cx="64" cy="64" r="30" fill="none" stroke="#d0bcff" stroke-width="6" opacity=".8"/>
<circle cx="64" cy="64" r="8" fill="#d0bcff" opacity=".8"/>
</svg>"""


def is_supported_image(data: bytes, mime: str) -> bool:
    if mime == "image/jpeg":
        return data.startswith(b"\xff\xd8")
    if mime == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if mime == "image/gif":
        return data.startswith((b"GIF87a", b"GIF89a"))
    if mime == "image/webp":
        return data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    if mime == "image/svg+xml":
        return data.lstrip().startswith(b"<svg")
    return True


def placeholder_cover() -> Response:
    return Response(
        content=PLACEHOLDER_SVG,
        media_type="image/svg+xml",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/tracks/{track_id}/cover")
def track_cover(track_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]) -> Response:
    track = get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    try:
        cover = read_cover_art(Path(track.path))
    except Exception:
        cover = None

    if not cover:
        return placeholder_cover()

    data, mime = cover
    if not is_supported_image(data, mime):
        return placeholder_cover()
    return Response(content=data, media_type=mime, headers=NO_CACHE_HEADERS)
