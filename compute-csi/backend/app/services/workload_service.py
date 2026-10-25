from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import WorkloadRunRepository
from app.database.session import AsyncSessionLocal
from app.schemas.workload import WorkloadSpec, StartRunResponse
from app.schemas.run import RunDetail, RunSummary, ActivityEvent, RunStatus
from app.schemas.common import PaginatedResponse
from app.services.temporal_service import TemporalService
from app.core.logging import get_logger
from app.core.exceptions import NotFoundError

logger = get_logger(__name__)


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkloadService:
    def __init__(self) -> None:
        self.temporal = TemporalService()

    async def create_run(self, spec: WorkloadSpec) -> StartRunResponse:
        """Create a new workload run, store in DB, start Temporal workflow."""
        run_id = str(uuid.uuid4())
        workflow_id = f"inference-{run_id}"

        async with AsyncSessionLocal() as session:
            repo = WorkloadRunRepository(session)
            await repo.create({
                "id": run_id,
                "workflow_id": workflow_id,
                "workload_type": spec.workload_type.value,
                "execution_mode": spec.execution_mode.value,
                "fault_scenario": spec.fault_scenario.value,
                "status": RunStatus.PENDING.value,
                "start_time": utcnow_iso(),
                "metadata_json": json.dumps(spec.model_dump()),
            })

        # Start Temporal workflow
        actual_workflow_id = workflow_id
        message = "Run started"
        try:
            actual_workflow_id = await self.temporal.start_workflow(
                run_id=run_id,
                spec={
                    "run_id": run_id,
                    "workload_type": spec.workload_type.value,
                    "execution_mode": spec.execution_mode.value,
                    "fault_scenario": spec.fault_scenario.value,
                    "input_size": spec.input_size,
                    "delay_seconds": spec.delay_seconds,
                    "max_retries": spec.max_retries,
                },
            )
            # Update DB with running status
            async with AsyncSessionLocal() as session:
                repo = WorkloadRunRepository(session)
                await repo.update(run_id, {
                    "workflow_id": actual_workflow_id,
                    "status": RunStatus.RUNNING.value,
                })
        except Exception as e:
            logger.warning("Temporal unavailable, run created in PENDING state", error=str(e))
            message = "Run created but Temporal is not available. Will remain PENDING."

        return StartRunResponse(
            run_id=run_id,
            workflow_id=actual_workflow_id,
            status=RunStatus.RUNNING.value if message == "Run started" else RunStatus.PENDING.value,
            message=message,
        )

    async def list_runs(self, page: int = 1, page_size: int = 20) -> PaginatedResponse[RunSummary]:
        """List all runs with pagination."""
        async with AsyncSessionLocal() as session:
            repo = WorkloadRunRepository(session)
            runs, total = await repo.list_all(page=page, page_size=page_size)
            summaries = [
                RunSummary(
                    run_id=r.id,
                    workflow_id=r.workflow_id,
                    status=r.status,
                    start_time=r.start_time,
                    duration_seconds=r.duration_seconds,
                    attempt_count=r.attempt_count,
                    failure_count=r.failure_count,
                )
                for r in runs
            ]
        return PaginatedResponse.build(summaries, total, page, page_size)

    async def get_run(self, run_id: str) -> RunDetail:
        """Get full run detail, syncing from Temporal if needed."""
        await self.sync_run_status(run_id)
        async with AsyncSessionLocal() as session:
            repo = WorkloadRunRepository(session)
            run = await repo.get_by_id(run_id)
            if not run:
                raise NotFoundError("Run", run_id)

            timeline: List[ActivityEvent] = []
            if run.workflow_id:
                try:
                    timeline = await self.temporal.get_run_timeline(run.workflow_id)
                except Exception as e:
                    logger.warning("Could not fetch timeline", run_id=run_id, error=str(e))

            return RunDetail(
                run_id=run.id,
                workflow_id=run.workflow_id,
                workload_type=run.workload_type,
                execution_mode=run.execution_mode,
                fault_scenario=run.fault_scenario,
                status=run.status,
                start_time=run.start_time,
                end_time=run.end_time,
                duration_seconds=run.duration_seconds,
                attempt_count=run.attempt_count,
                failure_count=run.failure_count,
                outcome=run.outcome,
                timeline=timeline,
            )

    async def cancel_run(self, run_id: str) -> bool:
        """Cancel a running workflow."""
        async with AsyncSessionLocal() as session:
            repo = WorkloadRunRepository(session)
            run = await repo.get_by_id(run_id)
            if not run:
                raise NotFoundError("Run", run_id)
            if not run.workflow_id:
                return False
            cancelled = await self.temporal.cancel_workflow(run.workflow_id)
            if cancelled:
                await repo.update(run_id, {"status": RunStatus.CANCELLED.value})
            return cancelled

    async def sync_run_status(self, run_id: str) -> None:
        """Sync run status from Temporal into DB."""
        async with AsyncSessionLocal() as session:
            repo = WorkloadRunRepository(session)
            run = await repo.get_by_id(run_id)
            if not run or not run.workflow_id:
                return
            if run.status in (RunStatus.COMPLETED.value, RunStatus.FAILED.value,
                              RunStatus.CANCELLED.value, RunStatus.TIMED_OUT.value):
                return  # Already terminal

        try:
            status_info = await self.temporal.get_run_status(run.workflow_id)
            temporal_status = status_info.get("status", "UNKNOWN")
            mapped_status = self.temporal.map_temporal_status(temporal_status)

            update_data: dict = {"status": mapped_status}
            if temporal_status in ("COMPLETED", "FAILED", "CANCELED", "TIMED_OUT"):
                update_data["end_time"] = status_info.get("close_time") or utcnow_iso()
                if run.start_time and update_data.get("end_time"):
                    try:
                        start = datetime.fromisoformat(run.start_time)
                        end = datetime.fromisoformat(update_data["end_time"])
                        update_data["duration_seconds"] = (end - start).total_seconds()
                    except Exception:
                        pass

            # Count attempts from timeline
            timeline = await self.temporal.get_run_timeline(run.workflow_id)
            attempt_count = sum(1 for e in timeline if e.event_type == "activity_started")
            failure_count = sum(1 for e in timeline if e.event_type in ("activity_failed", "activity_timed_out"))
            if attempt_count > 0:
                update_data["attempt_count"] = attempt_count
            if failure_count > 0:
                update_data["failure_count"] = failure_count

            async with AsyncSessionLocal() as session:
                repo = WorkloadRunRepository(session)
                await repo.update(run_id, update_data)
        except Exception as e:
            logger.warning("Failed to sync run status", run_id=run_id, error=str(e))
