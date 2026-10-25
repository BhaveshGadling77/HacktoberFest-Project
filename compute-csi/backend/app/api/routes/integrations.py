from __future__ import annotations

from fastapi import APIRouter
from app.integrations.temporal_client import get_temporal_client
from app.integrations.prometheus_client import PrometheusClient
from app.integrations.kepler_adapter import KeplerAdapter
from app.integrations.gemma_adapter import GemmaAdapter
from app.integrations.jarvislabs_adapter import JarvisLabsAdapter
from app.core.config import settings

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("/status")
async def get_integrations_status():
    """Verify live connectivity and capabilities of all integrated subsystems."""
    # 1. Temporal
    temporal_client = await get_temporal_client()
    temporal_status = {
        "connected": temporal_client is not None,
        "address": settings.TEMPORAL_ADDRESS,
        "namespace": settings.TEMPORAL_NAMESPACE,
        "task_queue": settings.TEMPORAL_TASK_QUEUE,
        "error": None if temporal_client else "Cannot establish gRPC connection to Temporal server",
    }

    # 2. Prometheus
    prom_client = PrometheusClient()
    prom_connected = await prom_client.check_connection()
    prom_status = {
        "connected": prom_connected,
        "url": settings.PROMETHEUS_URL,
        "error": None if prom_connected else "Prometheus HTTP endpoint unreachable",
    }

    # 3. Kepler
    kepler_adapter = KeplerAdapter(prom_client)
    kepler_metrics = await kepler_adapter.discover_available_metrics() if prom_connected else []
    kepler_targets = []
    if prom_connected:
        scrape_status = await prom_client.query('up{job="kepler"}')
        for series in scrape_status.get("data", {}).get("result", []):
            values = series.get("value", [])
            kepler_targets.append({
                "instance": series.get("metric", {}).get("instance", "unknown"),
                "up": len(values) > 1 and values[1] == "1",
            })
    kepler_connected = len(kepler_metrics) > 0
    kepler_status = {
        "connected": kepler_connected,
        "available_metrics": kepler_metrics,
        "scrape_targets": kepler_targets,
        "error": None if kepler_connected else (
            "Kepler scrape target is DOWN in Prometheus. Check the kepler container and target address."
            if kepler_targets and not any(target["up"] for target in kepler_targets)
            else "Kepler is scraped, but no supported energy metrics are present; check host sensors."
            if kepler_targets and any(target["up"] for target in kepler_targets)
            else "No Kepler scrape target found. Start with `docker compose --profile kepler up -d` or configure a Kubernetes exporter."
            if prom_connected else "Prometheus unavailable, cannot probe Kepler"
        ),
    }

    # 4. Gemma
    gemma_adapter = GemmaAdapter()
    gemma_connected = await gemma_adapter.check_connection()
    gemma_status = {
        "connected": gemma_connected,
        "endpoint": settings.GEMMA_ENDPOINT or None,
        "model": settings.GEMMA_MODEL,
        "error": None if gemma_connected else (
            "Gemma endpoint not configured" if not settings.GEMMA_ENDPOINT else "Endpoint unreachable"
        ),
    }

    # 5. JarvisLabs
    jarvis_adapter = JarvisLabsAdapter()
    jl_check = await jarvis_adapter.check_status()
    jarvis_status = {
        "connected": jl_check.get("available", False),
        "instance_url": settings.JARVISLABS_INSTANCE_URL or None,
        "error": jl_check.get("reason"),
    }

    return {
        "temporal": temporal_status,
        "prometheus": prom_status,
        "kepler": kepler_status,
        "gemma": gemma_status,
        "jarvislabs": jarvis_status,
    }
