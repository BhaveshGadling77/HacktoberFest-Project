from __future__ import annotations

from typing import List, Dict, Any
from fastapi import APIRouter, status
from app.schemas.workload import StartRunRequest, StartRunResponse, WorkloadType, ExecutionMode, FaultScenario
from app.services.workload_service import WorkloadService

router = APIRouter(prefix="", tags=["Workloads"])
workload_service = WorkloadService()


@router.get("/workloads")
async def list_workload_templates() -> List[Dict[str, Any]]:
    """Return available workload templates and execution modes."""
    return [
        {
            "id": "cpu-inference-simulation",
            "name": "Local CPU Inference Benchmark",
            "description": "Standard matrix compute simulation suitable for local development without GPU access.",
            "workload_type": WorkloadType.LOCAL_CPU.value,
            "supported_modes": [m.value for m in ExecutionMode],
            "supported_faults": [f.value for f in FaultScenario],
        },
        {
            "id": "gpu-jarvislabs-remote",
            "name": "Remote GPU JarvisLabs Inference",
            "description": "Real remote GPU-accelerated inference cluster (requires JarvisLabs credentials).",
            "workload_type": WorkloadType.REMOTE_GPU.value,
            "supported_modes": [ExecutionMode.NORMAL.value, ExecutionMode.FAULT_RETRY.value],
            "supported_faults": [FaultScenario.NONE.value, FaultScenario.FIRST_ATTEMPT_FAIL.value],
        },
    ]


@router.post("/runs", response_model=StartRunResponse, status_code=status.HTTP_201_CREATED)
@router.post("/workloads/run", response_model=StartRunResponse, status_code=status.HTTP_201_CREATED)
async def start_run(request: StartRunRequest):
    """Launch a new workload run managed by Temporal."""
    spec = request.workload_spec or WorkloadSpec()
    if request.fault_injection:
        fi_type = request.fault_injection.get("type", "").upper()
        if fi_type in ("RETRY", "FIRST_ATTEMPT_FAIL", "FAIL_RETRY"):
            spec.execution_mode = ExecutionMode.FAULT_RETRY
            spec.fault_scenario = FaultScenario.FIRST_ATTEMPT_FAIL
    elif request.fault_scenario:
        try:
            spec.fault_scenario = FaultScenario(request.fault_scenario)
        except Exception:
            pass

    res = await workload_service.create_run(spec)
    res.id = res.run_id
    return res
