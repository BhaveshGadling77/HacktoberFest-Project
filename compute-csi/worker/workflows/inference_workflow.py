from __future__ import annotations

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities.inference import run_inference_activity


@workflow.defn(name="InferenceWorkflow")
class InferenceWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        max_retries = int(params.get("max_retries", 3))
        
        # Configure retry policy so that activity failures cause Temporal to retry
        retry_policy = RetryPolicy(
            maximum_attempts=max_retries,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            backoff_coefficient=2.0,
        )

        result = await workflow.execute_activity(
            run_inference_activity,
            params,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )
        return result
