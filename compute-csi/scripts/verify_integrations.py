#!/usr/bin/env python3
"""
verify_integrations.py — Verify all Compute CSI integrations.

Checks reachability of Temporal, Prometheus, Kepler, and Gemma.
Prints a clear ✓/✗ status table and exits 0 if core services are up.
"""

import os
import sys
import json
import socket
import urllib.request
import urllib.error
from typing import Callable


# ── Config from environment ────────────────────────────────────────────────────

TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
GEMMA_ENDPOINT = os.environ.get("GEMMA_ENDPOINT", "")
GEMMA_API_KEY = os.environ.get("GEMMA_API_KEY", "")
KEPLER_EXPORTER = os.environ.get("KEPLER_EXPORTER_URL", "")  # e.g. http://kepler-exporter:9102


# ── Helpers ────────────────────────────────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check(name: str, fn: Callable[[], tuple[bool, str]], required: bool = True) -> bool:
    """Run a check function, return True if passed."""
    try:
        ok, detail = fn()
    except Exception as exc:
        ok, detail = False, str(exc)[:120]

    icon = f"{GREEN}✓{RESET}" if ok else (f"{RED}✗{RESET}" if required else f"{YELLOW}~{RESET}")
    req_label = "required" if required else "optional"
    status = "OK" if ok else "FAIL"
    color = GREEN if ok else (RED if required else YELLOW)
    print(f"  {icon}  {BOLD}{name:<30}{RESET} [{color}{status}{RESET}]  {detail}")
    return ok


def http_get(url: str, timeout: int = 10) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode(errors="replace")[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:200]


def tcp_reachable(host: str, port: int, timeout: int = 5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


# ── Individual checks ──────────────────────────────────────────────────────────

def check_temporal() -> tuple[bool, str]:
    parts = TEMPORAL_ADDRESS.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 7233
    ok = tcp_reachable(host, port)
    if ok:
        return True, f"TCP reachable at {TEMPORAL_ADDRESS}"
    return False, f"Cannot reach {TEMPORAL_ADDRESS} — is Temporal running?"


def check_prometheus() -> tuple[bool, str]:
    status, body = http_get(f"{PROMETHEUS_URL}/-/healthy")
    if status == 200:
        return True, f"Healthy at {PROMETHEUS_URL}"
    return False, f"HTTP {status}: {body[:80]}"


def check_prometheus_backend_target() -> tuple[bool, str]:
    status, body = http_get(f"{PROMETHEUS_URL}/api/v1/targets")
    if status != 200:
        return False, f"Cannot query targets (HTTP {status})"
    try:
        data = json.loads(body)
        targets = data.get("data", {}).get("activeTargets", [])
        backend_targets = [
            t for t in targets if "compute-csi-backend" in t.get("labels", {}).get("job", "")
        ]
        if not backend_targets:
            return False, "No compute-csi-backend scrape target found — check prometheus.yml"
        up = [t for t in backend_targets if t.get("health") == "up"]
        return bool(up), f"{len(up)}/{len(backend_targets)} compute-csi-backend targets UP"
    except json.JSONDecodeError:
        return False, "Invalid JSON from Prometheus targets API"


def check_kepler() -> tuple[bool, str]:
    if not KEPLER_EXPORTER:
        return False, "KEPLER_EXPORTER_URL not set — Kepler requires Kubernetes (see monitoring/README.md)"
    status, body = http_get(f"{KEPLER_EXPORTER}/metrics", timeout=5)
    if status == 200 and "kepler_container_joules_total" in body:
        return True, f"Kepler metrics available at {KEPLER_EXPORTER}"
    if status == 200:
        return False, "Endpoint reachable but kepler_container_joules_total not found"
    return False, f"HTTP {status} from {KEPLER_EXPORTER}"


def check_gemma() -> tuple[bool, str]:
    if not GEMMA_ENDPOINT:
        return False, "GEMMA_ENDPOINT not configured (set in .env)"
    headers = {"Accept": "application/json"}
    if GEMMA_API_KEY:
        headers["Authorization"] = f"Bearer {GEMMA_API_KEY}"
    try:
        req = urllib.request.Request(f"{GEMMA_ENDPOINT}/health", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True, f"Gemma reachable at {GEMMA_ENDPOINT} (HTTP {resp.status})"
    except urllib.error.HTTPError as e:
        # 404 on /health is still "reachable"
        if e.code in (404, 405):
            return True, f"Gemma endpoint reachable (HTTP {e.code} on /health — endpoint exists)"
        return False, f"HTTP {e.code} from Gemma endpoint"
    except Exception as exc:
        return False, str(exc)[:100]


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print()
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"  {BOLD}Compute CSI — Integration Verification{RESET}")
    print(f"{'=' * 60}")
    print(f"  TEMPORAL_ADDRESS : {TEMPORAL_ADDRESS}")
    print(f"  PROMETHEUS_URL   : {PROMETHEUS_URL}")
    print(f"  GEMMA_ENDPOINT   : {GEMMA_ENDPOINT or '(not set)'}")
    print(f"  KEPLER_EXPORTER  : {KEPLER_EXPORTER or '(not set)'}")
    print(f"{'=' * 60}\n")

    print(f"  {'Service':<32} {'Status':<10}  Detail")
    print(f"  {'-'*30}  {'-'*8}  {'-'*30}")

    # Core (required) services
    temporal_ok = check("Temporal gRPC", check_temporal, required=True)
    prometheus_ok = check("Prometheus", check_prometheus, required=True)
    check("Prometheus → backend target", check_prometheus_backend_target, required=False)

    # Optional services
    check("Kepler energy exporter", check_kepler, required=False)
    check("Gemma AI endpoint", check_gemma, required=False)

    print()
    core_ok = temporal_ok and prometheus_ok

    if core_ok:
        print(f"  {GREEN}{BOLD}Core services are UP.{RESET} System is operational.\n")
        sys.exit(0)
    else:
        missing = []
        if not temporal_ok:
            missing.append("Temporal")
        if not prometheus_ok:
            missing.append("Prometheus")
        print(
            f"  {RED}{BOLD}Core services DOWN: {', '.join(missing)}{RESET}\n"
            f"  Run `make dev-start` or `temporal server start-dev` to fix.\n"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
