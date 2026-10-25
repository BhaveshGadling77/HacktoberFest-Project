# Compute CSI — AI Infrastructure Forensics

> Evidence-based root-cause investigation, observability correlation, and anomaly attribution for distributed AI compute workloads.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.5-009688.svg)](https://fastapi.tiangolo.com)
[![Temporal](https://img.shields.io/badge/Temporal-1.25%2B-black.svg)](https://temporal.io)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4-38bdf8.svg)](https://tailwindcss.com/)

---

## 1. Overview & Mission

When an AI inference or training workload fails, experiences latency degradation, triggers repeated activity retries, or consumes abnormal amounts of energy, **Compute CSI** investigates the raw forensic evidence to explain what actually happened.

Rather than relying on speculative AI hallucination or fabricated metrics, Compute CSI correlates:
1. **Temporal Workflow History**: Authoritative trace of activity attempts, scheduled/started events, timeouts, and retry policies.
2. **Prometheus Telemetry**: Real infrastructure time series (CPU utilization, memory consumption).
3. **Kepler Energy Telemetry**: eBPF-derived RAPL energy measurements (where deployed in a supported Kubernetes cluster).
4. **Baseline Execution Reference**: Statistical median comparison (minimum 3 samples) for duration and resource consumption.
5. **Deterministic Forensic Engine**: Strict rule-based detection classifying facts, derived metrics, and limitations.
6. **Optional Gemma AI Explanations**: Structured incident synthesis with explicit uncertainty caveats and evidence grounding.

---

## 2. Architecture

```text
React 18 + Vite + Tailwind Console (Port 5173)
           │
           │ REST API (JSON)
           ▼
FastAPI Forensic Backend (Port 8000)
    │
    ├──► Temporal Orchestration Client (Port 7233)
    │        └──► InferenceWorkflow & Activities (Worker)
    │                  ├── Normal Execution
    │                  ├── Controlled Fault Injection (FIRST_ATTEMPT_FAIL)
    │                  ├── Artificial Latency Delay
    │                  └── Repeated Matrix Loops
    │
    ├──► Prometheus Client (Port 9090)
    │        ├── CPU & Memory Time Series
    │        └── Kepler eBPF Energy Exporter (Port 9102, conditional)
    │
    ├──► Evidence Collector & Baseline Engine (SQLite / PostgreSQL)
    │
    ├──► Deterministic Investigation Rules Engine
    │
    ├──► Gemma 2 LLM Serving Adapter (Optional)
    │
    └──► JarvisLabs Remote GPU Adapter (Optional)
```

---

## 3. Core Demo Scenario

1. A developer launches an AI inference workload via the **Compute CSI Console** (`/workloads`).
2. **Experiment A (Baseline)**: Workload runs cleanly in ~0.05s with 1 attempt and 0 failures. Baseline is established.
3. **Experiment B (Fault Injection)**: Workload runs with `FIRST_ATTEMPT_FAIL` fault scenario.
   - Activity attempt 1 deliberately raises `InjectedFaultError`.
   - Temporal detects failure, applies exponential backoff, and schedules attempt 2.
   - Activity attempt 2 succeeds.
4. **Forensics**: Compute CSI correlates the Temporal execution ledger, Prometheus scrape window, and baseline comparisons.
5. **Investigation Report**:
   - **Verified Fact**: Recorded 2 attempts, 1 failure, and increased execution time.
   - **Limitation**: Honestly flags Kepler energy metrics as unavailable if eBPF/K8s is not detected.
   - **AI Synthesis**: Generates root-cause hypothesis using Gemma without fabricating missing metrics.

---

## 4. Quickstart & Local Setup

### Prerequisites
- Python 3.12 (`python3.12` or managed via `uv`)
- Node.js 18+ & npm
- Docker & Docker Compose (optional for full containerized stack)
- Temporal CLI (`temporal server start-dev`)

### Option A: Complete Docker Compose Stack

Start all 7 services (Postgres, Temporal Server, Temporal Web UI, Prometheus, Backend, Worker, Frontend):

```bash
cd compute-csi
docker compose up -d --build
```

Access the interfaces:
- **Compute CSI Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI OpenAPI Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Temporal Web UI**: [http://localhost:8233](http://localhost:8233)
- **Prometheus Console**: [http://localhost:9090](http://localhost:9090)

---

### Option B: Local Development (Native)

#### 1. Start Temporal Dev Server
```bash
temporal server start-dev --ui-port 8233
```

#### 2. Backend Setup
```bash
cd compute-csi/backend
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e .
uvicorn app.main:app --reload --port 8000
```

#### 3. Temporal Worker Setup
```bash
cd compute-csi/worker
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e .
python worker.py
```

#### 4. Frontend Setup
```bash
cd compute-csi/frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 5. Environment Variables (`.env.example`)

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./compute_csi.db` | Application persistence ledger |
| `TEMPORAL_ADDRESS` | `localhost:7233` | Temporal gRPC cluster address |
| `TEMPORAL_NAMESPACE`| `default` | Temporal target namespace |
| `TEMPORAL_TASK_QUEUE`| `compute-csi-queue` | Worker queue name |
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus HTTP query API |
| `KEPLER_ENABLED` | `false` | Enable Kepler energy queries |
| `GEMMA_ENDPOINT` | `""` | Optional HTTP endpoint for Gemma serving |
| `GEMMA_API_KEY` | `""` | Optional Bearer token for Gemma endpoint |
| `GEMMA_MODEL` | `gemma2-2b-it` | Target model identifier |
| `JARVISLABS_API_KEY`| `""` | Optional API key for remote JarvisLabs GPUs |
| `JARVISLABS_INSTANCE_URL` | `""` | Optional JarvisLabs instance URL |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend backend API URL |

---

## 6. REST API Reference

All routes are available under `/api/v1` and aliased under `/api`:

### Health & Dashboard
- `GET /health` — Service health probe.
- `GET /api/v1/dashboard/summary` — Aggregated runs, incidents, retry count, and integration health.

### Workload Dispatch & Runs
- `GET /api/v1/workloads` — List supported workload templates and execution modes.
- `POST /api/v1/runs` — Schedule an inference workload on Temporal.
- `GET /api/v1/runs` — Paginated execution records.
- `GET /api/v1/runs/{run_id}` — Full run details including execution status and timestamps.
- `GET /api/v1/runs/{run_id}/timeline` — Sequence of Temporal activity events.
- `GET /api/v1/runs/{run_id}/metrics` — Prometheus and Kepler metric time series for run window.
- `POST /api/v1/runs/{run_id}/cancel` — Cancel a running Temporal workflow execution.

### Forensics & Incidents
- `GET /api/v1/incidents` — Filterable incident ledger by severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- `GET /api/v1/incidents/{incident_id}` — Complete forensic investigation report.
- `POST /api/v1/incidents/{incident_id}/investigate` — Trigger forensic re-investigation.
- `POST /api/v1/runs/{run_id}/investigate` — Escalate a workload run into an anomaly investigation.

### Integrations
- `GET /api/v1/integrations/status` — Live probe results for Temporal, Prometheus, Kepler, Gemma, and JarvisLabs.

---

## 7. Observability & Kepler Boundaries

### Kepler Requirements and Local Docker
Kepler uses Linux kernel features and hardware power counters (such as Intel/AMD RAPL) to measure energy consumption. Kubernetes is supported, and this project also provides an optional Docker Compose service for Linux hosts:

```bash
docker compose --profile kepler up -d --build
```

Prometheus must show the `kepler` target as UP at `http://localhost:9090/targets`. Docker Desktop may expose only its Linux VM, and hosts without supported energy sensors may not report energy metrics.
- **Honest Status**: If Kepler is not discovered in Prometheus, Compute CSI returns:
  ```json
  {
    "available": false,
    "unavailability_reason": "No Kepler energy metrics found in Prometheus"
  }
  ```
  It **never** fabricates fake energy curves.

### Remote GPU Monitoring Boundaries
Workloads dispatched to remote GPU providers (e.g., JarvisLabs) run outside the local Kubernetes cluster. Kepler cannot automatically observe external cloud instances. Compute CSI isolates remote GPU execution metadata from local node energy measurements.

---

## 8. Verification & Controlled Experiments

### Run Integration Verification
```bash
python scripts/verify_integrations.py
```
Checks reachability of Temporal, Prometheus, Kepler exporter, and Gemma, printing a status matrix.

### Seed Baseline and Fault Injection Runs
```bash
python scripts/seed_demo.py
```
Dispatches 3 baseline runs, waits for completion, triggers a controlled failure retry workflow, and executes an automated forensic investigation.

### Run Controlled Experiments
```bash
# Experiment A: Clean baseline execution
python scripts/run_experiment.py --experiment a --repeat 3

# Experiment B: Controlled activity failure and Temporal retry
python scripts/run_experiment.py --experiment b

# Experiment C: Injected latency delay
python scripts/run_experiment.py --experiment c

# Experiment D: Metrics collection & baseline deviation check
python scripts/run_experiment.py --experiment d
```

---

## 9. Running Automated Tests

```bash
# Backend unit & integration tests
cd backend
.venv/bin/pytest tests/ -v

# Worker & live Temporal retry tests
cd ../worker
.venv/bin/pytest tests/ -v

# Frontend TypeScript verification & build
cd ../frontend
npm run build
```

---

## 10. Hackathon Implementation Summary

| Capability | Status | Implementation Details |
| :--- | :---: | :--- |
| **Real Temporal Workflows** | Verified ✓ | `InferenceWorkflow` with configurable `RetryPolicy` |
| **Reproducible Fault Injection** | Verified ✓ | `FIRST_ATTEMPT_FAIL` injected in `run_inference_activity` |
| **Temporal Event History** | Verified ✓ | Parses real history events from Temporal gRPC handle |
| **Prometheus Integration** | Verified ✓ | Live HTTP queries for CPU/Memory and PromQL deltas |
| **Kepler Profiling Adapter** | Verified ✓ | Transparent metric discovery with honest fallback |
| **Baseline Service** | Verified ✓ | Configurable sample threshold (min 3) and median calculation |
| **Deterministic Forensic Engine** | Verified ✓ | Rules for repeated attempts, duration anomalies, missing data |
| **Gemma 2 AI Explanations** | Verified ✓ | Adapter with prompt grounding and deterministic fallback |
| **JarvisLabs GPU Adapter** | Verified ✓ | HTTP client adapter with configuration check |
| **Dark Forensics UI Dashboard** | Verified ✓ | React 18, Tailwind CSS, Recharts, TanStack Query |
