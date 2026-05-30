from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import badges, collect, health, usage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="wakatoken token usage backend",
        version="0.1.0",
        description="Collect ccusage JSON, aggregate token usage, and serve public SVG badges.",
        lifespan=lifespan,
    )

    origins = ["*"] if settings.cors_origins == "*" else [origin.strip() for origin in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(collect.router)
    app.include_router(usage.router)
    app.include_router(badges.router)
    return app


app = create_app()
