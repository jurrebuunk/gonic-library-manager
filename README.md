# Gonic Library Manager

Simple drop-in music library manager for a gonic-compatible music directory.

## Stack

**Python FastAPI + server-rendered templates/HTMX later + SQLite + Mutagen + yt-dlp + Docker**.

Why this stack:

- **FastAPI**: small backend/API, easy Docker deployment, good modular routing.
- **Server-rendered templates first**: enough for library/directory views without a frontend build step. HTMX can be added per component later.
- **SQLite**: single-file index database in `/data`, perfect for a drop-in container.
- **Mutagen**: reads audio tags now and can edit tags/cover art in the next milestone.
- **yt-dlp + ffmpeg**: planned for download/conversion background jobs.
- **Docker Compose**: mount the exact same music directory gonic serves.

## Implemented so far

1. **Project foundation + Docker setup**
   - FastAPI app factory
   - Dockerfile and docker-compose
   - Environment-based config
   - `/music` and `/data` mounts

2. **Music library scanner**
   - Recursive scanner for common audio extensions
   - Mutagen metadata reader
   - SQLite track index
   - Missing-file cleanup on rescan

3. **Library view + directory view**
   - Searchable library table at `/`
   - Grid view at `/?view=grid`
   - Selectable rows/cards with the right-side inspector updating from `selected_id`
   - Physical directory browser at `/directories`
   - Filterable nested directory table matching the Sonic Ledger design
   - Folder/audio/image icons in the directory manager
   - Albums and artists navigation pages, plus a placeholder Tools tab
   - Album cards can use folder artwork like `folder.jpg`/`folder.png`
   - Editable tag inspector for common tags
   - Cover-art upload/replacement from the inspector
   - Song deletion and album deletion
   - yt-dlp download tool at `/tools/downloads` with a cancellable background queue
   - Health endpoint at `/healthz`

Still intentionally not included yet: auth.

## Modular layout

```text
app/gonic_library_manager/
  core/           config and app-wide utilities
  db/             SQLite connection/schema
  models.py       app data models
  repositories/   database access
  services/       scanner, metadata, directory tree logic
  routers/        FastAPI route modules
  templates/      server-rendered HTML
  static/         CSS/assets
```

Future additions like auth should get their own service/router/repository modules.

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

Then open <http://localhost:8080>.

Edit `docker-compose.yml` or `.env` so `/music` points at the same host folder gonic serves.

## Pull the published image

GitHub Actions publishes the image to GitHub Container Registry on every push to `main`:

```bash
docker pull ghcr.io/jurrebuunk/gonic-library-manager:latest
```

If the repository/package is private, log in on the production host first:

```bash
echo YOUR_GITHUB_PAT | docker login ghcr.io -u jurrebuunk --password-stdin
```

## Local development with Nix

Enter the dev shell:

```bash
nix develop
```

Run the app locally:

```bash
uvicorn gonic_library_manager.main:app --reload --app-dir app --host 127.0.0.1 --port 8080
```

Then open <http://127.0.0.1:8080>.

The Nix dev shell defaults to:

- `MUSIC_LIBRARY_PATH=$PWD/example-music`
- `DATA_DIR=$PWD/data`

You can also run without entering the shell:

```bash
nix develop -c uvicorn gonic_library_manager.main:app --reload --app-dir app --host 127.0.0.1 --port 8080
```

Run tests:

```bash
nix develop -c python -m unittest discover -s tests -v
```

Open the download tool at <http://127.0.0.1:8080/tools/downloads>. It uses yt-dlp and ffmpeg
from the dev shell, stores task logs under `DATA_DIR/download-logs`, and runs up to
`DOWNLOAD_CONCURRENCY` downloads at the same time.

## Local development with Python venv

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn gonic_library_manager.main:app --reload --app-dir app
```

Install `ffmpeg` on the host when using the Python venv path; yt-dlp needs it for audio
conversion, metadata embedding, and cover art embedding.

## Gonic-friendly structure to aim for

```text
/music/
  Artist/
    Album/
      01 - Title.flac
      folder.jpg
```
