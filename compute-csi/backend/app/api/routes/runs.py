from __future__ import annotations

from typing import List
from fastapi import APIRouter, Query, HTTPException, status
from app.schemas.run import RunDetail, RunSummary, ActivityEvent
from app.schemas.metrics import RunMetrics
from app.schemas.common import PaginatedResponse
from app.services.workload_service import WorkloadService
from app.services.metrics_service import MetricsService
from app.services.investigation_engine import InvestigationEngine
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/runs", tags=["Runs"])
workload_service = WorkloadService()
metrics_service = MetricsService()
investigation_engine = InvestigationEngine()


@router.post("/{run_id}/investigate")
async def investigate_run_endpoint(run_id: str):
    try:
        return await investigation_engine.investigate_run(run_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=PaginatedResponse[RunSummary])
async def list_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return await workload_service.list_runs(page=page, page_size=page_size)


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(run_id: str):
    try:
        return await workload_service.get_run(run_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{run_id}/cancel")
async def cancel_run(run_id: str):
    success = await workload_service.cancel_run(run_id)
    return {"cancelled": success}


@router.get("/{run_id}/timeline", response_model=List[ActivityEvent])
async def get_run_timeline(run_id: str):
    try:
        run = await workload_service.get_run(run_id)
        return run.timeline
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{run_id}/metrics", response_model=RunMetrics)
async def get_run_metrics(run_id: str):
    try:
        run = await workload_service.get_run(run_id)
        return await metrics_service.get_run_metrics(
            run_id=run.run_id,
            start_time=run.start_time,
            end_time=run.end_time,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
