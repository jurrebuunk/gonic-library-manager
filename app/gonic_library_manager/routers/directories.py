import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from gonic_library_manager.core.config import get_settings
from gonic_library_manager.repositories.tracks import first_track, get_track
from gonic_library_manager.services.directory_entries import list_directory_entries

router = APIRouter(prefix="/directories", tags=["directories"])


def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


def get_db(request: Request) -> sqlite3.Connection:
    return request.app.state.db


@router.get("")
def directory_view(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    q: str = "",
    selected_id: int | None = None,
):
    settings = get_settings()
    entries = list_directory_entries(db, settings=settings, query=q)
    selected_track = get_track(db, selected_id) if selected_id else None
    selected_track = selected_track or first_track(db)
    return templates.TemplateResponse(
        request,
        "directories.html",
        {
            "active_page": "folders",
            "settings": settings,
            "entries": entries,
            "q": q,
            "selected_track": selected_track,
            "selected_id": selected_track.id if selected_track else None,
        },
    )
