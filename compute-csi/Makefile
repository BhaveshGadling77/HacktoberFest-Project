.PHONY: help dev-start dev-stop dev-logs backend-install worker-install frontend-install test-backend test-worker seed verify-integrations run-experiment

help:
	@echo "Compute CSI - Available commands:"
	@echo "  make dev-start      - Start all services with Docker Compose"
	@echo "  make dev-stop       - Stop all services"
	@echo "  make dev-logs       - Show service logs"
	@echo "  make temporal-dev   - Start Temporal dev server locally"
	@echo "  make backend-run    - Run backend locally (requires Temporal)"
	@echo "  make worker-run     - Run worker locally (requires Temporal)"
	@echo "  make frontend-run   - Run frontend dev server"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-worker    - Run worker tests"
	@echo "  make seed           - Seed demo data"
	@echo "  make verify         - Verify all integrations"
	@echo "  make experiment-a   - Run Experiment A (normal)"
	@echo "  make experiment-b   - Run Experiment B (retry)"

dev-start:
	docker compose up -d
	@echo "Services starting. Frontend: http://localhost:5173 Backend: http://localhost:8000 Temporal UI: http://localhost:8233"

dev-stop:
	docker compose down

dev-logs:
	docker compose logs -f

temporal-dev:
	temporal server start-dev --ui-port 8233

backend-run:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

worker-run:
	cd worker && .venv/bin/python worker.py

frontend-run:
	cd frontend && npm run dev

backend-install:
	cd backend && uv venv --python 3.12 .venv && source .venv/bin/activate && uv pip install -e .

worker-install:
	cd worker && uv venv --python 3.12 .venv && source .venv/bin/activate && uv pip install -e .

frontend-install:
	cd frontend && npm install

test-backend:
	cd backend && .venv/bin/pytest tests/ -v

test-worker:
	cd worker && .venv/bin/pytest tests/ -v

seed:
	cd backend && .venv/bin/python ../scripts/seed_demo.py

verify:
	cd backend && .venv/bin/python ../scripts/verify_integrations.py

experiment-a:
	python scripts/run_experiment.py --experiment a

experiment-b:
	python scripts/run_experiment.py --experiment b
