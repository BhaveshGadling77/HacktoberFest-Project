from __future__ import annotations

import asyncio
import os
import sys
from temporalio.client import Client
from temporalio.worker import Worker

# Add parent directory to path so relative imports work seamlessly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows.inference_workflow import InferenceWorkflow
from activities.inference import run_inference_activity


async def run_worker():
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "compute-csi-queue")

    print(f"Connecting to Temporal server at {temporal_address} (namespace: {temporal_namespace})...")
    client = await Client.connect(temporal_address, namespace=temporal_namespace)
    print(f"Temporal client connected. Registering worker on task queue '{task_queue}'...")

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[InferenceWorkflow],
        activities=[run_inference_activity],
    )

    print("Compute CSI Temporal Worker active. Waiting for inference workflows...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
