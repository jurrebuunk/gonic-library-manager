import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from gonic_library_manager.core.config import get_settings
from gonic_library_manager.repositories.tracks import count_tracks, list_tracks
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
):
    return templates.TemplateResponse(
        request,
        "library.html",
        {
            "settings": get_settings(),
            "tracks": list_tracks(db, q),
            "total_tracks": count_tracks(db),
            "q": q,
        },
    )


@router.post("/scan")
def scan_now(db: Annotated[sqlite3.Connection, Depends(get_db)]):
    scan_library(db, get_settings())
    return RedirectResponse(url="/", status_code=303)
