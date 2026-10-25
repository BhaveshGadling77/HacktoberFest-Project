from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query
from app.integrations.prometheus_client import PrometheusClient
from app.integrations.kepler_adapter import KeplerAdapter

router = APIRouter(prefix="/metrics", tags=["Metrics"])
prometheus_client = PrometheusClient()
kepler_adapter = KeplerAdapter(prometheus_client)


@router.get("/raw")
async def query_raw_metrics(query: str = Query(..., description="PromQL expression")):
    """Direct PromQL query pass-through."""
    return await prometheus_client.query(query)


@router.get("/available")
async def list_available_metrics():
    """List discovered metrics in Prometheus and Kepler."""
    all_metrics = await prometheus_client.get_available_metrics()
    kepler_metrics = await kepler_adapter.discover_available_metrics()
    return {
        "prometheus_connected": await prometheus_client.check_connection(),
        "total_metrics_found": len(all_metrics),
        "kepler_metrics_found": kepler_metrics,
        "sample_metrics": all_metrics[:50],
    }
