import sqlite3
import tempfile
import unittest
from pathlib import Path

from gonic_library_manager.core.config import Settings
from gonic_library_manager.db.connection import init_db
from gonic_library_manager.repositories.tracks import count_tracks, list_tracks
from gonic_library_manager.services.directory_tree import build_directory_tree
from gonic_library_manager.services.scanner import iter_audio_files, scan_library


class ScannerTest(unittest.TestCase):
    def make_settings(self, root: Path) -> Settings:
        return Settings(
            app_name="test",
            app_host="127.0.0.1",
            app_port=8080,
            music_library_path=root / "music",
            data_dir=root / "data",
            library_extensions=frozenset({".flac", ".mp3"}),
        )

    def test_scan_indexes_audio_files_and_removes_missing_tracks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = self.make_settings(root)
            album_dir = settings.music_library_path / "Artist" / "Album"
            album_dir.mkdir(parents=True)
            first_track = album_dir / "01 - One.flac"
            second_track = album_dir / "02 - Two.mp3"
            ignored = album_dir / "notes.txt"
            first_track.write_bytes(b"fake flac")
            second_track.write_bytes(b"fake mp3")
            ignored.write_text("not audio")

            init_db(settings)
            connection = sqlite3.connect(settings.database_path)
            connection.row_factory = sqlite3.Row
            try:
                files = iter_audio_files(settings=settings)
                self.assertEqual([path.name for path in files], ["01 - One.flac", "02 - Two.mp3"])

                result = scan_library(connection, settings)
                self.assertEqual(result.scanned, 2)
                self.assertEqual(result.failed, 0)
                self.assertEqual(count_tracks(connection), 2)
                self.assertEqual(list_tracks(connection)[0].rel_path, "Artist/Album/01 - One.flac")

                second_track.unlink()
                result = scan_library(connection, settings)
                self.assertEqual(result.removed, 1)
                self.assertEqual(count_tracks(connection), 1)
            finally:
                connection.close()

    def test_directory_tree_matches_physical_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = self.make_settings(root)
            album_dir = settings.music_library_path / "Artist" / "Album"
            album_dir.mkdir(parents=True)
            (album_dir / "01 - One.flac").write_bytes(b"fake flac")
            (album_dir / "cover.jpg").write_bytes(b"fake image")

            tree = build_directory_tree(settings=settings)
            self.assertEqual(tree.rel_path, ".")
            self.assertEqual(tree.directories[0].name, "Artist")
            album = tree.directories[0].directories[0]
            self.assertEqual(album.name, "Album")
            self.assertEqual(album.files[0].rel_path, "Artist/Album/01 - One.flac")


if __name__ == "__main__":
    unittest.main()
