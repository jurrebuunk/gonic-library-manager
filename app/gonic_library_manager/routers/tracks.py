import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse

from gonic_library_manager.dependencies import get_db
from gonic_library_manager.models import TrackMetadata
from gonic_library_manager.repositories.tracks import delete_track_row, get_track
from gonic_library_manager.services.cover_art import write_cover_art
from gonic_library_manager.services.file_manager import delete_track_file
from gonic_library_manager.services.scanner import scan_file
from gonic_library_manager.services.tag_editor import update_tags

router = APIRouter(prefix="/tracks", tags=["tracks"])

def safe_redirect(next_url: str | None, fallback: str = "/") -> RedirectResponse:
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return RedirectResponse(url=next_url, status_code=303)
    return RedirectResponse(url=fallback, status_code=303)


@router.post("/{track_id}/tags")
def save_tags(
    track_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    title: Annotated[str | None, Form()] = None,
    artist: Annotated[str | None, Form()] = None,
    album: Annotated[str | None, Form()] = None,
    album_artist: Annotated[str | None, Form()] = None,
    date: Annotated[str | None, Form()] = None,
    track_number: Annotated[int | None, Form()] = None,
    disc_number: Annotated[int | None, Form()] = None,
    genre: Annotated[str | None, Form()] = None,
    next_url: Annotated[str | None, Form(alias="next")] = None,
) -> RedirectResponse:
    track = get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    update_tags(
        Path(track.path),
        TrackMetadata(
            title=title,
            artist=artist,
            album=album,
            album_artist=album_artist,
            date=date,
            track_number=track_number,
            disc_number=disc_number,
            genre=genre,
        ),
    )
    scan_file(db, Path(track.path))
    return safe_redirect(next_url)


@router.post("/{track_id}/cover")
async def save_cover(
    track_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    cover: Annotated[UploadFile, File()],
    next_url: Annotated[str | None, Form(alias="next")] = None,
) -> RedirectResponse:
    track = get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    if cover.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail="Cover must be a JPEG or PNG image")

    image = await cover.read()
    write_cover_art(Path(track.path), image, cover.content_type or "image/jpeg")
    scan_file(db, Path(track.path))
    return safe_redirect(next_url)


@router.post("/{track_id}/delete")
def delete_track(
    track_id: int,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    next_url: Annotated[str | None, Form(alias="next")] = None,
) -> RedirectResponse:
    track = get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    delete_track_file(track)
    delete_track_row(db, track_id)
    return safe_redirect(next_url)
