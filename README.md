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
   - Physical directory browser at `/directories`
   - Health endpoint at `/healthz`

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

Future additions like tag editing, cover editing, auth, and background jobs should each get their own service/router/repository modules.

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

Then open <http://localhost:8080>.

Edit `docker-compose.yml` or `.env` so `/music` points at the same host folder gonic serves.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn gonic_library_manager.main:app --reload --app-dir app
```

## Gonic-friendly structure to aim for

```text
/music/
  Artist/
    Album/
      01 - Title.flac
      cover.jpg
```
