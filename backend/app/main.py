"""AgentForge FastAPI application entrypoint."""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.base import Base
from app.db.session import engine

import app.models  # noqa: F401  (register all tables on Base.metadata)

configure_logging()
logger = get_logger("agentforge.main")

HTTP_REQUESTS = Counter(
    "agentforge_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_LATENCY = Histogram(
    "agentforge_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev convenience; alembic owns prod migrations)."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database tables ensured", environment=settings.ENVIRONMENT)
        from app.db.session import async_session_factory
        from app.services.seed import seed_builtin_templates

        async with async_session_factory() as session:
            await seed_builtin_templates(session)
    except Exception as exc:  # noqa: BLE001
        logger.warning("could not initialize database", error=str(exc))
    yield
    await engine.dispose()


app = FastAPI(
    title="AgentForge API",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # allow any Render-hosted frontend without hard-wiring its URL at deploy time
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next) -> Response:
    """Record request counts and latency for Prometheus."""
    start = time.perf_counter()
    response = await call_next(request)
    path = request.scope.get("route").path if request.scope.get("route") else request.url.path
    HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    HTTP_LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
    return response


@app.get("/health", tags=["ops"])
async def health() -> dict:
    """Liveness probe."""
    return {"status": "ok", "service": "agentforge-backend", "environment": settings.ENVIRONMENT}


app.mount("/metrics", make_asgi_app())

app.include_router(api_router, prefix="/api/v1")
