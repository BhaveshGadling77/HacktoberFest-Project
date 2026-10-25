from __future__ import annotations

from typing import Optional, List
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_temporal_client = None


async def get_temporal_client():
    """Get or create Temporal client. Returns None on connection error."""
    global _temporal_client
    if _temporal_client is not None:
        return _temporal_client
    try:
        from temporalio.client import Client
        client = await Client.connect(
            settings.TEMPORAL_ADDRESS,
            namespace=settings.TEMPORAL_NAMESPACE,
        )
        _temporal_client = client
        logger.info("Connected to Temporal", address=settings.TEMPORAL_ADDRESS)
        return client
    except Exception as e:
        logger.error("Failed to connect to Temporal", error=str(e))
        return None


async def reset_temporal_client() -> None:
    global _temporal_client
    _temporal_client = None


async def get_workflow_history(workflow_id: str, run_id: Optional[str] = None) -> List[dict]:
    """Fetch workflow history events as list of dicts."""
    client = await get_temporal_client()
    if client is None:
        return []
    try:
        handle = client.get_workflow_handle(workflow_id, run_id=run_id)
        events = []
        async for event in handle.fetch_history_events():
            try:
                from temporalio.api.enums.v1 import EventType
                ev_name = EventType.Name(event.event_type).removeprefix("EVENT_TYPE_")
            except Exception:
                ev_name = str(event.event_type)

            event_time = event.event_time
            if event_time:
                # Temporal history timestamps are protobuf Timestamp values.
                event_timestamp = event_time.ToDatetime(tzinfo=timezone.utc).isoformat()
            else:
                event_timestamp = datetime.now(timezone.utc).isoformat()

            event_dict = {
                "event_id": str(event.event_id),
                "event_type": ev_name,
                "timestamp": event_timestamp,
                "attributes": {},
            }
            # Extract common attributes safely
            attr_name = None
            for attr_field in [
                "activity_task_scheduled_event_attributes",
                "activity_task_started_event_attributes",
                "activity_task_completed_event_attributes",
                "activity_task_failed_event_attributes",
                "activity_task_timed_out_event_attributes",
                "workflow_execution_started_event_attributes",
                "workflow_execution_completed_event_attributes",
                "workflow_execution_failed_event_attributes",
            ]:
                attr = getattr(event, attr_field, None)
                if attr is not None:
                    attr_name = attr_field
                    try:
                        if hasattr(attr, "activity_type"):
                            event_dict["attributes"]["activity_type"] = attr.activity_type.name if attr.activity_type else ""
                        if hasattr(attr, "attempt"):
                            event_dict["attributes"]["attempt"] = attr.attempt
                        if hasattr(attr, "failure") and attr.failure:
                            event_dict["attributes"]["failure_message"] = attr.failure.message
                    except Exception:
                        pass
                    break
            events.append(event_dict)
        return events
    except Exception as e:
        logger.error("Failed to fetch workflow history", workflow_id=workflow_id, error=str(e))
        return []


async def get_workflow_status(workflow_id: str) -> dict:
    """Get workflow execution status info."""
    client = await get_temporal_client()
    if client is None:
        return {"status": "UNKNOWN", "error": "Temporal not connected"}
    try:
        from temporalio.client import WorkflowExecutionStatus
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        status_name = desc.status.name if desc.status else "UNKNOWN"
        start_time = desc.start_time.isoformat() if desc.start_time else None
        close_time = desc.close_time.isoformat() if desc.close_time else None
        return {
            "status": status_name,
            "start_time": start_time,
            "close_time": close_time,
            "attempt_count": getattr(desc, "execution_time", None),
            "raw": {},
        }
    except Exception as e:
        logger.error("Failed to get workflow status", workflow_id=workflow_id, error=str(e))
        return {"status": "UNKNOWN", "error": str(e)}
