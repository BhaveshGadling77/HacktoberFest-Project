# Compute CSI — AI Infrastructure Forensics

**Compute CSI** is an end-to-end AI infrastructure forensics platform that investigates workload failures, latency spikes, repeated retries, and energy anomalies using real workflow orchestration, deterministic root-cause rules, and Prometheus/Kepler telemetry.

## Directory Structure
- **[`compute-csi/`](./compute-csi/)** — Complete application code:
  - **`backend/`** — FastAPI backend, database models, evidence collector, and forensic engine.
  - **`worker/`** — Temporal worker, inference workflows, and deterministic fault injection.
  - **`frontend/`** — React 18, Vite, TypeScript, Tailwind CSS, Recharts forensics console.
  - **`monitoring/`** — Prometheus configuration and Kepler observability guide.
  - **`scripts/`** — Integration verification, demo seeding, and automated experiment runners.
  - **`docker-compose.yml`** — 7-service containerized environment.
  - **`Makefile`** — Automation commands for dev, build, testing, and seeding.

Refer to [`compute-csi/README.md`](./compute-csi/README.md) for full architecture details, local setup instructions, API specifications, and demo workflows.
