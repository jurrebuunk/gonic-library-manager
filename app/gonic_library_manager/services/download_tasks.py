import asyncio
import contextlib
import os
import signal
from pathlib import Path

from gonic_library_manager.core.config import Settings, get_settings
from gonic_library_manager.db.connection import db_session
from gonic_library_manager.models import DownloadTaskOptions
from gonic_library_manager.repositories.downloads import (
    cancel_queued_download_task,
    finish_download_task,
    get_download_task,
    insert_download_task,
    list_queued_download_task_ids,
    mark_download_task_running,
    mark_orphaned_running_tasks_failed,
)
from gonic_library_manager.services.scanner import scan_library

DEFAULT_SINGLE_TEMPLATE = "%(artist,uploader|Unknown Artist)s/%(album|Singles)s/%(title)s.%(ext)s"
DEFAULT_PLAYLIST_TEMPLATE = (
    "%(artist,playlist_uploader,uploader|Unknown Artist)s/"
    "%(album,playlist_title|Downloaded Playlist)s/"
    "%(playlist_index)02d - %(title)s.%(ext)s"
)
ALLOWED_DOWNLOAD_TYPES = {"single", "playlist"}
ALLOWED_AUDIO_FORMATS = {"best", "mp3", "opus", "m4a", "flac", "vorbis", "wav"}
ALLOWED_AUDIO_QUALITIES = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def default_output_template(download_type: str) -> str:
    return DEFAULT_SINGLE_TEMPLATE if download_type == "single" else DEFAULT_PLAYLIST_TEMPLATE


def normalize_download_options(options: DownloadTaskOptions) -> DownloadTaskOptions:
    url = options.url.strip()
    if not url:
        raise ValueError("A video or playlist URL is required.")

    download_type = (
        options.download_type if options.download_type in ALLOWED_DOWNLOAD_TYPES else "playlist"
    )
    audio_format = options.audio_format if options.audio_format in ALLOWED_AUDIO_FORMATS else "mp3"
    audio_quality = (
        options.audio_quality if options.audio_quality in ALLOWED_AUDIO_QUALITIES else "0"
    )
    output_template = options.output_template.strip() or default_output_template(download_type)
    output_subdir = options.output_subdir.strip() or "."
    label = options.label.strip() if options.label else None

    return DownloadTaskOptions(
        url=url,
        label=label,
        download_type=download_type,
        output_subdir=output_subdir,
        output_template=output_template,
        audio_format=audio_format,
        audio_quality=audio_quality,
        embed_metadata=options.embed_metadata,
        embed_thumbnail=options.embed_thumbnail,
        write_thumbnail=options.write_thumbnail,
        restrict_filenames=options.restrict_filenames,
        use_archive=options.use_archive,
    )


def resolve_output_base(settings: Settings, output_subdir: str) -> Path:
    relative = Path(output_subdir.strip() or ".")
    if relative.is_absolute():
        raise ValueError("Output location must be relative to the music library root.")
    destination = (settings.music_library_path / relative).resolve()
    try:
        destination.relative_to(settings.music_library_path)
    except ValueError as exc:
        raise ValueError("Output location must stay inside the music library root.") from exc
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def build_ytdlp_command(options: DownloadTaskOptions, settings: Settings) -> list[str]:
    options = normalize_download_options(options)
    output_base = resolve_output_base(settings, options.output_subdir)

    command = [
        settings.ytdlp_binary,
        "--newline",
        "--continue",
        "--no-overwrites",
        "--ignore-errors",
        "--extract-audio",
        "--audio-format",
        options.audio_format,
        "--audio-quality",
        options.audio_quality,
        "--paths",
        str(output_base),
        "-o",
        options.output_template,
    ]

    if options.download_type == "single":
        command.append("--no-playlist")
    else:
        command.append("--yes-playlist")

    if options.embed_metadata:
        command.append("--embed-metadata")
    if options.embed_thumbnail:
        command.extend(["--embed-thumbnail", "--convert-thumbnails", "jpg"])
    elif options.write_thumbnail:
        command.extend(["--convert-thumbnails", "jpg"])
    if options.write_thumbnail:
        command.append("--write-thumbnail")
    if options.restrict_filenames:
        command.append("--restrict-filenames")
    if options.use_archive:
        command.extend(["--download-archive", str(settings.data_dir / "yt-dlp-archive.txt")])

    command.append(options.url)
    return command


def read_log_tail(log_path: Path, max_bytes: int = 6000) -> str:
    if not log_path.exists():
        return ""
    with log_path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - max_bytes))
        return handle.read().decode("utf-8", errors="replace")


def _append_log(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", errors="replace") as handle:
        handle.write(line)
        if not line.endswith("\n"):
            handle.write("\n")


def _scan_library(settings: Settings) -> None:
    with db_session(settings) as connection:
        scan_library(connection, settings)


class DownloadTaskManager:
    """Runs yt-dlp jobs outside request handlers and keeps cancel handles in memory."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._semaphore = asyncio.Semaphore(self.settings.download_concurrency)
        self._started = False
        self._runners: dict[int, asyncio.Task[None]] = {}
        self._processes: dict[int, asyncio.subprocess.Process] = {}
        self._cancel_requested: set[int] = set()
        self._scan_lock = asyncio.Lock()

    async def start(self) -> None:
        self._started = True
        with db_session(self.settings) as connection:
            mark_orphaned_running_tasks_failed(connection)
            queued_task_ids = list_queued_download_task_ids(connection)
        for task_id in queued_task_ids:
            self.schedule(task_id)

    async def shutdown(self) -> None:
        self._started = False
        for task_id in list(self._processes):
            await self.cancel(task_id)
        for task_id, runner in list(self._runners.items()):
            if task_id not in self._processes:
                runner.cancel()
        runners = list(self._runners.values())
        if not runners:
            return
        done, pending = await asyncio.wait(runners, timeout=5)
        for runner in pending:
            runner.cancel()
        if done or pending:
            await asyncio.gather(*done, *pending, return_exceptions=True)

    def schedule(self, task_id: int) -> None:
        if not self._started:
            return
        runner = self._runners.get(task_id)
        if runner and not runner.done():
            return
        runner = asyncio.create_task(self._run_task(task_id), name=f"download-task-{task_id}")
        runner.add_done_callback(
            lambda _task, current_id=task_id: self._runners.pop(current_id, None)
        )
        self._runners[task_id] = runner

    async def enqueue(self, options: DownloadTaskOptions) -> int:
        options = normalize_download_options(options)
        resolve_output_base(self.settings, options.output_subdir)
        log_dir = self.settings.data_dir / "download-logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with db_session(self.settings) as connection:
            task_id = insert_download_task(connection, options, log_dir / "pending.log")
            log_path = log_dir / f"{task_id}.log"
            connection.execute(
                "UPDATE download_tasks SET log_path = ? WHERE id = ?",
                (str(log_path), task_id),
            )
        self.schedule(task_id)
        return task_id

    async def cancel(self, task_id: int) -> bool:
        self._cancel_requested.add(task_id)
        with db_session(self.settings) as connection:
            if cancel_queued_download_task(connection, task_id):
                return True
            task = get_download_task(connection, task_id)
        if not task or task.status in TERMINAL_STATUSES:
            return False

        process = self._processes.get(task_id)
        if process and process.returncode is None:
            _append_log(task.log_path, "\n[cancel] Cancellation requested; terminating yt-dlp...")
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)
            return True
        return task.status == "running"

    async def _run_task(self, task_id: int) -> None:
        async with self._semaphore:
            with db_session(self.settings) as connection:
                task = get_download_task(connection, task_id)
            if not task or task.status != "queued":
                return
            if task_id in self._cancel_requested:
                with db_session(self.settings) as connection:
                    finish_download_task(
                        connection,
                        task_id,
                        "cancelled",
                        error="Cancelled before start.",
                    )
                return

            options = DownloadTaskOptions(
                url=task.url,
                label=task.label,
                download_type=task.download_type,
                output_subdir=task.output_subdir,
                output_template=task.output_template,
                audio_format=task.audio_format,
                audio_quality=task.audio_quality,
                embed_metadata=task.embed_metadata,
                embed_thumbnail=task.embed_thumbnail,
                write_thumbnail=task.write_thumbnail,
                restrict_filenames=task.restrict_filenames,
                use_archive=task.use_archive,
            )

            try:
                command = build_ytdlp_command(options, self.settings)
                with db_session(self.settings) as connection:
                    started = mark_download_task_running(connection, task_id, command)
                if not started:
                    return
                _append_log(task.log_path, "$ " + " ".join(command))
                await self._spawn_and_wait(task_id, task.log_path, command)
            except FileNotFoundError:
                message = f"Could not find yt-dlp binary: {self.settings.ytdlp_binary}"
                _append_log(task.log_path, message)
                with db_session(self.settings) as connection:
                    finish_download_task(connection, task_id, "failed", error=message)
            except Exception as exc:
                message = str(exc)
                _append_log(task.log_path, f"[error] {message}")
                with db_session(self.settings) as connection:
                    finish_download_task(connection, task_id, "failed", error=message)

    async def _spawn_and_wait(self, task_id: int, log_path: Path, command: list[str]) -> None:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
        )
        self._processes[task_id] = process
        if task_id in self._cancel_requested and process.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)

        assert process.stdout is not None
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            _append_log(log_path, line.decode("utf-8", errors="replace").rstrip("\n"))

        return_code = await process.wait()
        self._processes.pop(task_id, None)

        if task_id in self._cancel_requested:
            with db_session(self.settings) as connection:
                finish_download_task(
                    connection,
                    task_id,
                    "cancelled",
                    return_code=return_code,
                    error="Cancelled by user.",
                )
            _append_log(log_path, f"[cancelled] yt-dlp exited with code {return_code}.")
            return

        if return_code == 0:
            _append_log(log_path, "[done] Download completed. Rescanning library index...")
            async with self._scan_lock:
                await asyncio.to_thread(_scan_library, self.settings)
            with db_session(self.settings) as connection:
                finish_download_task(connection, task_id, "completed", return_code=return_code)
            _append_log(log_path, "[done] Library index refreshed.")
        else:
            message = f"yt-dlp exited with code {return_code}."
            with db_session(self.settings) as connection:
                finish_download_task(
                    connection,
                    task_id,
                    "failed",
                    return_code=return_code,
                    error=message,
                )
            _append_log(log_path, f"[failed] {message}")
