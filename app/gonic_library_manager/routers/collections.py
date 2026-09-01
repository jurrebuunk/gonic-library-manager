import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from gonic_library_manager.core.config import get_settings
from gonic_library_manager.repositories.tracks import (
    first_track,
    get_track,
    list_albums,
    list_artists,
    list_recent_tracks,
)

router = APIRouter(tags=["collections"])


def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


def get_db(request: Request) -> sqlite3.Connection:
    return request.app.state.db


@router.get("/albums")
def albums_view(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
):
    return templates.TemplateResponse(
        request,
        "collections.html",
        {
            "settings": get_settings(),
            "active_page": "albums",
            "page_title": "Albums",
            "items": list_albums(db),
            "selected_track": first_track(db),
            "kind": "albums",
        },
    )


@router.get("/artists")
def artists_view(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
):
    return templates.TemplateResponse(
        request,
        "collections.html",
        {
            "settings": get_settings(),
            "active_page": "artists",
            "page_title": "Artists",
            "items": list_artists(db),
            "selected_track": first_track(db),
            "kind": "artists",
        },
    )


@router.get("/recent")
def recent_view(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    selected_id: int | None = None,
):
    tracks = list_recent_tracks(db)
    selected_track = get_track(db, selected_id) if selected_id else None
    return templates.TemplateResponse(
        request,
        "recent.html",
        {
            "settings": get_settings(),
            "active_page": "recent",
            "tracks": tracks,
            "selected_track": selected_track or (tracks[0] if tracks else first_track(db)),
        },
    )
