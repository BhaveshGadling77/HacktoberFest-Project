from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.schemas.incident import IncidentSummary, InvestigationReport
from app.schemas.common import PaginatedResponse
from app.services.incident_service import IncidentService
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/incidents", tags=["Incidents"])
incident_service = IncidentService()


@router.get("", response_model=PaginatedResponse[IncidentSummary])
async def list_incidents(
    severity: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return await incident_service.list_incidents(
        severity=severity,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/{incident_id}", response_model=InvestigationReport)
async def get_incident(incident_id: str):
    try:
        return await incident_service.get_incident_report(incident_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{incident_id}/investigate", response_model=InvestigationReport)
async def investigate_incident(incident_id: str):
    try:
        return await incident_service.investigate_incident(incident_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/from-run/{run_id}", response_model=IncidentSummary, status_code=status.HTTP_201_CREATED)
async def create_incident_from_run(run_id: str):
    try:
        return await incident_service.create_incident_for_run(run_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
