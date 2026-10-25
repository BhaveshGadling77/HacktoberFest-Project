from __future__ import annotations

import asyncio
import math
import time
from temporalio import activity
from activities.fault_injection import FaultInjectionConfig


def _simulate_inference(size: int) -> dict:
    """CPU-compatible mathematical benchmark simulating model inference without requiring GPU."""
    n = max(10, min(size, 400))
    # Matrix simulation
    a = [[math.sin(i * 0.05 + j * 0.02) for j in range(n)] for i in range(min(n, 50))]
    b = [[math.cos(j * 0.05 + k * 0.02) for k in range(min(n, 50))] for j in range(n)]
    
    total = 0.0
    for r in range(len(a)):
        for c in range(len(b[0])):
            total += sum(a[r][k] * b[k][c] for k in range(min(len(a[0]), len(b))))

    return {
        "output_checksum": round(total, 4),
        "dimensions": f"{len(a)}x{len(b[0])}",
        "processed_tokens": size * 4,
    }


@activity.defn(name="run_inference_activity")
async def run_inference_activity(params: dict) -> dict:
    info = activity.info()
    attempt = info.attempt

    fault_scenario = params.get("fault_scenario", "NONE")
    execution_mode = params.get("execution_mode", "NORMAL")
    input_size = int(params.get("input_size", 100))
    delay_seconds = int(params.get("delay_seconds", 0))

    # Controlled fault injection checkpoint
    FaultInjectionConfig.evaluate(fault_scenario=fault_scenario, attempt=attempt, delay_seconds=delay_seconds)

    # Artificial delay scenario
    if execution_mode == "DELAY" or delay_seconds > 0:
        sleep_time = delay_seconds if delay_seconds > 0 else 2
        await asyncio.sleep(sleep_time)

    # Inference computation
    start_time = time.monotonic()
    result = _simulate_inference(input_size)

    # Repeated processing mode (simulates loops or runaway activity internal cycles)
    if execution_mode == "REPEATED":
        for _ in range(2):
            result = _simulate_inference(input_size)

    compute_duration = time.monotonic() - start_time

    return {
        "status": "SUCCESS",
        "attempt": attempt,
        "execution_mode": execution_mode,
        "fault_scenario": fault_scenario,
        "input_size": input_size,
        "inference_output": result,
        "compute_duration_seconds": round(compute_duration, 4),
        "timestamp": time.time(),
    }
