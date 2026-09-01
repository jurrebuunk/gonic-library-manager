import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from gonic_library_manager.core.config import get_settings
from gonic_library_manager.repositories.tracks import first_track
from gonic_library_manager.services.directory_tree import build_directory_tree

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
):
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "directories.html",
        {
            "active_page": "folders",
            "settings": settings,
            "tree": build_directory_tree(settings=settings),
            "selected_track": first_track(db),
        },
    )
