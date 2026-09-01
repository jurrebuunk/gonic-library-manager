import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from gonic_library_manager.core.config import Settings, ensure_runtime_dirs, get_settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    rel_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    extension TEXT NOT NULL,
    title TEXT,
    artist TEXT,
    album TEXT,
    album_artist TEXT,
    genre TEXT,
    date TEXT,
    track_number INTEGER,
    disc_number INTEGER,
    duration_seconds REAL,
    bitrate INTEGER,
    sample_rate INTEGER,
    channels INTEGER,
    has_cover INTEGER NOT NULL DEFAULT 0,
    size_bytes INTEGER NOT NULL,
    mtime REAL NOT NULL,
    scanned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tracks_rel_path ON tracks(rel_path);
CREATE INDEX IF NOT EXISTS idx_tracks_artist_album ON tracks(artist, album);
CREATE INDEX IF NOT EXISTS idx_tracks_title ON tracks(title);
"""

MIGRATIONS = (
    "ALTER TABLE tracks ADD COLUMN bitrate INTEGER",
    "ALTER TABLE tracks ADD COLUMN sample_rate INTEGER",
    "ALTER TABLE tracks ADD COLUMN channels INTEGER",
)


def connect(settings: Settings | None = None) -> sqlite3.Connection:
    settings = settings or get_settings()
    ensure_runtime_dirs(settings)
    connection = sqlite3.connect(settings.database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(settings: Settings | None = None) -> None:
    connection = connect(settings)
    try:
        connection.executescript(SCHEMA_SQL)
        for migration in MIGRATIONS:
            try:
                connection.execute(migration)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        connection.commit()
    finally:
        connection.close()


@contextmanager
def db_session(settings: Settings | None = None) -> Iterator[sqlite3.Connection]:
    connection = connect(settings)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
