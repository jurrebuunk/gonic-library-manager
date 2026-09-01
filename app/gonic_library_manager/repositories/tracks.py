import sqlite3
from pathlib import Path

from gonic_library_manager.models import Track, TrackMetadata


UPSERT_TRACK_SQL = """
INSERT INTO tracks (
    path, rel_path, filename, extension, title, artist, album, album_artist,
    genre, date, track_number, disc_number, duration_seconds, has_cover,
    size_bytes, mtime, scanned_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
ON CONFLICT(path) DO UPDATE SET
    rel_path = excluded.rel_path,
    filename = excluded.filename,
    extension = excluded.extension,
    title = excluded.title,
    artist = excluded.artist,
    album = excluded.album,
    album_artist = excluded.album_artist,
    genre = excluded.genre,
    date = excluded.date,
    track_number = excluded.track_number,
    disc_number = excluded.disc_number,
    duration_seconds = excluded.duration_seconds,
    has_cover = excluded.has_cover,
    size_bytes = excluded.size_bytes,
    mtime = excluded.mtime,
    scanned_at = CURRENT_TIMESTAMP
"""


def row_to_track(row: sqlite3.Row) -> Track:
    return Track(
        id=row["id"],
        path=Path(row["path"]),
        rel_path=row["rel_path"],
        filename=row["filename"],
        extension=row["extension"],
        size_bytes=row["size_bytes"],
        mtime=row["mtime"],
        metadata=TrackMetadata(
            title=row["title"],
            artist=row["artist"],
            album=row["album"],
            album_artist=row["album_artist"],
            genre=row["genre"],
            date=row["date"],
            track_number=row["track_number"],
            disc_number=row["disc_number"],
            duration_seconds=row["duration_seconds"],
            has_cover=bool(row["has_cover"]),
        ),
    )


def upsert_track(connection: sqlite3.Connection, track: Track) -> None:
    metadata = track.metadata
    connection.execute(
        UPSERT_TRACK_SQL,
        (
            str(track.path),
            track.rel_path,
            track.filename,
            track.extension,
            metadata.title,
            metadata.artist,
            metadata.album,
            metadata.album_artist,
            metadata.genre,
            metadata.date,
            metadata.track_number,
            metadata.disc_number,
            metadata.duration_seconds,
            int(metadata.has_cover),
            track.size_bytes,
            track.mtime,
        ),
    )


def list_tracks(connection: sqlite3.Connection, query: str | None = None, limit: int = 1000) -> list[Track]:
    sql = "SELECT * FROM tracks"
    params: list[object] = []
    if query:
        sql += " WHERE title LIKE ? OR artist LIKE ? OR album LIKE ? OR album_artist LIKE ? OR rel_path LIKE ?"
        needle = f"%{query}%"
        params.extend([needle, needle, needle, needle, needle])
    sql += " ORDER BY COALESCE(artist, ''), COALESCE(album, ''), COALESCE(track_number, 9999), filename LIMIT ?"
    params.append(limit)
    rows = connection.execute(sql, params).fetchall()
    return [row_to_track(row) for row in rows]


def count_tracks(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) AS count FROM tracks").fetchone()
    return int(row["count"])


def delete_missing_tracks(connection: sqlite3.Connection, existing_paths: set[Path]) -> int:
    rows = connection.execute("SELECT id, path FROM tracks").fetchall()
    removed = 0
    normalized = {str(path.resolve()) for path in existing_paths}
    for row in rows:
        if str(Path(row["path"]).resolve()) not in normalized:
            connection.execute("DELETE FROM tracks WHERE id = ?", (row["id"],))
            removed += 1
    return removed
