import sqlite3
import tempfile
import unittest
from pathlib import Path

from gonic_library_manager.core.config import Settings
from gonic_library_manager.db.connection import init_db
from gonic_library_manager.models import DownloadTaskOptions
from gonic_library_manager.repositories.downloads import get_download_task, insert_download_task
from gonic_library_manager.services.download_tasks import (
    DEFAULT_PLAYLIST_TEMPLATE,
    DEFAULT_SINGLE_TEMPLATE,
    build_ytdlp_command,
    default_output_template,
    resolve_output_base,
)


class DownloadTasksTest(unittest.TestCase):
    def make_settings(self, root: Path) -> Settings:
        return Settings(
            app_name="test",
            app_host="127.0.0.1",
            app_port=8080,
            music_library_path=root / "music",
            data_dir=root / "data",
            library_extensions=frozenset({".flac", ".mp3", ".opus"}),
            ytdlp_binary="yt-dlp",
            download_concurrency=2,
        )

    def make_options(self, **overrides) -> DownloadTaskOptions:
        values = {
            "url": "https://example.com/watch?v=abc",
            "label": "Example",
            "download_type": "single",
            "output_subdir": ".",
            "output_template": DEFAULT_SINGLE_TEMPLATE,
            "audio_format": "mp3",
            "audio_quality": "0",
            "embed_metadata": True,
            "embed_thumbnail": True,
            "write_thumbnail": False,
            "restrict_filenames": False,
            "use_archive": True,
        }
        values.update(overrides)
        return DownloadTaskOptions(**values)

    def test_builds_gonic_friendly_single_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            command = build_ytdlp_command(self.make_options(), settings)

            self.assertIn("--no-playlist", command)
            self.assertIn("--extract-audio", command)
            self.assertIn("--embed-metadata", command)
            self.assertIn("--embed-thumbnail", command)
            self.assertIn(DEFAULT_SINGLE_TEMPLATE, command)
            self.assertEqual(
                command[command.index("--paths") + 1],
                str(settings.music_library_path),
            )

    def test_playlist_template_and_output_subdir_stay_inside_music_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.make_settings(Path(tmp))
            destination = resolve_output_base(settings, "Incoming/YouTube")
            self.assertEqual(destination, settings.music_library_path / "Incoming" / "YouTube")
            self.assertEqual(default_output_template("playlist"), DEFAULT_PLAYLIST_TEMPLATE)

            with self.assertRaises(ValueError):
                resolve_output_base(settings, "../outside")

    def test_download_task_repository_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = self.make_settings(root)
            init_db(settings)
            connection = sqlite3.connect(settings.database_path)
            connection.row_factory = sqlite3.Row
            try:
                options = self.make_options()
                task_id = insert_download_task(connection, options, settings.data_dir / "task.log")
                connection.commit()

                task = get_download_task(connection, task_id)
                self.assertIsNotNone(task)
                assert task is not None
                self.assertEqual(task.status, "queued")
                self.assertEqual(task.label, "Example")
                self.assertTrue(task.embed_metadata)
                self.assertTrue(task.use_archive)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
