from __future__ import annotations

from typing import Optional
import httpx
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.workload import WorkloadSpec

logger = get_logger(__name__)


class JarvisLabsAdapter:
    def __init__(
        self,
        api_key: Optional[str] = None,
        instance_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or settings.JARVISLABS_API_KEY
        self.instance_url = instance_url or settings.JARVISLABS_INSTANCE_URL

    def _is_configured(self) -> bool:
        return bool(self.api_key and self.instance_url)

    async def run_inference(self, spec: WorkloadSpec) -> dict:
        """Run remote GPU inference on JarvisLabs instance."""
        if not self._is_configured():
            return {
                "available": False,
                "reason": "JarvisLabs credentials not configured",
                "result": None,
                "duration_seconds": 0.0,
            }
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "workload_type": spec.workload_type.value,
                "input_size": spec.input_size,
                "execution_mode": spec.execution_mode.value,
                "fault_scenario": spec.fault_scenario.value,
            }
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.instance_url}/inference",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "available": True,
                    "result": data.get("result"),
                    "duration_seconds": float(data.get("duration_seconds", 0.0)),
                }
        except Exception as e:
            logger.error("JarvisLabs inference failed", error=str(e))
            return {
                "available": False,
                "reason": str(e),
                "result": None,
                "duration_seconds": 0.0,
            }

    async def check_status(self) -> dict:
        """Check if JarvisLabs instance is available."""
        if not self._is_configured():
            return {"available": False, "reason": "JarvisLabs credentials not configured"}
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.instance_url}/health",
                    headers=headers,
                )
                if response.status_code == 200:
                    return {"available": True, "reason": None}
                return {"available": False, "reason": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"available": False, "reason": str(e)}
