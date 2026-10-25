from __future__ import annotations

from typing import Optional, List
from datetime import datetime, timezone

from app.integrations.prometheus_client import PrometheusClient
from app.schemas.metrics import MetricSeries, MetricPoint
from app.core.logging import get_logger

logger = get_logger(__name__)

KEPLER_METRIC_CANDIDATES = [
    "kepler_container_joules_total",
    "kepler_process_package_joules_total",
    "kepler_node_package_joules_total",
    "kepler_container_package_joules_total",
]


class KeplerAdapter:
    def __init__(self, prometheus_client: Optional[PrometheusClient] = None) -> None:
        self.prometheus = prometheus_client or PrometheusClient()

    async def discover_available_metrics(self) -> List[str]:
        """Query Prometheus to find which Kepler metrics exist."""
        all_metrics = await self.prometheus.get_available_metrics()
        available = [m for m in KEPLER_METRIC_CANDIDATES if m in all_metrics]
        logger.info("Kepler metrics discovered", available=available)
        return available

    async def get_energy_for_window(
        self,
        start: str,
        end: str,
        container_filter: Optional[str] = None,
    ) -> MetricSeries:
        """Get energy consumption for a time window. Returns MetricSeries."""
        available_metrics = await self.discover_available_metrics()
        if not available_metrics:
            return MetricSeries(
                name="energy_joules",
                unit="joules",
                available=False,
                unavailability_reason="No Kepler energy metrics found in Prometheus",
            )

        metric = available_metrics[0]
        # For cumulative counters, use increase() to get delta
        if container_filter:
            promql = f'increase({metric}{{container_name=~"{container_filter}"}}[5m])'
        else:
            promql = f"increase({metric}[5m])"

        try:
            result = await self.prometheus.query_range(promql, start=start, end=end, step="15s")
            if result.get("status") != "success":
                return MetricSeries(
                    name="energy_joules",
                    unit="joules",
                    available=False,
                    unavailability_reason=f"Prometheus query failed: {result.get('error', 'unknown')}",
                )

            data = result.get("data", {})
            results = data.get("result", [])
            if not results:
                return MetricSeries(
                    name="energy_joules",
                    unit="joules",
                    available=False,
                    unavailability_reason="No energy data found for the time window",
                )

            # Aggregate all series
            points: List[MetricPoint] = []
            seen_timestamps: dict = {}
            for series in results:
                for ts, val in series.get("values", []):
                    try:
                        float_val = float(val)
                        ts_key = str(ts)
                        if ts_key not in seen_timestamps:
                            seen_timestamps[ts_key] = 0.0
                        seen_timestamps[ts_key] += float_val
                    except (ValueError, TypeError):
                        continue

            for ts_str, val in sorted(seen_timestamps.items()):
                try:
                    dt = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                    points.append(MetricPoint(timestamp=dt.isoformat(), value=val))
                except Exception:
                    continue

            return MetricSeries(
                name="energy_joules",
                unit="joules",
                points=points,
                available=True,
            )
        except Exception as e:
            logger.error("Kepler energy query failed", error=str(e))
            return MetricSeries(
                name="energy_joules",
                unit="joules",
                available=False,
                unavailability_reason=str(e),
            )
