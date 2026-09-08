from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrackMetadata:
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    genre: str | None = None
    date: str | None = None
    track_number: int | None = None
    disc_number: int | None = None
    duration_seconds: float | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    has_cover: bool = False


@dataclass(frozen=True)
class Track:
    id: int | None
    path: Path
    rel_path: str
    filename: str
    extension: str
    size_bytes: int
    mtime: float
    metadata: TrackMetadata


@dataclass(frozen=True)
class DirectoryFile:
    name: str
    rel_path: str


@dataclass(frozen=True)
class DirectoryNode:
    name: str
    rel_path: str
    directories: list["DirectoryNode"]
    files: list[DirectoryFile]


@dataclass(frozen=True)
class DownloadTaskOptions:
    url: str
    label: str | None
    download_type: str
    output_subdir: str
    output_template: str
    audio_format: str
    audio_quality: str
    embed_metadata: bool = True
    embed_thumbnail: bool = True
    write_thumbnail: bool = False
    restrict_filenames: bool = False
    use_archive: bool = True


@dataclass(frozen=True)
class DownloadTask:
    id: int
    url: str
    label: str | None
    download_type: str
    status: str
    output_subdir: str
    output_template: str
    audio_format: str
    audio_quality: str
    embed_metadata: bool
    embed_thumbnail: bool
    write_thumbnail: bool
    restrict_filenames: bool
    use_archive: bool
    command: list[str]
    log_path: Path
    return_code: int | None
    error: str | None
    created_at: str
    started_at: str | None
    finished_at: str | None
