from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from gonic_library_manager.core.config import ensure_runtime_dirs, get_settings
from gonic_library_manager.db.connection import connect, init_db
from gonic_library_manager.routers import directories, library, system

PACKAGE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ensure_runtime_dirs(settings)
    init_db(settings)
    app.state.db = connect(settings)
    try:
        yield
    finally:
        app.state.db.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
    app.mount("/static", StaticFiles(directory=str(PACKAGE_DIR / "static")), name="static")
    app.include_router(library.router)
    app.include_router(directories.router)
    app.include_router(system.router)
    return app


app = create_app()
