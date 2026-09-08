import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from gonic_library_manager.core.config import get_settings
from gonic_library_manager.dependencies import get_db, get_templates
from gonic_library_manager.models import DownloadTask, DownloadTaskOptions
from gonic_library_manager.repositories.downloads import list_download_tasks, serialize_task
from gonic_library_manager.services.download_tasks import (
    ALLOWED_AUDIO_FORMATS,
    ALLOWED_AUDIO_QUALITIES,
    ALLOWED_DOWNLOAD_TYPES,
    DEFAULT_PLAYLIST_TEMPLATE,
    DEFAULT_SINGLE_TEMPLATE,
    DownloadTaskManager,
    default_output_template,
    read_log_tail,
)

router = APIRouter(prefix="/tools/downloads", tags=["downloads"])


def _task_context(tasks: list[DownloadTask]) -> list[dict]:
    return [serialize_task(task, read_log_tail(task.log_path)) for task in tasks]


def _manager(request: Request) -> DownloadTaskManager:
    manager = getattr(request.app.state, "download_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="Download manager is not available")
    return manager


@router.get("")
def downloads_page(
    request: Request,
    db: Annotated[sqlite3.Connection, Depends(get_db)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
):
    settings = get_settings()
    tasks = list_download_tasks(db)
    return templates.TemplateResponse(
        request,
        "downloads.html",
        {
            "settings": settings,
            "active_page": "tools",
            "active_tool": "downloads",
            "selected_track": None,
            "selected_album": None,
            "selected_artist": None,
            "download_tasks_panel": True,
            "download_tasks": tasks,
            "download_task_items": _task_context(tasks),
            "defaults": {
                "download_type": "playlist",
                "single_template": DEFAULT_SINGLE_TEMPLATE,
                "playlist_template": DEFAULT_PLAYLIST_TEMPLATE,
                "output_template": default_output_template("playlist"),
                "output_subdir": ".",
                "audio_format": "mp3",
                "audio_quality": "0",
                "embed_metadata": True,
                "embed_thumbnail": True,
                "write_thumbnail": False,
                "restrict_filenames": False,
                "use_archive": True,
            },
            "audio_formats": sorted(ALLOWED_AUDIO_FORMATS),
            "audio_qualities": sorted(ALLOWED_AUDIO_QUALITIES),
        },
    )


@router.post("")
async def create_download_task(
    request: Request,
    url: Annotated[str, Form()],
    label: Annotated[str, Form()] = "",
    download_type: Annotated[str, Form()] = "playlist",
    output_subdir: Annotated[str, Form()] = ".",
    output_template: Annotated[str, Form()] = "",
    audio_format: Annotated[str, Form()] = "mp3",
    audio_quality: Annotated[str, Form()] = "0",
    embed_metadata: Annotated[bool, Form()] = False,
    embed_thumbnail: Annotated[bool, Form()] = False,
    write_thumbnail: Annotated[bool, Form()] = False,
    restrict_filenames: Annotated[bool, Form()] = False,
    use_archive: Annotated[bool, Form()] = False,
) -> RedirectResponse:
    if download_type not in ALLOWED_DOWNLOAD_TYPES:
        raise HTTPException(status_code=400, detail="Invalid download type")
    if audio_format not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(status_code=400, detail="Invalid audio format")
    if audio_quality not in ALLOWED_AUDIO_QUALITIES:
        raise HTTPException(status_code=400, detail="Invalid audio quality")

    options = DownloadTaskOptions(
        url=url,
        label=label or None,
        download_type=download_type,
        output_subdir=output_subdir,
        output_template=output_template or default_output_template(download_type),
        audio_format=audio_format,
        audio_quality=audio_quality,
        embed_metadata=embed_metadata,
        embed_thumbnail=embed_thumbnail,
        write_thumbnail=write_thumbnail,
        restrict_filenames=restrict_filenames,
        use_archive=use_archive,
    )
    try:
        task_id = await _manager(request).enqueue(options)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(url=f"/tools/downloads?created={task_id}", status_code=303)


@router.post("/{task_id}/cancel")
async def cancel_download_task(request: Request, task_id: int) -> RedirectResponse:
    await _manager(request).cancel(task_id)
    return RedirectResponse(url="/tools/downloads", status_code=303)


@router.get("/tasks")
def download_tasks_api(db: Annotated[sqlite3.Connection, Depends(get_db)]) -> JSONResponse:
    tasks = list_download_tasks(db)
    return JSONResponse({"tasks": _task_context(tasks)})
