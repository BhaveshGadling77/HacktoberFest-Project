from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from app.integrations.temporal_client import (
    get_temporal_client,
    get_workflow_history,
    get_workflow_status,
)
from app.schemas.run import RunDetail, ActivityEvent, RunStatus
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import WorkflowError

logger = get_logger(__name__)

# Map Temporal event type names to our event types
EVENT_TYPE_MAP = {
    "WORKFLOW_EXECUTION_STARTED": "workflow_started",
    "ACTIVITY_TASK_SCHEDULED": "activity_scheduled",
    "ACTIVITY_TASK_STARTED": "activity_started",
    "ACTIVITY_TASK_COMPLETED": "activity_completed",
    "ACTIVITY_TASK_FAILED": "activity_failed",
    "ACTIVITY_TASK_TIMED_OUT": "activity_timed_out",
    "WORKFLOW_EXECUTION_COMPLETED": "workflow_completed",
    "WORKFLOW_EXECUTION_FAILED": "workflow_failed",
    "WORKFLOW_EXECUTION_CANCELED": "workflow_cancelled",
    "WORKFLOW_EXECUTION_TIMED_OUT": "workflow_timed_out",
    "TIMER_STARTED": "timer_started",
    "TIMER_FIRED": "timer_fired",
}

TEMPORAL_STATUS_MAP = {
    "RUNNING": RunStatus.RUNNING,
    "COMPLETED": RunStatus.COMPLETED,
    "FAILED": RunStatus.FAILED,
    "CANCELED": RunStatus.CANCELLED,
    "TERMINATED": RunStatus.FAILED,
    "CONTINUED_AS_NEW": RunStatus.RUNNING,
    "TIMED_OUT": RunStatus.TIMED_OUT,
}


class TemporalService:
    async def start_workflow(self, run_id: str, spec: dict) -> str:
        """Start InferenceWorkflow and return workflow_id."""
        client = await get_temporal_client()
        if client is None:
            raise WorkflowError("N/A", "Temporal is not connected")

        workflow_id = f"inference-{run_id}"
        try:
            from temporalio.common import RetryPolicy
            from datetime import timedelta

            # Import here to avoid import errors if temporalio not installed
            handle = await client.start_workflow(
                "InferenceWorkflow",
                spec,
                id=workflow_id,
                task_queue=settings.TEMPORAL_TASK_QUEUE,
            )
            logger.info("Started workflow", workflow_id=workflow_id, run_id=run_id)
            return workflow_id
        except Exception as e:
            logger.error("Failed to start workflow", run_id=run_id, error=str(e))
            raise WorkflowError(workflow_id, str(e))

    async def get_run_status(self, workflow_id: str) -> dict:
        """Get status of a workflow."""
        status_info = await get_workflow_status(workflow_id)
        return status_info

    async def get_run_timeline(self, workflow_id: str) -> List[ActivityEvent]:
        """Parse Temporal history into ActivityEvent list."""
        events = await get_workflow_history(workflow_id)
        return self._parse_events(events)

    def _parse_events(self, raw_events: List[dict]) -> List[ActivityEvent]:
        """Convert raw Temporal history events to ActivityEvent objects."""
        timeline: List[ActivityEvent] = []
        for evt in raw_events:
            event_type_raw = evt.get("event_type", "UNKNOWN")
            event_type = EVENT_TYPE_MAP.get(event_type_raw, event_type_raw.lower())
            attrs = evt.get("attributes", {})
            activity_name = attrs.get("activity_type", None)
            attempt = attrs.get("attempt", 1)
            failure_reason = attrs.get("failure_message", None)

            timeline.append(ActivityEvent(
                event_id=str(evt.get("event_id", str(uuid.uuid4()))),
                event_type=event_type,
                activity_name=activity_name,
                attempt=attempt,
                timestamp=evt.get("timestamp", datetime.now(timezone.utc).isoformat()),
                failure_reason=failure_reason,
            ))
        return timeline

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        client = await get_temporal_client()
        if client is None:
            return False
        try:
            handle = client.get_workflow_handle(workflow_id)
            await handle.cancel()
            logger.info("Cancelled workflow", workflow_id=workflow_id)
            return True
        except Exception as e:
            logger.error("Failed to cancel workflow", workflow_id=workflow_id, error=str(e))
            return False

    def map_temporal_status(self, temporal_status: str) -> str:
        """Map Temporal status string to our RunStatus."""
        return TEMPORAL_STATUS_MAP.get(temporal_status, RunStatus.PENDING).value
