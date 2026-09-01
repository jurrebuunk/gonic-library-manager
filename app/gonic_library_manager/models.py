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
