import sqlite3
from pathlib import Path

from gonic_library_manager.models import Track, TrackMetadata

UPSERT_TRACK_SQL = """
INSERT INTO tracks (
    path, rel_path, filename, extension, title, artist, album, album_artist,
    genre, date, track_number, disc_number, duration_seconds, bitrate,
    sample_rate, channels, has_cover, size_bytes, mtime, scanned_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
    bitrate = excluded.bitrate,
    sample_rate = excluded.sample_rate,
    channels = excluded.channels,
    has_cover = excluded.has_cover,
    size_bytes = excluded.size_bytes,
    mtime = excluded.mtime,
    scanned_at = CURRENT_TIMESTAMP
"""


def _row_get(row: sqlite3.Row, key: str) -> object | None:
    return row[key] if key in row.keys() else None


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
            bitrate=_row_get(row, "bitrate"),
            sample_rate=_row_get(row, "sample_rate"),
            channels=_row_get(row, "channels"),
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
            metadata.bitrate,
            metadata.sample_rate,
            metadata.channels,
            int(metadata.has_cover),
            track.size_bytes,
            track.mtime,
        ),
    )


def list_tracks(
    connection: sqlite3.Connection,
    query: str | None = None,
    limit: int = 1000,
) -> list[Track]:
    sql = "SELECT * FROM tracks"
    params: list[object] = []
    if query:
        sql += (
            " WHERE title LIKE ? OR artist LIKE ? OR album LIKE ? "
            "OR album_artist LIKE ? OR rel_path LIKE ?"
        )
        needle = f"%{query}%"
        params.extend([needle, needle, needle, needle, needle])
    sql += (
        " ORDER BY COALESCE(artist, ''), COALESCE(album, ''), "
        "COALESCE(track_number, 9999), filename LIMIT ?"
    )
    params.append(limit)
    rows = connection.execute(sql, params).fetchall()
    return [row_to_track(row) for row in rows]


def get_track(connection: sqlite3.Connection, track_id: int) -> Track | None:
    row = connection.execute("SELECT * FROM tracks WHERE id = ?", (track_id,)).fetchone()
    return row_to_track(row) if row else None


def get_track_by_rel_path(connection: sqlite3.Connection, rel_path: str) -> Track | None:
    row = connection.execute("SELECT * FROM tracks WHERE rel_path = ?", (rel_path,)).fetchone()
    return row_to_track(row) if row else None


def first_track(connection: sqlite3.Connection) -> Track | None:
    row = connection.execute(
        """
        SELECT * FROM tracks
        ORDER BY COALESCE(artist, ''), COALESCE(album, ''), COALESCE(track_number, 9999), filename
        LIMIT 1
        """
    ).fetchone()
    return row_to_track(row) if row else None


def update_track_metadata(connection: sqlite3.Connection, track: Track) -> None:
    metadata = track.metadata
    connection.execute(
        """
        UPDATE tracks
        SET title = ?, artist = ?, album = ?, album_artist = ?, genre = ?, date = ?,
            track_number = ?, disc_number = ?, duration_seconds = ?, bitrate = ?,
            sample_rate = ?, channels = ?, has_cover = ?, scanned_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            metadata.title,
            metadata.artist,
            metadata.album,
            metadata.album_artist,
            metadata.genre,
            metadata.date,
            metadata.track_number,
            metadata.disc_number,
            metadata.duration_seconds,
            metadata.bitrate,
            metadata.sample_rate,
            metadata.channels,
            int(metadata.has_cover),
            track.id,
        ),
    )
    connection.commit()


def count_tracks(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) AS count FROM tracks").fetchone()
    return int(row["count"])


def list_albums(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT COALESCE(album, 'Unknown Album') AS album,
               COALESCE(album_artist, artist, 'Unknown Artist') AS artist,
               COUNT(*) AS track_count,
               MIN(id) AS first_track_id,
               COALESCE(MIN(CASE WHEN has_cover = 1 THEN id END), MIN(id)) AS cover_track_id
        FROM tracks
        GROUP BY COALESCE(album, 'Unknown Album'), COALESCE(album_artist, artist, 'Unknown Artist')
        ORDER BY album COLLATE NOCASE
        """
    ).fetchall()


def list_album_tracks_by_anchor(connection: sqlite3.Connection, track_id: int) -> list[Track]:
    anchor = get_track(connection, track_id)
    if not anchor:
        return []
    album = anchor.metadata.album or "Unknown Album"
    artist = anchor.metadata.album_artist or anchor.metadata.artist or "Unknown Artist"
    rows = connection.execute(
        """
        SELECT * FROM tracks
        WHERE COALESCE(album, 'Unknown Album') = ?
          AND COALESCE(album_artist, artist, 'Unknown Artist') = ?
        ORDER BY COALESCE(track_number, 9999), filename
        """,
        (album, artist),
    ).fetchall()
    return [row_to_track(row) for row in rows]


def list_artists(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT COALESCE(artist, 'Unknown Artist') AS artist,
               COUNT(*) AS track_count,
               COUNT(DISTINCT COALESCE(album, 'Unknown Album')) AS album_count,
               MIN(id) AS first_track_id,
               COALESCE(MIN(CASE WHEN has_cover = 1 THEN id END), MIN(id)) AS cover_track_id
        FROM tracks
        GROUP BY COALESCE(artist, 'Unknown Artist')
        ORDER BY artist COLLATE NOCASE
        """
    ).fetchall()


def list_artist_tracks_by_anchor(connection: sqlite3.Connection, track_id: int) -> list[Track]:
    anchor = get_track(connection, track_id)
    if not anchor:
        return []
    artist = anchor.metadata.artist or "Unknown Artist"
    rows = connection.execute(
        """
        SELECT * FROM tracks
        WHERE COALESCE(artist, 'Unknown Artist') = ?
        ORDER BY COALESCE(album, ''), COALESCE(track_number, 9999), filename
        """,
        (artist,),
    ).fetchall()
    return [row_to_track(row) for row in rows]


def delete_track_row(connection: sqlite3.Connection, track_id: int) -> None:
    connection.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    connection.commit()


def delete_track_rows_by_paths(connection: sqlite3.Connection, paths: set[Path]) -> None:
    for path in paths:
        connection.execute("DELETE FROM tracks WHERE path = ?", (str(path),))
    connection.commit()


def delete_track_rows_by_ids(connection: sqlite3.Connection, track_ids: set[int]) -> None:
    for track_id in track_ids:
        connection.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    connection.commit()


def delete_missing_tracks(connection: sqlite3.Connection, existing_paths: set[Path]) -> int:
    rows = connection.execute("SELECT id, path FROM tracks").fetchall()
    removed = 0
    normalized = {str(path.resolve()) for path in existing_paths}
    for row in rows:
        if str(Path(row["path"]).resolve()) not in normalized:
            connection.execute("DELETE FROM tracks WHERE id = ?", (row["id"],))
            removed += 1
    return removed
