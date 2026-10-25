from __future__ import annotations

import pytest
from app.services.metrics_service import MetricsService
from app.schemas.metrics import RunMetrics


@pytest.mark.asyncio
async def test_metrics_service_unavailable_fallback():
    # In local testing without Prometheus/Kepler running, metrics return structured unavailable
    service = MetricsService()
    metrics = await service.get_run_metrics(
        run_id="test-run-123",
        start_time="2026-10-25T10:00:00Z",
        end_time="2026-10-25T10:05:00Z",
    )
    assert isinstance(metrics, RunMetrics)
    assert metrics.run_id == "test-run-123"
    # Energy series should honestly report unavailable
    assert not metrics.energy_joules.available
    assert metrics.energy_joules.unavailability_reason is not None
