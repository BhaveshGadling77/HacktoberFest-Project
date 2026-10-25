from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    dashboard,
    workloads,
    runs,
    incidents,
    metrics,
    integrations,
)

api_router = APIRouter()

api_router.include_router(dashboard.router)
api_router.include_router(workloads.router)
api_router.include_router(runs.router)
api_router.include_router(incidents.router)
api_router.include_router(metrics.router)
api_router.include_router(integrations.router)
