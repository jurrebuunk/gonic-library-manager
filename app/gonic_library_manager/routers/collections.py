import sqlite3
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from gonic_library_manager.core.config import get_settings
from gonic_library_manager.dependencies import get_db, get_templates
from gonic_library_manager.models import Track
from gonic_library_manager.repositories.tracks import (
    delete_track_rows_by_ids,
    list_album_tracks_by_anchor,
    list_albums,
    list_artist_tracks_by_anchor,
    list_artists,
)
from gonic_library_manager.services.cover_art import write_album_folder_cover
from gonic_library_manager.services.file_manager import delete_album_files
from gonic_library_manager.services.scanner import scan_file

router = APIRouter(tags=["collections"])


def album_summary(anchor_id: int, tracks: list[Track]) -> dict[str, Any] | None:
    if not tracks:
        return None
    first = tracks[0]
    album = first.metadata.album or "Unknown Album"
    artist = first.metadata.album_artist or first.metadata.artist or "Unknown Artist"
    cover_track = next((track for track in tracks if track.metadata.has_cover), first)
    parent_dirs = {track.path.parent for track in tracks}
    directory = next(iter(parent_dirs)).as_posix() if len(parent_dirs) == 1 else "Multiple folders"
    return {
        "anchor_id": anchor_id,
        "title": album,
        "artist": artist,
        "track_count": len(tracks),
        "total_size": sum(track.size_bytes for track in tracks),
        "cover_track_id": cover_track.id,
        "tracks": tracks,
        "directory": directory,
    }


def artist_summary(anchor_id: int, tracks: list[Track]) -> dict[str, Any] | None:
    if not tracks:
        return None
    first = tracks[0]
    artist = first.metadata.artist or "Unknown Artist"
    cover_track = next((track for track in tracks if track.metadata.has_cover), first)
    albums = sorted({track.metadata.album or "Unknown Album" for track in tracks})
    return {
        "anchor_id": anchor_id,
        "name": artist,
        "album_count": len(albums),
        "track_count": len(tracks),
        "total_size": sum(track.size_bytes for track in tracks),
        "cover_track_id": cover_track.id,
        "albums": albums,
        "tracks": tracks,
    }


@router.get("/albums")
def albums_view(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    selected_album_id: int | None = None,
):
    selected_album = None
    if selected_album_id:
        selected_album = album_summary(
            selected_album_id,
            list_album_tracks_by_anchor(db, selected_album_id),
        )

    return templates.TemplateResponse(
        request,
        "collections.html",
        {
            "settings": get_settings(),
            "active_page": "albums",
            "page_title": "Albums",
            "items": list_albums(db),
            "selected_track": None,
            "selected_album": selected_album,
            "selected_artist": None,
            "selected_album_id": selected_album_id if selected_album else None,
            "selected_artist_id": None,
            "deselect_url": "/albums",
            "kind": "albums",
        },
    )


@router.post("/albums/{track_id}/cover")
async def replace_album_cover(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    track_id: int,
    cover: Annotated[UploadFile, File()],
) -> RedirectResponse:
    tracks = list_album_tracks_by_anchor(db, track_id)
    if not tracks:
        raise HTTPException(status_code=404, detail="Album not found")
    if cover.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail="Cover must be a JPEG or PNG image")

    image = await cover.read()
    write_album_folder_cover(
        [Path(track.path) for track in tracks],
        image,
        cover.content_type or "image/jpeg",
    )
    for track in tracks:
        scan_file(db, Path(track.path))
    return RedirectResponse(url=f"/albums?selected_album_id={track_id}", status_code=303)


@router.post("/albums/{track_id}/delete")
def delete_album(
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    track_id: int,
) -> RedirectResponse:
    tracks = list_album_tracks_by_anchor(db, track_id)
    if not tracks:
        raise HTTPException(status_code=404, detail="Album not found")
    delete_album_files(tracks)
    delete_track_rows_by_ids(db, {track.id for track in tracks if track.id is not None})
    return RedirectResponse(url="/albums", status_code=303)


@router.get("/artists")
def artists_view(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    selected_artist_id: int | None = None,
):
    selected_artist = None
    if selected_artist_id:
        selected_artist = artist_summary(
            selected_artist_id,
            list_artist_tracks_by_anchor(db, selected_artist_id),
        )

    return templates.TemplateResponse(
        request,
        "collections.html",
        {
            "settings": get_settings(),
            "active_page": "artists",
            "page_title": "Artists",
            "items": list_artists(db),
            "selected_track": None,
            "selected_album": None,
            "selected_artist": selected_artist,
            "selected_album_id": None,
            "selected_artist_id": selected_artist_id if selected_artist else None,
            "deselect_url": "/artists",
            "kind": "artists",
        },
    )
