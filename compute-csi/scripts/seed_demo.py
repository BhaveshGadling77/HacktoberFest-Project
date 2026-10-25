#!/usr/bin/env python3
"""
seed_demo.py — Seed demo data for Compute CSI.

Connects to the backend API, creates baseline and fault-injection runs,
waits for completion, then triggers an investigation and prints a summary.
"""

import os
import sys
import time
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")
TIMEOUT = int(os.environ.get("SEED_TIMEOUT", "120"))


def api(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        print(f"  [HTTP {e.code}] {method} {path}: {body_text[:200]}", file=sys.stderr)
        raise
    except urllib.error.URLError as e:
        print(f"  [URLError] {method} {path}: {e.reason}", file=sys.stderr)
        raise


def wait_for_run(run_id: str, label: str, timeout: int = TIMEOUT) -> dict | None:
    """Poll until run reaches a terminal state or timeout."""
    deadline = time.time() + timeout
    dot_count = 0
    while time.time() < deadline:
        try:
            run = api("GET", f"/api/runs/{run_id}")
        except Exception:
            time.sleep(3)
            continue
        status = str(run.get("status", "unknown")).lower()
        if status in ("completed", "failed", "cancelled", "timed_out"):
            print(f"\n  [{label}] run {run_id} → {status.upper()}")
            return run
        print(".", end="", flush=True)
        dot_count += 1
        if dot_count % 20 == 0:
            print(f" ({int(deadline - time.time())}s left)", flush=True)
        time.sleep(3)
    print(f"\n  [TIMEOUT] {label} run {run_id} did not complete within {timeout}s")
    return None


def check_health():
    try:
        result = api("GET", "/health")
        print(f"  Backend health: {result}")
    except Exception as exc:
        print(f"\n  ERROR: Cannot reach backend at {API_BASE}")
        print(f"  → {exc}")
        print("  Ensure services are running: make dev-start")
        sys.exit(1)


def create_run(fault_type: str | None = None, label: str = "") -> str:
    payload: dict = {}
    if fault_type:
        payload["fault_injection"] = {"type": fault_type}
    run = api("POST", "/api/runs", payload)
    run_id = run["id"]
    print(f"  Created {label or 'run'}: {run_id}")
    return run_id


def trigger_investigation(run_id: str) -> dict:
    result = api("POST", f"/api/runs/{run_id}/investigate", {})
    print(f"  Investigation triggered for {run_id}: {result.get('status', 'unknown')}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Seed Compute CSI with demo data")
    parser.add_argument(
        "--api-url", default=API_BASE, help="Backend API base URL"
    )
    parser.add_argument(
        "--baseline-count", type=int, default=3, help="Number of baseline runs to create"
    )
    parser.add_argument(
        "--skip-wait", action="store_true", help="Don't wait for runs to complete"
    )
    args = parser.parse_args()

    global API_BASE
    API_BASE = args.api_url.rstrip("/")

    print("=" * 60)
    print("  Compute CSI — Demo Data Seeder")
    print(f"  API: {API_BASE}")
    print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # 1. Health check
    print("\n[1/4] Checking backend health...")
    check_health()

    # 2. Baseline runs
    print(f"\n[2/4] Creating {args.baseline_count} baseline runs...")
    baseline_ids = []
    for i in range(args.baseline_count):
        run_id = create_run(label=f"baseline-{i+1}")
        baseline_ids.append(run_id)

    if not args.skip_wait:
        print("  Waiting for baseline runs to complete...")
        baseline_results = []
        for run_id in baseline_ids:
            result = wait_for_run(run_id, label="baseline")
            baseline_results.append(result)

        completed = [r for r in baseline_results if r and r.get("status") == "completed"]
        print(f"  Baseline: {len(completed)}/{args.baseline_count} completed successfully")

    # 3. Fault injection run
    print("\n[3/4] Creating fault injection run (FIRST_ATTEMPT_FAIL)...")
    fault_id = create_run(fault_type="FIRST_ATTEMPT_FAIL", label="fault-injection")

    if not args.skip_wait:
        print("  Waiting for fault run to complete (may take longer due to retry)...")
        fault_result = wait_for_run(fault_id, label="fault", timeout=TIMEOUT * 2)
        if fault_result:
            retries = fault_result.get("retry_count", 0)
            status = fault_result.get("status", "unknown")
            print(f"  Fault run status: {status}, retries: {retries}")

    # 4. Trigger investigation
    print(f"\n[4/4] Triggering AI investigation for fault run ({fault_id})...")
    try:
        investigation = trigger_investigation(fault_id)
    except Exception as exc:
        print(f"  Investigation failed (may require Gemma endpoint): {exc}")
        investigation = {"status": "skipped"}

    # Summary
    print("\n" + "=" * 60)
    print("  SEED SUMMARY")
    print("=" * 60)
    print(f"  Baseline runs created : {args.baseline_count}")
    print(f"  Fault run ID          : {fault_id}")
    print(f"  Investigation status  : {investigation.get('status', 'unknown')}")
    print(f"\n  View runs    : {API_BASE}/api/runs")
    print(f"  Temporal UI  : http://localhost:8233")
    print(f"  Prometheus   : http://localhost:9090")
    print("=" * 60)


if __name__ == "__main__":
    main()
