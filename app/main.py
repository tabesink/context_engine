from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    admin,
    ai_settings,
    auth,
    documents,
    health,
    jobs,
    lightrag,
    lightrag_admin,
    lightrag_domains,
    operations,
    retrieve,
    users,
    workspace_tree,
)
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    del app
    configure_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(documents.router)
    app.include_router(admin.router)
    app.include_router(ai_settings.router)
    app.include_router(retrieve.router)
    app.include_router(lightrag.router)
    app.include_router(lightrag_admin.router)
    app.include_router(lightrag_domains.router)
    app.include_router(users.router)
    app.include_router(workspace_tree.router)
    app.include_router(jobs.router)
    app.include_router(operations.router)
    return app


app = create_app()

