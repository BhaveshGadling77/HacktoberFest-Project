from __future__ import annotations

import statistics
import uuid
from typing import Optional, List

from app.database.repositories import BaselineSampleRepository
from app.database.session import AsyncSessionLocal
from app.schemas.run import RunDetail
from app.schemas.metrics import RunMetrics
from app.core.logging import get_logger

logger = get_logger(__name__)

MIN_RELIABLE_SAMPLES = 3
ANOMALY_THRESHOLD = 0.50  # 50% deviation


class BaselineService:
    async def add_sample(
        self,
        run_id: str,
        workload_type: str,
        execution_mode: str,
        duration: float,
        energy: Optional[float] = None,
        cpu: Optional[float] = None,
        memory: Optional[float] = None,
    ) -> None:
        """Add a baseline sample for a workload type/mode combination."""
        async with AsyncSessionLocal() as session:
            repo = BaselineSampleRepository(session)
            await repo.create({
                "id": str(uuid.uuid4()),
                "workload_type": workload_type,
                "execution_mode": execution_mode,
                "duration_seconds": duration,
                "energy_joules": energy,
                "cpu_percent": cpu,
                "memory_mb": memory,
                "run_id": run_id,
            })
        logger.debug("Added baseline sample", workload_type=workload_type, execution_mode=execution_mode)

    async def get_baseline(self, workload_type: str, execution_mode: str) -> dict:
        """Get baseline stats. is_reliable=True only if >= MIN_RELIABLE_SAMPLES exist."""
        async with AsyncSessionLocal() as session:
            repo = BaselineSampleRepository(session)
            samples = await repo.get_by_workload(workload_type, execution_mode)

        if not samples:
            return {
                "workload_type": workload_type,
                "execution_mode": execution_mode,
                "sample_count": 0,
                "is_reliable": False,
                "median_duration": None,
                "median_energy": None,
                "median_cpu": None,
                "median_memory": None,
            }

        durations = [s.duration_seconds for s in samples if s.duration_seconds is not None]
        energies = [s.energy_joules for s in samples if s.energy_joules is not None]
        cpus = [s.cpu_percent for s in samples if s.cpu_percent is not None]
        memories = [s.memory_mb for s in samples if s.memory_mb is not None]

        return {
            "workload_type": workload_type,
            "execution_mode": execution_mode,
            "sample_count": len(samples),
            "is_reliable": len(samples) >= MIN_RELIABLE_SAMPLES,
            "median_duration": statistics.median(durations) if durations else None,
            "median_energy": statistics.median(energies) if energies else None,
            "median_cpu": statistics.median(cpus) if cpus else None,
            "median_memory": statistics.median(memories) if memories else None,
        }

    async def compare_to_baseline(self, run: RunDetail, metrics: RunMetrics) -> dict:
        """Compare a run to its baseline. Only flag anomaly if baseline is reliable and deviation > 50%."""
        baseline = await self.get_baseline(run.workload_type, run.execution_mode)

        duration_deviation: Optional[float] = None
        energy_deviation: Optional[float] = None
        is_anomalous = False
        anomaly_reasons: List[str] = []

        # Duration comparison
        if baseline["is_reliable"] and baseline["median_duration"] and run.duration_seconds:
            median_dur = baseline["median_duration"]
            actual_dur = run.duration_seconds
            if median_dur > 0:
                duration_deviation = (actual_dur - median_dur) / median_dur
                if abs(duration_deviation) > ANOMALY_THRESHOLD:
                    is_anomalous = True
                    anomaly_reasons.append(
                        f"Duration deviation {duration_deviation:.1%} exceeds threshold {ANOMALY_THRESHOLD:.0%}"
                    )

        # Energy comparison (only if energy available)
        if (
            baseline["is_reliable"]
            and baseline["median_energy"]
            and metrics.energy_joules.available
            and metrics.energy_joules.points
        ):
            actual_energy = sum(p.value for p in metrics.energy_joules.points)
            median_energy = baseline["median_energy"]
            if median_energy > 0:
                energy_deviation = (actual_energy - median_energy) / median_energy
                if abs(energy_deviation) > ANOMALY_THRESHOLD:
                    is_anomalous = True
                    anomaly_reasons.append(
                        f"Energy deviation {energy_deviation:.1%} exceeds threshold {ANOMALY_THRESHOLD:.0%}"
                    )

        return {
            "baseline": baseline,
            "duration_deviation": duration_deviation,
            "energy_deviation": energy_deviation,
            "is_anomalous": is_anomalous,
            "anomaly_reasons": anomaly_reasons,
            "baseline_reliable": baseline["is_reliable"],
        }
