FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken
WORKDIR /app

RUN pip install --no-cache-dir \
    "lightrag-hku[api]" \
    fastapi \
    "uvicorn[standard]" \
    gunicorn \
    "PyJWT>=2,<3" \
    bcrypt \
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

RUN mkdir -p "$TIKTOKEN_CACHE_DIR" \
    && python -m lightrag.tools.download_cache \
        --cache-dir "$TIKTOKEN_CACHE_DIR" \
        --models \
            gpt-4o-mini \
            gpt-4o \
            text-embedding-3-small \
            text-embedding-3-large \
            cl100k_base \
            o200k_base

EXPOSE 9621

CMD ["python", "-m", "lightrag.api.lightrag_server"]
