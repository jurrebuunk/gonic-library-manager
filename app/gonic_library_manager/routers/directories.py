from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from gonic_library_manager.core.config import get_settings
from gonic_library_manager.services.directory_tree import build_directory_tree

router = APIRouter(prefix="/directories", tags=["directories"])


def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


@router.get("")
def directory_view(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
):
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "directories.html",
        {
            "settings": settings,
            "tree": build_directory_tree(settings=settings),
        },
    )
