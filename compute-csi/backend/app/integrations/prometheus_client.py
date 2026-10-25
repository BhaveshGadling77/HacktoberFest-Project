from __future__ import annotations

from typing import Optional, List
from datetime import datetime

import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PrometheusClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or settings.PROMETHEUS_URL).rstrip("/")

    async def query(self, promql: str, time: Optional[str] = None) -> dict:
        """Execute instant PromQL query."""
        try:
            params: dict = {"query": promql}
            if time:
                params["time"] = time
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/query", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.warning("Prometheus query timed out", promql=promql)
            return {"status": "error", "error": "timeout"}
        except Exception as e:
            logger.error("Prometheus query failed", promql=promql, error=str(e))
            return {"status": "error", "error": str(e)}

    async def query_range(self, promql: str, start: str, end: str, step: str = "15s") -> dict:
        """Execute range PromQL query."""
        try:
            params = {"query": promql, "start": start, "end": end, "step": step}
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/query_range", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.warning("Prometheus range query timed out", promql=promql)
            return {"status": "error", "error": "timeout"}
        except Exception as e:
            logger.error("Prometheus range query failed", promql=promql, error=str(e))
            return {"status": "error", "error": str(e)}

    async def get_available_metrics(self) -> List[str]:
        """List all available metric names."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/label/__name__/values")
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error("Failed to get Prometheus metrics", error=str(e))
            return []

    async def check_connection(self) -> bool:
        """Check if Prometheus is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/-/healthy")
                return response.status_code == 200
        except Exception:
            try:
                # Fallback: try a simple query
                result = await self.query("up")
                return result.get("status") == "success"
            except Exception:
                return False
