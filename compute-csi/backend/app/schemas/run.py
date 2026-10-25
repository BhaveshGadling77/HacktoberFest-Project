from __future__ import annotations

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class ActivityEvent(BaseModel):
    event_id: str
    event_type: str
    activity_name: Optional[str] = None
    attempt: int = 1
    timestamp: str
    duration_ms: Optional[float] = None
    failure_reason: Optional[str] = None


class RunDetail(BaseModel):
    run_id: str
    workflow_id: Optional[str] = None
    workload_type: str
    execution_mode: str
    fault_scenario: str
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    attempt_count: int = 0
    failure_count: int = 0
    outcome: Optional[str] = None
    timeline: List[ActivityEvent] = []


class RunSummary(BaseModel):
    run_id: str
    workflow_id: Optional[str] = None
    status: str
    start_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    attempt_count: int = 0
    failure_count: int = 0
