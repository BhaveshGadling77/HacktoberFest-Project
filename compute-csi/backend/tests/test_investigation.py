from __future__ import annotations

import pytest
import uuid
from app.services.investigation_engine import InvestigationEngine
from app.database.session import AsyncSessionLocal, init_db
from app.database.repositories import WorkloadRunRepository
from app.schemas.incident import FindingType


@pytest.mark.asyncio
async def test_investigation_retry_detection():
    await init_db()
    run_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        repo = WorkloadRunRepository(session)
        await repo.create({
            "id": run_id,
            "workflow_id": f"test-workflow-{run_id}",
            "workload_type": "LOCAL_CPU",
            "execution_mode": "FAULT_RETRY",
            "fault_scenario": "FIRST_ATTEMPT_FAIL",
            "status": "COMPLETED",
            "start_time": "2026-10-25T10:00:00Z",
            "end_time": "2026-10-25T10:00:05Z",
            "duration_seconds": 5.2,
            "attempt_count": 2,
            "failure_count": 1,
            "outcome": "SUCCESS",
        })

    engine = InvestigationEngine()
    report = await engine.investigate_run(run_id)

    assert report.run_id == run_id
    finding_types = [f.finding_type for f in report.findings]
    assert FindingType.REPEATED_ATTEMPTS in finding_types
    assert FindingType.FAILED_ATTEMPTS in finding_types
    
    # Assert energy anomaly is NEVER claimed when energy data is missing
    assert FindingType.ENERGY_ANOMALY not in finding_types
    assert FindingType.MISSING_DATA in finding_types
    assert any("Kepler energy metrics were unavailable" in lim for lim in report.limitations)
