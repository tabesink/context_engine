FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    gunicorn \
    python-multipart \
    httpx \
    pydantic \
    pydantic-settings \
    python-dotenv \
    numpy \
    tenacity \
    pipmaster \
    asyncpg \
    pgvector \
    redis

COPY external/lightrag /app/lightrag

EXPOSE 9621

CMD ["python", "-m", "lightrag.api.lightrag_server"]
