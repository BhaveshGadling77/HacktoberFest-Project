from __future__ import annotations

import asyncio
import uuid
import pytest
from temporalio.client import Client
from temporalio.worker import Worker
from workflows.inference_workflow import InferenceWorkflow
from activities.inference import run_inference_activity


@pytest.mark.asyncio
async def test_live_workflow_with_injected_fault_retry():
    client = await Client.connect("localhost:7233", namespace="default")
    queue_name = f"test-queue-{uuid.uuid4().hex[:8]}"

    # Run worker in background
    async with Worker(
        client,
        task_queue=queue_name,
        workflows=[InferenceWorkflow],
        activities=[run_inference_activity],
    ):
        # Execute workflow with FIRST_ATTEMPT_FAIL
        run_id = str(uuid.uuid4())
        workflow_id = f"test-run-{run_id}"

        result = await client.execute_workflow(
            InferenceWorkflow.run,
            {
                "run_id": run_id,
                "workload_type": "LOCAL_CPU",
                "execution_mode": "FAULT_RETRY",
                "fault_scenario": "FIRST_ATTEMPT_FAIL",
                "input_size": 50,
                "max_retries": 3,
            },
            id=workflow_id,
            task_queue=queue_name,
        )

        assert result["status"] == "SUCCESS"
        assert result["attempt"] == 2  # Proves retry succeeded after initial failure!
        assert "inference_output" in result

        # Check Temporal workflow history
        from temporalio.api.enums.v1 import EventType
        handle = client.get_workflow_handle(workflow_id)
        events = []
        async for event in handle.fetch_history_events():
            events.append(EventType.Name(event.event_type))

        assert "EVENT_TYPE_WORKFLOW_EXECUTION_STARTED" in events
        assert "EVENT_TYPE_ACTIVITY_TASK_STARTED" in events
        assert "EVENT_TYPE_ACTIVITY_TASK_COMPLETED" in events  # Proves completion on retry
        assert "EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED" in events
