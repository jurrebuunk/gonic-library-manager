import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from gonic_library_manager.core.config import get_settings
from gonic_library_manager.repositories.tracks import (
    count_tracks,
    first_track,
    get_track,
    list_tracks,
)
from gonic_library_manager.services.scanner import scan_library

router = APIRouter()


def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


def get_db(request: Request) -> sqlite3.Connection:
    return request.app.state.db


@router.get("/")
def library_view(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    q: str = "",
    view: str = "list",
    selected_id: int | None = None,
):
    tracks = list_tracks(db, q)
    selected_track = get_track(db, selected_id) if selected_id else None
    selected_track = selected_track or (tracks[0] if tracks else first_track(db))
    return templates.TemplateResponse(
        request,
        "library.html",
        {
            "settings": get_settings(),
            "active_page": "tracks",
            "tracks": tracks,
            "selected_track": selected_track,
            "total_tracks": count_tracks(db),
            "q": q,
            "view": "grid" if view == "grid" else "list",
            "selected_id": selected_track.id if selected_track else None,
        },
    )


@router.post("/scan")
def scan_now(db: Annotated[sqlite3.Connection, Depends(get_db)]):
    scan_library(db, get_settings())
    return RedirectResponse(url="/", status_code=303)
