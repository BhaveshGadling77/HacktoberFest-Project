import asyncio
from datetime import timedelta
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

@activity.defn
async def run_ai_inference(simulate_fault: bool) -> str:
    if simulate_fault:
        raise Exception("Simulated inference failure (e.g. OOM or network timeout)")
    return "Inference completed successfully"

@workflow.defn
class AIWorkloadWorkflow:
    @workflow.run
    async def run(self, simulate_fault: bool) -> str:
        return await workflow.execute_activity(
            run_ai_inference,
            simulate_fault,
            start_to_close_timeout=timedelta(seconds=10),
        )

async def main():
    # Explicitly use 127.0.0.1 to avoid local DNS/localhost lookup issues in venv
    client = await Client.connect("127.0.0.1:7233")
    worker = Worker(
        client,
        task_queue="ai-inference-task-queue",
        workflows=[AIWorkloadWorkflow],
        activities=[run_ai_inference],
    )
    print("Starting Temporal worker on 127.0.0.1:7233...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
