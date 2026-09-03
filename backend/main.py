"""FastAPI application factory.

Run with::

    uvicorn main:app --reload --port 8000

The app exposes:
    GET  /health          → liveness probe
    GET  /docs            → Swagger UI (debug only)
    GET  /redoc           → ReDoc (debug only)
    /api/auth/*           → auth routes
    /api/artifacts/*      → artifact routes
    /api/attempts/*       → attempt routes
    /api/mastery/*        → mastery routes
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import api_router
from config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Run startup / shutdown logic.

    Startup: warm the settings cache and the Supabase client so the first
    request doesn't pay the initialisation cost.
    """
    settings = get_settings()

    # Eagerly import domain registry to surface any mis-configuration early.
    from domains import DOMAIN_REGISTRY  # noqa: F401

    print(
        f"✓ Repair API v{settings.app_version} starting — "
        f"{len(DOMAIN_REGISTRY)} domain(s) loaded: {list(DOMAIN_REGISTRY)}"
    )
    yield
    print("✓ Repair API shutting down.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    from api.verification import router as verification_router
    app.include_router(api_router)
    app.include_router(verification_router)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
