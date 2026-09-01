import sqlite3
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates

from gonic_library_manager.core.config import get_settings
from gonic_library_manager.repositories.tracks import get_track
from gonic_library_manager.services.directory_entries import breadcrumbs_for, list_directory_entries

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
    dir: str = ".",
    q: str = "",
    selected_id: int | None = None,
):
    settings = get_settings()
    try:
        entries = list_directory_entries(db, settings=settings, current_dir=dir, query=q)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    selected_track = get_track(db, selected_id) if selected_id else None
    deselect_url = f"/directories?{urlencode({'dir': dir, 'q': q})}"
    return templates.TemplateResponse(
        request,
        "directories.html",
        {
            "active_page": "folders",
            "settings": settings,
            "entries": entries,
            "breadcrumbs": breadcrumbs_for(dir),
            "current_dir": dir,
            "q": q,
            "selected_track": selected_track,
            "selected_id": selected_track.id if selected_track else None,
            "deselect_url": deselect_url,
        },
    )
