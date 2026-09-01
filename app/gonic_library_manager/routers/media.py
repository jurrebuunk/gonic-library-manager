import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from gonic_library_manager.repositories.tracks import get_track
from gonic_library_manager.services.cover_art import read_cover_art

router = APIRouter(prefix="/media", tags=["media"])


def get_db(request: Request) -> sqlite3.Connection:
    return request.app.state.db


@router.get("/tracks/{track_id}/cover")
def track_cover(track_id: int, db: Annotated[sqlite3.Connection, Depends(get_db)]) -> Response:
    track = get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    cover = read_cover_art(Path(track.path))
    if not cover:
        raise HTTPException(status_code=404, detail="Cover art not found")

    data, mime = cover
    return Response(content=data, media_type=mime)
