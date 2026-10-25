import asyncio
import sys
from temporalio.client import Client
from main import AIWorkloadWorkflow

async def main():
    # Explicitly use 127.0.0.1 to avoid local DNS/localhost lookup issues in venv
    client = await Client.connect("127.0.0.1:7233")
    
    simulate_fault = len(sys.argv) > 1 and sys.argv[1] == "--fault"
    print(f"Submitting AI Inference Workflow (Fault Injection: {simulate_fault})...")
    
    try:
        result = await client.execute_workflow(
            AIWorkloadWorkflow.run,
            simulate_fault,
            id="ai-inference-test-run",
            task_queue="ai-inference-task-queue",
        )
        print(f"✅ Workflow completed successfully: {result}")
    except Exception as e:
        print(f"❌ Workflow failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
