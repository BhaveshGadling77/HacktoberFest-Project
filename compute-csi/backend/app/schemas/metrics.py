from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class MetricPoint(BaseModel):
    timestamp: str
    value: float


class MetricSeries(BaseModel):
    name: str
    unit: str
    points: List[MetricPoint] = []
    available: bool = False
    unavailability_reason: Optional[str] = None


class RunMetrics(BaseModel):
    run_id: str
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    energy_joules: MetricSeries
    cpu_percent: MetricSeries
    memory_mb: MetricSeries
    raw_available_metrics: List[str] = []
