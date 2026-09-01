import sqlite3
from collections.abc import Iterator

from fastapi import Request
from fastapi.templating import Jinja2Templates

from gonic_library_manager.db.connection import connect


def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


def get_db() -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
