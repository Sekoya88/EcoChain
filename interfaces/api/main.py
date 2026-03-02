"""EcoChain AI — FastAPI Application.

Application FastAPI avec :
- Lifespan context manager pour l'initialisation/cleanup
- CORS middleware
- Middleware de logging structure
- Health check endpoint
- SSE events streaming
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from interfaces.api.dependencies import get_use_case, reset_dependencies
from interfaces.api.routers.documents import router as documents_router
from interfaces.api.routers.events import router as events_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager.

    Args:
        app: Instance FastAPI.

    Yields:
        None apres l'initialisation.
    """
    logger.info("Starting EcoChain AI API...")
    use_case = get_use_case()
    logger.info("EcoChain AI API ready (AGNO agents)")
    yield
    logger.info("Shutting down EcoChain AI API...")
    reset_dependencies()
    logger.info("Cleanup complete")


app = FastAPI(
    title="EcoChain AI",
    description=(
        "Supply Chain Carbon Footprint Optimization API. "
        "Analyzes logistics documents, calculates Scope 3 emissions, "
        "and generates reduction recommendations using AGNO multi-agent architecture."
    ),
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next: object) -> Response:
    """Middleware de logging structure.

    Args:
        request: Requete HTTP entrante.
        call_next: Callable pour passer au handler suivant.

    Returns:
        Response HTTP.
    """
    start_time = time.perf_counter()
    response: Response = await call_next(request)  # type: ignore[misc]
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "%s %s -> %d (%.0fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )

    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.0f}"
    return response


# Register routers
app.include_router(documents_router)
app.include_router(events_router)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status de l'application.
    """
    return {"status": "healthy", "service": "ecochain-ai", "version": "0.2.0"}


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        Information sur l'API.
    """
    return {
        "service": "EcoChain AI",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
        "events": "/api/v1/events/stream",
    }
