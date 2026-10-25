# Monitoring — Prometheus & Kepler

This directory contains monitoring configuration for **Compute CSI — AI Infrastructure Forensics**.

---

## What Prometheus Collects

Prometheus scrapes itself, the backend, and Kepler endpoints listed in `kepler-targets.json`:

| Job | Target | Purpose |
|-----|--------|---------|
| `prometheus` | `localhost:9090` | Prometheus self-monitoring |
| `compute-csi-backend` | `backend:8000/metrics` | FastAPI application metrics (request counts, latencies, active workflows, error rates) |
| `kepler` | `kepler-targets.json` | Kepler energy metrics from a supported Linux/Kubernetes deployment |

The backend exposes standard [Prometheus Python client](https://github.com/prometheus/client_python) metrics via the `/metrics` endpoint, including:
- HTTP request duration histograms (`http_request_duration_seconds`)
- Active Temporal workflow gauges (`temporal_active_workflows`)
- Experiment run counters and error rates
- Database query latencies

---

## What Kepler Is

[Kepler](https://sustainable-computing.io/) (Kubernetes-based Efficient Power Level Exporter) is an open-source CNCF project that uses **eBPF** probes and hardware performance counters to measure per-process and per-container energy consumption.

### Requirements

> [!IMPORTANT]
> The opt-in Compose service is intended for Linux hosts. Docker Desktop may expose its Linux VM rather than the physical host, and hardware energy sensors may not be available.

| Requirement | Details |
|-------------|---------|
| **Kubernetes** | Needed for Kubernetes pod attribution; the Compose service can export host and process metrics without Kubernetes |
| **Linux kernel ≥ 4.18** | Required for eBPF support |
| **eBPF / BCC** | Kernel must be compiled with eBPF support (`CONFIG_BPF=y`) |
| **Host access** | Compose uses host PID visibility, read-only `/proc` and `/sys`, and `SYS_PTRACE` to collect host metrics |
| **Hardware PMU** | CPU Performance Monitoring Units for accurate power estimates; falls back to model-based estimates if unavailable |
| **RAPL** | Intel Running Average Power Limit (AMD alternatives exist) for CPU socket/package power |

### Run Kepler with the Compose stack

The Kepler service and Prometheus scrape target are configured. On a supported
Linux host, start the stack with the Kepler profile:

```bash
docker compose --profile kepler up --build
```

Prometheus scrapes `kepler:28282` on the Compose network. Kepler metrics are
also published at `http://localhost:28282/metrics`. The target is configured
in `monitoring/kepler-targets.json`.

Check Prometheus scrape status at `http://localhost:9090/targets`, then check
Compute CSI integration status at
`http://localhost:8000/api/v1/integrations/status`. Kepler should show as
connected when it exports one of the CPU energy counters recognized by the
adapter.

If Kepler is already running in Kubernetes or on another host, replace the
target in `monitoring/kepler-targets.json` with an address reachable from the
Prometheus container. For Kubernetes installation options, see Kepler’s
[official installation guide](https://github.com/sustainable-computing-io/kepler/blob/main/docs/user/installation.md).

Stop Kepler while leaving the rest of the stack running with:

```bash
docker compose stop kepler
```

This service reads host `/proc` and `/sys`. Docker Desktop and non-Linux Docker
hosts may expose only a VM's metrics, and they may not expose physical hardware
energy readings.

---

## Kepler Metric Reference

| Metric | Type | Description |
|--------|------|-------------|
| `kepler_container_joules_total` | Counter | Total energy (joules) consumed by a container |
| `kepler_container_core_joules_total` | Counter | Energy from CPU cores |
| `kepler_container_dram_joules_total` | Counter | Energy from DRAM |
| `kepler_container_uncore_joules_total` | Counter | Energy from uncore components (LLC, IMC) |
| `kepler_container_package_joules_total` | Counter | Total CPU package energy |
| `kepler_container_gpu_joules_total` | Counter | GPU energy (requires NVML) |
| `kepler_container_other_joules_total` | Counter | Other platform energy |
| `kepler_node_package_joules_total` | Counter | Total node CPU package energy |
| `kepler_node_dram_joules_total` | Counter | Total node DRAM energy |

All container metrics include labels: `container_id`, `container_name`, `pod_name`, `namespace`, `node`.

### Sample PromQL Queries

```promql
# Container power in watts (rate over 1 minute)
rate(kepler_container_joules_total[1m])

# Top 5 energy-consuming containers
topk(5, rate(kepler_container_joules_total[5m]))

# Energy efficiency: joules per API request
rate(kepler_container_joules_total[5m]) / rate(http_request_duration_seconds_count[5m])
```

---

## Why Kepler Cannot Monitor JarvisLabs GPU Workloads

JarvisLabs provides **remote GPU instances** (cloud VMs) that run entirely outside your Kubernetes cluster. Kepler's eBPF probes only instrument **local kernel processes** on the nodes it is deployed to.

| Scenario | Kepler Coverage |
|----------|----------------|
| Pods running in your K8s cluster | ✅ Full coverage (CPU + GPU if NVML enabled) |
| Containers on Docker Compose host | ❌ No (no DaemonSet, no eBPF privileges) |
| JarvisLabs remote GPU instance | ❌ No (separate host, different kernel, no Kepler agent) |

**Alternatives for JarvisLabs energy tracking:**
1. **JarvisLabs API** — poll instance-hours and multiply by instance TDP (approximate)
2. **NVML / nvidia-smi** — if you have SSH access to the JarvisLabs instance, you can run `nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits` and ship metrics to your Prometheus via a custom exporter
3. **Carbon-aware estimation** — use instance type TDP × compute time × regional carbon intensity (e.g., via [Cloud Carbon Footprint](https://www.cloudcarbonfootprint.org/))

---

## Verifying Kepler Metrics Are Available

```bash
# Check if Kepler exporter is reachable
curl -s http://<kepler-exporter-host>:9102/metrics | grep kepler_container_joules_total

# Verify Prometheus is scraping Kepler
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | grep kepler

# Query a Kepler metric
curl -s 'http://localhost:9090/api/v1/query?query=kepler_container_joules_total' | python3 -m json.tool
```

If the metric returns empty results, check:
1. Kepler DaemonSet pods are `Running`: `kubectl get pods -n kepler`
2. Prometheus target is `UP`: http://localhost:9090/targets
3. The scrape config host/port matches the Kepler service

---

## Supported Deployment Topology

```
┌─────────────────────────────────────────────────────────────────┐
│  Docker Compose (local dev / this project)                      │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ postgres │  │ temporal │  │ backend  │──▶│ prometheus   │   │
│  │ :5432    │  │ :7233    │  │ :8000    │  │ :9090        │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│       ▲              ▲             ▲                             │
│       └──────────────┴─────────────┘                            │
│                   worker + frontend                              │
└─────────────────────────────────────────────────────────────────┘
         │  API calls to remote GPU
         ▼
┌─────────────────────────┐
│  JarvisLabs GPU Instance │   (separate cloud host — no Kepler)
│  GPU inference / training│
└─────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Kubernetes cluster (Kepler-capable deployment)                  │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────────────────┐  │
│  │  Node 1  │  │  Node 2  │  │  Node N                     │  │
│  │┌────────┐│  │┌────────┐│  │┌────────┐                   │  │
│  ││ Kepler ││  ││ Kepler ││  ││ Kepler │  (DaemonSet)      │  │
│  ││ :9102  ││  ││ :9102  ││  ││ :9102  │                   │  │
│  │└────────┘│  │└────────┘│  │└────────┘                   │  │
│  └──────────┘  └──────────┘  └─────────────────────────────┘  │
│                       ▲                                          │
│              ┌─────────────────┐                                │
│              │   Prometheus    │◀── scrapes all Kepler pods     │
│              └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```
