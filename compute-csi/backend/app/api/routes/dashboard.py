from __future__ import annotations

import json
from fastapi import APIRouter
from app.database.session import AsyncSessionLocal
from app.database.repositories import WorkloadRunRepository, IncidentRepository
from app.schemas.run import RunSummary
from app.schemas.incident import IncidentSummary
from app.integrations.temporal_client import get_temporal_client
from app.integrations.prometheus_client import PrometheusClient
from app.integrations.kepler_adapter import KeplerAdapter
from app.integrations.gemma_adapter import GemmaAdapter
from app.integrations.jarvislabs_adapter import JarvisLabsAdapter
from app.core.config import settings

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
@router.get("/")
@router.get("/summary")
async def get_dashboard_summary():
    async with AsyncSessionLocal() as session:
        run_repo = WorkloadRunRepository(session)
        inc_repo = IncidentRepository(session)

        # Runs count
        all_runs, total_runs = await run_repo.list_all(page=1, page_size=100)
        active_runs = sum(1 for r in all_runs if r.status in ("RUNNING", "PENDING"))
        failed_runs = sum(1 for r in all_runs if r.status in ("FAILED", "TIMED_OUT"))
        total_retries = await run_repo.sum_retries()

        recent_runs_db = await run_repo.get_recent(limit=5)
        recent_runs = [
            RunSummary(
                run_id=r.id,
                workflow_id=r.workflow_id,
                status=r.status,
                start_time=r.start_time,
                duration_seconds=r.duration_seconds,
                attempt_count=r.attempt_count,
                failure_count=r.failure_count,
            )
            for r in recent_runs_db
        ]

        # Incidents
        detected_incidents = await inc_repo.count_all()
        recent_inc_db = await inc_repo.get_recent(limit=5)
        recent_incidents = [
            IncidentSummary(
                incident_id=i.id,
                run_id=i.run_id,
                title=i.title,
                severity=i.severity,
                status=i.status,
                finding_types=json.loads(i.finding_types_json) if i.finding_types_json else [],
                created_at=i.created_at,
            )
            for i in recent_inc_db
        ]

    # Health checks
    temporal_connected = (await get_temporal_client()) is not None
    prom_client = PrometheusClient()
    prom_connected = await prom_client.check_connection()

    kepler_adapter = KeplerAdapter(prom_client)
    kepler_metrics = await kepler_adapter.discover_available_metrics()
    kepler_connected = len(kepler_metrics) > 0

    gemma_adapter = GemmaAdapter()
    gemma_connected = await gemma_adapter.check_connection()

    jarvislabs_adapter = JarvisLabsAdapter()
    jl_status = await jarvislabs_adapter.check_status()

    return {
        "total_runs": total_runs,
        "active_runs": active_runs,
        "failed_runs": failed_runs,
        "detected_incidents": detected_incidents,
        "total_retries": total_retries,
        "energy_metrics_available": kepler_connected,
        "recent_runs": [r.model_dump() for r in recent_runs],
        "recent_incidents": [i.model_dump() for i in recent_incidents],
        "integration_health": {
            "temporal": {"connected": temporal_connected, "address": settings.TEMPORAL_ADDRESS},
            "prometheus": {"connected": prom_connected, "url": settings.PROMETHEUS_URL},
            "kepler": {"connected": kepler_connected, "available_metrics": kepler_metrics},
            "gemma": {"connected": gemma_connected, "model": settings.GEMMA_MODEL},
            "jarvislabs": jl_status,
        },
    }
