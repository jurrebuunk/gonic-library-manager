from pathlib import Path

from gonic_library_manager.core.config import Settings, get_settings
from gonic_library_manager.models import DirectoryFile, DirectoryNode
from gonic_library_manager.services.scanner import is_audio_file


def build_directory_tree(root: Path | None = None, settings: Settings | None = None) -> DirectoryNode:
    settings = settings or get_settings()
    root = (root or settings.music_library_path).resolve()
    root.mkdir(parents=True, exist_ok=True)

    def walk(path: Path) -> DirectoryNode:
        directories: list[DirectoryNode] = []
        files: list[DirectoryFile] = []
        for child in sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            if child.name.startswith("."):
                continue
            if child.is_dir():
                directories.append(walk(child))
            elif is_audio_file(child, settings):
                files.append(
                    DirectoryFile(name=child.name, rel_path=child.relative_to(root).as_posix())
                )
        rel_path = "." if path == root else path.relative_to(root).as_posix()
        return DirectoryNode(path.name or str(path), rel_path, directories, files)

    return walk(root)
