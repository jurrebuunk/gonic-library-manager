from dataclasses import dataclass
from functools import lru_cache
from os import getenv
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables.

    Kept deliberately small and dependency-free so future modules can depend on it
    without pulling in web framework code.
    """

    app_name: str
    app_host: str
    app_port: int
    music_library_path: Path
    data_dir: Path
    library_extensions: frozenset[str]
    ytdlp_binary: str
    download_concurrency: int

    @property
    def database_path(self) -> Path:
        return self.data_dir / "library.sqlite3"


def _csv_extensions(value: str) -> frozenset[str]:
    return frozenset(
        ext.strip().lower() if ext.strip().startswith(".") else f".{ext.strip().lower()}"
        for ext in value.split(",")
        if ext.strip()
    )


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=getenv("APP_NAME", "Sonic Ledger"),
        app_host=getenv("APP_HOST", "0.0.0.0"),
        app_port=int(getenv("APP_PORT", "8080")),
        music_library_path=Path(getenv("MUSIC_LIBRARY_PATH", "/music")).resolve(),
        data_dir=Path(getenv("DATA_DIR", "/data")).resolve(),
        library_extensions=_csv_extensions(
            getenv("LIBRARY_EXTENSIONS", ".mp3,.flac,.ogg,.opus,.m4a,.aac,.wav")
        ),
        ytdlp_binary=getenv("YTDLP_BINARY", "yt-dlp"),
        download_concurrency=max(1, int(getenv("DOWNLOAD_CONCURRENCY", "3"))),
    )


def ensure_runtime_dirs(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    settings.music_library_path.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
