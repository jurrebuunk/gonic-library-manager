from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates


def format_bytes(value: int | None) -> str:
    if value is None:
        return "—"
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TB"


def format_duration(value: float | None) -> str:
    if not value:
        return "—"
    minutes, seconds = divmod(int(value), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_timestamp(value: float | None) -> str:
    if value is None:
        return "—"
    return datetime.fromtimestamp(value).strftime("%b %d, %Y")


def file_badge(path_or_extension: str | Path) -> str:
    extension = str(path_or_extension)
    if "." in extension:
        extension = Path(extension).suffix or extension
    return extension.replace(".", "").upper() or "AUDIO"


def configure_templates(templates: Jinja2Templates) -> Jinja2Templates:
    templates.env.filters["bytes"] = format_bytes
    templates.env.filters["duration"] = format_duration
    templates.env.filters["file_badge"] = file_badge
    templates.env.filters["date"] = format_timestamp
    return templates
