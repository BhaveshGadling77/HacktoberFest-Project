from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class WorkloadType(str, Enum):
    LOCAL_CPU = "LOCAL_CPU"
    REMOTE_GPU = "REMOTE_GPU"


class ExecutionMode(str, Enum):
    NORMAL = "NORMAL"
    FAULT_RETRY = "FAULT_RETRY"
    DELAY = "DELAY"
    REPEATED = "REPEATED"


class FaultScenario(str, Enum):
    NONE = "NONE"
    FIRST_ATTEMPT_FAIL = "FIRST_ATTEMPT_FAIL"
    TIMEOUT_THEN_RETRY = "TIMEOUT_THEN_RETRY"
    REPEATED_PROCESSING = "REPEATED_PROCESSING"


class WorkloadSpec(BaseModel):
    workload_type: WorkloadType = WorkloadType.LOCAL_CPU
    execution_mode: ExecutionMode = ExecutionMode.NORMAL
    fault_scenario: FaultScenario = FaultScenario.NONE
    input_size: int = Field(default=100, ge=1, le=1000)
    delay_seconds: int = Field(default=0, ge=0, le=30)
    max_retries: int = Field(default=3, ge=1, le=5)


class StartRunRequest(BaseModel):
    workload_spec: WorkloadSpec


class StartRunResponse(BaseModel):
    run_id: str
    workflow_id: str
    status: str
    message: str
