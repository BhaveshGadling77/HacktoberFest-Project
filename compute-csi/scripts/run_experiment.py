#!/usr/bin/env python3
"""
run_experiment.py — Run Compute CSI experiments A, B, C, D.

Experiments:
  a  Normal execution — record duration baseline
  b  Fault injection (FIRST_ATTEMPT_FAIL) — verify Temporal retries
  c  Delay injection — compare duration to baseline
  d  Metrics collection — compare energy/resource metrics to baseline

Output: JSON file with experiment results + console summary.
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", "./experiment_results"))

EXPERIMENTS = {
    "a": "Normal execution — baseline duration",
    "b": "Fault injection (FIRST_ATTEMPT_FAIL) — retry verification",
    "c": "Delay injection — latency impact",
    "d": "Metrics collection — resource/energy comparison",
}

# ── HTTP helpers ───────────────────────────────────────────────────────────────

def api(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def prom_query(query: str) -> list[dict]:
    """Execute an instant PromQL query."""
    url = f"{PROMETHEUS_URL}/api/v1/query"
    encoded_query = urllib.parse.quote(query)
    try:
        import urllib.parse
        with urllib.request.urlopen(
            f"{url}?query={encoded_query}", timeout=10
        ) as resp:
            data = json.loads(resp.read())
            return data.get("data", {}).get("result", [])
    except Exception:
        return []


def wait_for_run(run_id: str, timeout: int = 180) -> dict | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            run = api("GET", f"/api/runs/{run_id}")
            if run.get("status") in ("completed", "failed", "cancelled"):
                return run
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(3)
    print()
    return None


# ── Experiment runners ─────────────────────────────────────────────────────────

def run_experiment_a(repeat: int) -> dict:
    """Normal execution — measure duration."""
    print(f"\n  [Experiment A] Normal execution × {repeat}")
    results = []
    for i in range(repeat):
        start = time.monotonic()
        run = api("POST", "/api/runs", {})
        run_id = run["id"]
        completed = wait_for_run(run_id, timeout=120)
        elapsed = time.monotonic() - start
        status = completed.get("status") if completed else "timeout"
        results.append(
            {
                "run_id": run_id,
                "iteration": i + 1,
                "duration_s": round(elapsed, 3),
                "status": status,
                "data_source": "real" if status == "completed" else "simulated",
            }
        )
        print(f"  Run {i+1}: {status} in {elapsed:.2f}s")

    durations = [r["duration_s"] for r in results if r["status"] == "completed"]
    return {
        "experiment": "a",
        "description": EXPERIMENTS["a"],
        "repeat": repeat,
        "runs": results,
        "summary": {
            "completed": len(durations),
            "avg_duration_s": round(sum(durations) / len(durations), 3) if durations else None,
            "min_duration_s": round(min(durations), 3) if durations else None,
            "max_duration_s": round(max(durations), 3) if durations else None,
        },
    }


def run_experiment_b(repeat: int) -> dict:
    """Fault injection — verify Temporal retries."""
    print(f"\n  [Experiment B] Fault injection (FIRST_ATTEMPT_FAIL) × {repeat}")
    results = []
    for i in range(repeat):
        start = time.monotonic()
        run = api("POST", "/api/runs", {"fault_injection": {"type": "FIRST_ATTEMPT_FAIL"}})
        run_id = run["id"]
        completed = wait_for_run(run_id, timeout=240)
        elapsed = time.monotonic() - start
        status = completed.get("status") if completed else "timeout"
        retry_count = completed.get("retry_count", 0) if completed else 0
        temporal_verified = retry_count > 0
        results.append(
            {
                "run_id": run_id,
                "iteration": i + 1,
                "duration_s": round(elapsed, 3),
                "status": status,
                "retry_count": retry_count,
                "temporal_retries_verified": temporal_verified,
                "data_source": "real",
            }
        )
        print(
            f"  Run {i+1}: {status} in {elapsed:.2f}s  "
            f"retries={retry_count} ({'✓ verified' if temporal_verified else '✗ no retries observed'})"
        )

    retried = [r for r in results if r["temporal_retries_verified"]]
    return {
        "experiment": "b",
        "description": EXPERIMENTS["b"],
        "repeat": repeat,
        "runs": results,
        "summary": {
            "completed": len([r for r in results if r["status"] == "completed"]),
            "temporal_retries_verified": len(retried),
            "avg_retry_count": (
                round(sum(r["retry_count"] for r in results) / len(results), 2)
                if results
                else 0
            ),
        },
    }


def run_experiment_c(repeat: int) -> dict:
    """Delay injection — measure latency impact."""
    print(f"\n  [Experiment C] Delay injection × {repeat}")
    results = []
    for i in range(repeat):
        start = time.monotonic()
        run = api("POST", "/api/runs", {"fault_injection": {"type": "DELAY", "delay_ms": 5000}})
        run_id = run["id"]
        completed = wait_for_run(run_id, timeout=180)
        elapsed = time.monotonic() - start
        status = completed.get("status") if completed else "timeout"
        results.append(
            {
                "run_id": run_id,
                "iteration": i + 1,
                "duration_s": round(elapsed, 3),
                "injected_delay_ms": 5000,
                "status": status,
                "data_source": "real" if status == "completed" else "simulated",
            }
        )
        print(f"  Run {i+1}: {status} in {elapsed:.2f}s (5s delay injected)")

    durations = [r["duration_s"] for r in results if r["status"] == "completed"]
    return {
        "experiment": "c",
        "description": EXPERIMENTS["c"],
        "repeat": repeat,
        "runs": results,
        "summary": {
            "completed": len(durations),
            "avg_duration_s": round(sum(durations) / len(durations), 3) if durations else None,
            "injected_delay_ms": 5000,
            "note": "Compare avg_duration_s against Experiment A baseline to measure overhead.",
        },
    }


def run_experiment_d(repeat: int) -> dict:
    """Collect available metrics — compare to baseline."""
    print(f"\n  [Experiment D] Metrics collection × {repeat}")

    # Determine what metrics are available
    import urllib.parse

    available: dict[str, bool] = {}

    def probe_metric(metric: str) -> bool:
        url = f"{PROMETHEUS_URL}/api/v1/query?query={urllib.parse.quote(metric)}"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read())
                return bool(data.get("data", {}).get("result"))
        except Exception:
            return False

    available["prometheus_scraping"] = probe_metric("up")
    available["backend_metrics"] = probe_metric("http_request_duration_seconds_count")
    available["kepler_energy"] = probe_metric("kepler_container_joules_total")
    available["kepler_gpu"] = probe_metric("kepler_container_gpu_joules_total")

    print("\n  Available data sources:")
    for name, is_real in available.items():
        tag = "real" if is_real else "simulated/unavailable"
        icon = "✓" if is_real else "~"
        print(f"    {icon} {name}: {tag}")

    results = []
    for i in range(repeat):
        start = time.monotonic()
        run = api("POST", "/api/runs", {})
        run_id = run["id"]

        # Snapshot pre-run metrics
        metrics_before: dict = {}
        if available["backend_metrics"]:
            metrics_before["http_requests"] = probe_metric(
                "sum(http_request_duration_seconds_count)"
            )

        completed = wait_for_run(run_id, timeout=120)
        elapsed = time.monotonic() - start
        status = completed.get("status") if completed else "timeout"

        # Snapshot post-run metrics
        metrics_after: dict = {}
        energy_joules: float | None = None
        if available["kepler_energy"]:
            url = (
                f"{PROMETHEUS_URL}/api/v1/query?"
                "query="
                + urllib.parse.quote(
                    f'increase(kepler_container_joules_total[{int(elapsed)+5}s])'
                )
            )
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    data = json.loads(resp.read())
                    results_raw = data.get("data", {}).get("result", [])
                    if results_raw:
                        energy_joules = round(
                            sum(float(r["value"][1]) for r in results_raw), 4
                        )
            except Exception:
                energy_joules = None

        results.append(
            {
                "run_id": run_id,
                "iteration": i + 1,
                "duration_s": round(elapsed, 3),
                "status": status,
                "energy_joules": energy_joules,
                "energy_source": "kepler (real)" if energy_joules is not None else "unavailable",
                "metrics_available": available,
            }
        )
        energy_str = f"{energy_joules}J" if energy_joules is not None else "N/A (Kepler not active)"
        print(f"  Run {i+1}: {status} in {elapsed:.2f}s | energy: {energy_str}")

    return {
        "experiment": "d",
        "description": EXPERIMENTS["d"],
        "repeat": repeat,
        "runs": results,
        "data_sources": {
            k: ("real" if v else "simulated") for k, v in available.items()
        },
        "summary": {
            "completed": len([r for r in results if r["status"] == "completed"]),
            "kepler_available": available["kepler_energy"],
            "note": (
                "Kepler energy metrics are real Kubernetes eBPF data when available. "
                "Without Kepler, energy figures are unavailable — "
                "see monitoring/README.md for Kepler setup."
            ),
        },
    }


# ── Main ───────────────────────────────────────────────────────────────────────

RUNNERS = {
    "a": run_experiment_a,
    "b": run_experiment_b,
    "c": run_experiment_c,
    "d": run_experiment_d,
}


def main():
    parser = argparse.ArgumentParser(
        description="Run Compute CSI experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(f"  {k}: {v}" for k, v in EXPERIMENTS.items()),
    )
    parser.add_argument(
        "--experiment",
        choices=list(EXPERIMENTS.keys()),
        required=True,
        help="Which experiment to run (a/b/c/d)",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
        help="Number of times to repeat the experiment (default: 3)",
    )
    parser.add_argument(
        "--api-url",
        default=API_BASE,
        help=f"Backend API URL (default: {API_BASE})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(RESULTS_DIR),
        help="Directory to write result JSON files",
    )
    args = parser.parse_args()

    global API_BASE
    API_BASE = args.api_url.rstrip("/")

    print("=" * 60)
    print(f"  Compute CSI — Experiment Runner")
    print(f"  Experiment : {args.experiment.upper()} — {EXPERIMENTS[args.experiment]}")
    print(f"  Repeat     : {args.repeat}")
    print(f"  API        : {API_BASE}")
    print(f"  Started    : {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Verify backend reachable
    try:
        api("GET", "/health")
    except Exception as exc:
        print(f"\nERROR: Cannot reach backend at {API_BASE}: {exc}")
        print("Run `make dev-start` first.")
        sys.exit(1)

    # Run experiment
    runner = RUNNERS[args.experiment]
    result = runner(args.repeat)
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    result["api_url"] = API_BASE

    # Save results
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"experiment_{args.experiment}_{ts}.json"
    out_file.write_text(json.dumps(result, indent=2))

    # Print summary
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    summary = result.get("summary", {})
    for k, v in summary.items():
        print(f"  {k:<30}: {v}")

    if "data_sources" in result:
        print("\n  Data source provenance:")
        for src, kind in result["data_sources"].items():
            icon = "✓" if kind == "real" else "~"
            print(f"    {icon} {src}: {kind}")

    print(f"\n  Results written to: {out_file}")
    print("=" * 60)


if __name__ == "__main__":
    import urllib.parse  # ensure available in module scope for experiment d
    main()
