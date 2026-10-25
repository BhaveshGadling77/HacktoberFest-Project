from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone

from app.integrations.prometheus_client import PrometheusClient
from app.integrations.kepler_adapter import KeplerAdapter
from app.schemas.metrics import RunMetrics, MetricSeries, MetricPoint
from app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsService:
    def __init__(self) -> None:
        self.prometheus = PrometheusClient()
        self.kepler = KeplerAdapter(self.prometheus)

    async def get_run_metrics(
        self,
        run_id: str,
        window_start: Optional[str] = None,
        window_end: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> RunMetrics:
        """Collect CPU, memory, and energy metrics for a run window."""
        now = datetime.now(timezone.utc)
        start = start_time or window_start or now.isoformat()
        end = end_time or window_end or now.isoformat()

        # Get available Prometheus metrics
        raw_available = await self.prometheus.get_available_metrics()

        # Energy via Kepler
        energy_series = await self.kepler.get_energy_for_window(start=start, end=end)

        # CPU percent
        cpu_series = await self._get_cpu_series(start, end)

        # Memory MB
        memory_series = await self._get_memory_series(start, end)

        return RunMetrics(
            run_id=run_id,
            window_start=start,
            window_end=end,
            energy_joules=energy_series,
            cpu_percent=cpu_series,
            memory_mb=memory_series,
            raw_available_metrics=raw_available[:50],  # Cap for response size
        )

    async def _get_cpu_series(self, start: str, end: str) -> MetricSeries:
        try:
            promql = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
            result = await self.prometheus.query_range(promql, start=start, end=end, step="15s")
            if result.get("status") != "success":
                return MetricSeries(
                    name="cpu_percent",
                    unit="percent",
                    available=False,
                    unavailability_reason="Prometheus query failed",
                )
            points = self._extract_points(result)
            if not points:
                return MetricSeries(
                    name="cpu_percent",
                    unit="percent",
                    available=False,
                    unavailability_reason="No CPU data found for window",
                )
            return MetricSeries(name="cpu_percent", unit="percent", points=points, available=True)
        except Exception as e:
            return MetricSeries(
                name="cpu_percent",
                unit="percent",
                available=False,
                unavailability_reason=str(e),
            )

    async def _get_memory_series(self, start: str, end: str) -> MetricSeries:
        try:
            promql = "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024"
            result = await self.prometheus.query_range(promql, start=start, end=end, step="15s")
            if result.get("status") != "success":
                return MetricSeries(
                    name="memory_mb",
                    unit="megabytes",
                    available=False,
                    unavailability_reason="Prometheus query failed",
                )
            points = self._extract_points(result)
            if not points:
                return MetricSeries(
                    name="memory_mb",
                    unit="megabytes",
                    available=False,
                    unavailability_reason="No memory data found for window",
                )
            return MetricSeries(name="memory_mb", unit="megabytes", points=points, available=True)
        except Exception as e:
            return MetricSeries(
                name="memory_mb",
                unit="megabytes",
                available=False,
                unavailability_reason=str(e),
            )

    def _extract_points(self, query_result: dict) -> list[MetricPoint]:
        """Extract MetricPoint list from Prometheus range query result."""
        points: list[MetricPoint] = []
        results = query_result.get("data", {}).get("result", [])
        # Aggregate all series
        ts_map: dict[str, float] = {}
        for series in results:
            for ts, val in series.get("values", []):
                try:
                    fval = float(val)
                    ts_key = str(ts)
                    ts_map[ts_key] = ts_map.get(ts_key, 0.0) + fval
                except (ValueError, TypeError):
                    continue
        for ts_str, val in sorted(ts_map.items()):
            try:
                dt = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                points.append(MetricPoint(timestamp=dt.isoformat(), value=val))
            except Exception:
                continue
        return points
