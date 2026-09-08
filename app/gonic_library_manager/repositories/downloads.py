import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

from gonic_library_manager.models import DownloadTask, DownloadTaskOptions


def _bool(value: Any) -> bool:
    return bool(int(value or 0))


def task_from_row(row: sqlite3.Row) -> DownloadTask:
    command_json = row["command_json"] or "[]"
    try:
        command = json.loads(command_json)
    except json.JSONDecodeError:
        command = []
    return DownloadTask(
        id=int(row["id"]),
        url=row["url"],
        label=row["label"],
        download_type=row["download_type"],
        status=row["status"],
        output_subdir=row["output_subdir"],
        output_template=row["output_template"],
        audio_format=row["audio_format"],
        audio_quality=row["audio_quality"],
        embed_metadata=_bool(row["embed_metadata"]),
        embed_thumbnail=_bool(row["embed_thumbnail"]),
        write_thumbnail=_bool(row["write_thumbnail"]),
        restrict_filenames=_bool(row["restrict_filenames"]),
        use_archive=_bool(row["use_archive"]),
        command=command,
        log_path=Path(row["log_path"]),
        return_code=row["return_code"],
        error=row["error"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
    )


def insert_download_task(
    connection: sqlite3.Connection,
    options: DownloadTaskOptions,
    log_path: Path,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO download_tasks (
            url, label, download_type, status, output_subdir, output_template,
            audio_format, audio_quality, embed_metadata, embed_thumbnail,
            write_thumbnail, restrict_filenames, use_archive, command_json, log_path
        ) VALUES (?, ?, ?, 'queued', ?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', ?)
        """,
        (
            options.url,
            options.label,
            options.download_type,
            options.output_subdir,
            options.output_template,
            options.audio_format,
            options.audio_quality,
            int(options.embed_metadata),
            int(options.embed_thumbnail),
            int(options.write_thumbnail),
            int(options.restrict_filenames),
            int(options.use_archive),
            str(log_path),
        ),
    )
    return int(cursor.lastrowid)


def get_download_task(connection: sqlite3.Connection, task_id: int) -> DownloadTask | None:
    row = connection.execute("SELECT * FROM download_tasks WHERE id = ?", (task_id,)).fetchone()
    return task_from_row(row) if row else None


def list_download_tasks(connection: sqlite3.Connection, limit: int = 50) -> list[DownloadTask]:
    rows = connection.execute(
        "SELECT * FROM download_tasks ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [task_from_row(row) for row in rows]


def list_queued_download_task_ids(connection: sqlite3.Connection) -> list[int]:
    rows = connection.execute(
        "SELECT id FROM download_tasks WHERE status = 'queued' ORDER BY id ASC"
    ).fetchall()
    return [int(row["id"]) for row in rows]


def mark_orphaned_running_tasks_failed(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        UPDATE download_tasks
        SET status = 'failed',
            finished_at = CURRENT_TIMESTAMP,
            error = 'The application restarted while this task was running.'
        WHERE status = 'running'
        """
    )


def mark_download_task_running(
    connection: sqlite3.Connection,
    task_id: int,
    command: list[str],
) -> bool:
    cursor = connection.execute(
        """
        UPDATE download_tasks
        SET status = 'running', started_at = CURRENT_TIMESTAMP, command_json = ?, error = NULL
        WHERE id = ? AND status = 'queued'
        """,
        (json.dumps(command), task_id),
    )
    return cursor.rowcount > 0


def finish_download_task(
    connection: sqlite3.Connection,
    task_id: int,
    status: str,
    return_code: int | None = None,
    error: str | None = None,
) -> None:
    connection.execute(
        """
        UPDATE download_tasks
        SET status = ?, return_code = ?, error = ?, finished_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, return_code, error, task_id),
    )


def cancel_queued_download_task(connection: sqlite3.Connection, task_id: int) -> bool:
    cursor = connection.execute(
        """
        UPDATE download_tasks
        SET status = 'cancelled', finished_at = CURRENT_TIMESTAMP, error = 'Cancelled before start.'
        WHERE id = ? AND status = 'queued'
        """,
        (task_id,),
    )
    return cursor.rowcount > 0


def serialize_task(task: DownloadTask, log_tail: str = "") -> dict[str, Any]:
    data = asdict(task)
    data["log_path"] = str(task.log_path)
    data["can_cancel"] = task.status in {"queued", "running"}
    data["log_tail"] = log_tail
    return data
