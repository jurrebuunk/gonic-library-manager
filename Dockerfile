FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install .

EXPOSE 8080

CMD ["uvicorn", "gonic_library_manager.main:app", "--host", "0.0.0.0", "--port", "8080", "--app-dir", "app"]
