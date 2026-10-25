from __future__ import annotations

import pytest
import uuid
from app.services.baseline_service import BaselineService
from app.database.session import init_db


@pytest.mark.asyncio
async def test_baseline_reliability_threshold():
    await init_db()
    service = BaselineService()
    workload = f"TEST_WL_{uuid.uuid4().hex[:6]}"
    mode = "NORMAL"

    # Initially 0 samples -> not reliable
    b0 = await service.get_baseline(workload, mode)
    assert b0["sample_count"] == 0
    assert not b0["is_reliable"]

    # Add 1 sample -> still not reliable (< 3)
    await service.add_sample(str(uuid.uuid4()), workload, mode, duration=2.0)
    b1 = await service.get_baseline(workload, mode)
    assert b1["sample_count"] == 1
    assert not b1["is_reliable"]

    # Add 2 more samples (total 3) -> should now be reliable
    await service.add_sample(str(uuid.uuid4()), workload, mode, duration=2.2)
    await service.add_sample(str(uuid.uuid4()), workload, mode, duration=2.1)
    b3 = await service.get_baseline(workload, mode)
    assert b3["sample_count"] == 3
    assert b3["is_reliable"]
    assert b3["median_duration"] == pytest.approx(2.1, rel=1e-2)
