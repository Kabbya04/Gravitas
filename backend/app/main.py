from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import documents, drafts, health
from app.core.settings import get_settings
from app.core.yaml_config import get_yaml_config
from app.db.database import get_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_engine()
    yield


def create_app() -> FastAPI:
    y = get_yaml_config()
    app = FastAPI(title=y.get("app", {}).get("name", "gravitas-api"), lifespan=lifespan)

    origins = list(y.get("app", {}).get("cors_origins", []))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(drafts.router)
    return app


app = create_app()
