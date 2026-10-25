from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import init_db
from app.api.routes import health
from app.api.router import api_router
from app.core.exceptions import NotFoundError, ValidationError, IntegrationError, WorkflowError

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Compute CSI backend...", db_url=settings.DATABASE_URL)
    try:
        await init_db()
    except Exception as e:
        logger.warning("Database initialization deferred or failed", error=str(e))
    yield
    logger.info("Shutting down Compute CSI backend...")


app = FastAPI(
    title="Compute CSI — AI Infrastructure Forensics API",
    description="Evidence-based root-cause analysis and observability for AI workloads.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router)
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api")


# Global Exception Handlers
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "error_type": "NotFoundError"},
    )


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc), "error_type": "ValidationError"},
    )


@app.exception_handler(IntegrationError)
async def integration_handler(request: Request, exc: IntegrationError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc), "error_type": "IntegrationError"},
    )


@app.exception_handler(WorkflowError)
async def workflow_handler(request: Request, exc: WorkflowError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc), "error_type": "WorkflowError"},
    )
