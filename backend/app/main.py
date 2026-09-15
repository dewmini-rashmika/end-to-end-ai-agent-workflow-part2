"""
TripMate AI — FastAPI application entry point.

Startup sequence:
  1. Configure logging
  2. Connect to DB + run migrations
  3. Seed RAG knowledge base
  4. Register routes + middleware
"""
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config.settings import settings
from app.config.logging_config import configure_logging, get_logger
from app.db.base import create_all_tables
from app.routes import auth_router, trip_router, thread_router, rag_router

# Configure logging first
configure_logging()
logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    logger.info(
        "tripmate_starting",
        version=settings.APP_VERSION,
        env=settings.APP_ENV,
    )

    # Create DB tables (Alembic handles prod migrations, this covers dev)
    if settings.APP_ENV == "development":
        try:
            await create_all_tables()
            logger.info("db_tables_ready")
        except Exception as e:
            logger.warning("db_table_creation_warning", error=str(e))

    # Seed RAG knowledge base (no-op if already seeded)
    try:
        from app.rag.retriever import ingest_travel_knowledge
        await ingest_travel_knowledge()
    except Exception as e:
        logger.warning("rag_seed_warning", error=str(e))

    logger.info("tripmate_started")
    yield

    logger.info("tripmate_shutdown")


# ── Rate limiter ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-grade AI travel planner with multi-agent architecture, "
            "MCP servers, HITL review, guardrails, RAG, and LiteLLM."
        ),
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── State ─────────────────────────────────────────────────────────────────
    app.state.limiter = limiter

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred. Please try again."},
        )

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(elapsed)
        return response

    # ── Routes ────────────────────────────────────────────────────────────────
    API_PREFIX = "/api/v1"
    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(trip_router, prefix=API_PREFIX)
    app.include_router(thread_router, prefix=API_PREFIX)
    app.include_router(rag_router, prefix=API_PREFIX)

    # ── Health endpoints ──────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
        }

    @app.get("/health/detailed", tags=["Health"])
    async def detailed_health():
        """Check DB and Redis connectivity."""
        checks: dict = {}

        # DB check
        try:
            from app.db.base import engine
            async with engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {str(e)}"

        # RAG check
        try:
            from app.rag.vector_store import vector_store
            count = await vector_store.count()
            checks["rag"] = f"ok ({count} docs)"
        except Exception as e:
            checks["rag"] = f"unavailable: {str(e)}"

        overall = "healthy" if all("error" not in v for v in checks.values()) else "degraded"
        return {"status": overall, "checks": checks}

    return app


app = create_app()


# ── Dev entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
