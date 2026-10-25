from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.session import init_db


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_workloads_list():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/workloads")
    assert response.status_code == 200
    templates = response.json()
    assert len(templates) >= 1
    assert templates[0]["workload_type"] == "LOCAL_CPU"


@pytest.mark.asyncio
async def test_get_unknown_run_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/runs/non-existent-uuid")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_workload_spec_422():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Invalid input_size > 1000
        response = await ac.post("/api/v1/runs", json={
            "workload_spec": {
                "workload_type": "LOCAL_CPU",
                "execution_mode": "NORMAL",
                "fault_scenario": "NONE",
                "input_size": 99999,
                "delay_seconds": 0,
                "max_retries": 3,
            }
        })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_integrations_status():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/integrations/status")
    assert response.status_code == 200
    data = response.json()
    assert "temporal" in data
    assert "prometheus" in data
    assert "kepler" in data
    assert "gemma" in data
    assert "jarvislabs" in data
