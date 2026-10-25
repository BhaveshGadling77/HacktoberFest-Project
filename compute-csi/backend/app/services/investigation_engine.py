from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.database.repositories import (
    WorkloadRunRepository,
    IncidentRepository,
    InvestigationReportRepository,
)
from app.database.session import AsyncSessionLocal
from app.schemas.incident import (
    InvestigationReport,
    Finding,
    FindingType,
    Severity,
    EvidenceItem,
)
from app.schemas.run import RunDetail
from app.services.evidence_collector import EvidenceCollector
from app.services.baseline_service import BaselineService
from app.services.metrics_service import MetricsService
from app.services.gemma_service import GemmaService
from app.core.logging import get_logger

logger = get_logger(__name__)


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InvestigationEngine:
    def __init__(self) -> None:
        self.evidence_collector = EvidenceCollector()
        self.baseline_service = BaselineService()
        self.metrics_service = MetricsService()
        self.gemma_service = GemmaService()

    async def investigate_run(self, run_id: str, incident_id: Optional[str] = None) -> InvestigationReport:
        """Run a full forensic investigation on a workload run."""
        async with AsyncSessionLocal() as session:
            run_repo = WorkloadRunRepository(session)
            run = await run_repo.get_by_id(run_id)

        if not run:
            raise ValueError(f"Run {run_id} not found")

        # Collect evidence
        evidence = await self.evidence_collector.collect_evidence(
            run_id=run.id,
            workflow_id=run.workflow_id,
            start_time=run.start_time,
            end_time=run.end_time,
        )

        # Collect metrics
        metrics = await self.metrics_service.get_run_metrics(
            run_id=run.id,
            start_time=run.start_time,
            end_time=run.end_time,
        )

        # Baseline comparison
        run_detail = RunDetail(
            run_id=run.id,
            workflow_id=run.workflow_id or "unknown",
            status=run.status, # type: ignore
            start_time=run.start_time or utcnow_iso(),
            end_time=run.end_time,
            duration_seconds=run.duration_seconds,
            attempt_count=run.attempt_count,
            failure_count=run.failure_count,
            workload_type=run.workload_type, # type: ignore
            execution_mode=run.execution_mode, # type: ignore
            fault_scenario=run.fault_scenario, # type: ignore
            outcome=run.outcome,
            timeline=[],
        )
        baseline_comp = await self.baseline_service.compare_to_baseline(run_detail, metrics)

        # Deterministic analysis rules
        findings: List[Finding] = []
        limitations: List[str] = []

        # Rule 1: Repeated Activity Attempts
        if run.attempt_count > 1:
            matching_evidence = [e.evidence_id for e in evidence if "attempt" in e.description.lower() or "retry" in e.description.lower()]
            findings.append(Finding(
                finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                finding_type=FindingType.REPEATED_ATTEMPTS,
                description=f"Activity was attempted {run.attempt_count} times before finishing. This indicates one or more retry cycles occurred.",
                severity=Severity.HIGH if run.attempt_count > 2 else Severity.MEDIUM,
                evidence_refs=matching_evidence,
                verified=True,
                confidence=1.0,
                uncertainty_note="Attempts recorded in Temporal workflow history are verified facts.",
                suggested_action="Review activity logs for the initial failure cause and review retry policy backoff parameters.",
            ))

        # Rule 2: Failed Activity Attempts
        if run.failure_count > 0:
            matching_evidence = [e.evidence_id for e in evidence if "fail" in e.description.lower()]
            findings.append(Finding(
                finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                finding_type=FindingType.FAILED_ATTEMPTS,
                description=f"Observed {run.failure_count} activity failure(s) during workflow execution.",
                severity=Severity.HIGH,
                evidence_refs=matching_evidence,
                verified=True,
                confidence=1.0,
                uncertainty_note="Recorded in Temporal execution history.",
                suggested_action="Inspect the failure trace to confirm if failure was an injected fault or an infrastructure timeout.",
            ))

        # Rule 3: Duration Anomaly
        if baseline_comp.get("duration_anomaly"):
            dev_pct = baseline_comp.get("duration_deviation_pct", 0)
            findings.append(Finding(
                finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                finding_type=FindingType.DURATION_ANOMALY,
                description=f"Execution duration of {run.duration_seconds:.2f}s deviated by {dev_pct:+.1f}% from the established baseline ({baseline_comp.get('baseline_median_duration', 0):.2f}s).",
                severity=Severity.MEDIUM,
                evidence_refs=[e.evidence_id for e in evidence if e.source == "temporal"],
                verified=True,
                confidence=0.85,
                uncertainty_note="Baseline comparison is statistically reliable (>= 3 samples). Duration increase is consistent with retry delays.",
                suggested_action="Compare workflow timeline with baseline timeline to locate latency contributor.",
            ))
        elif not baseline_comp.get("is_reliable", False):
            limitations.append("Insufficient baseline samples (< 3) to establish a statistically reliable duration baseline.")

        # Rule 4: Energy Anomaly (NEVER claim anomaly if data is unavailable)
        if metrics.energy_joules.available and metrics.energy_joules.points:
            if baseline_comp.get("energy_anomaly"):
                findings.append(Finding(
                    finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                    finding_type=FindingType.ENERGY_ANOMALY,
                    description="Measured energy consumption deviated significantly from the established workload baseline.",
                    severity=Severity.MEDIUM,
                    evidence_refs=[e.evidence_id for e in evidence if e.source == "kepler"],
                    verified=True,
                    confidence=0.75,
                    uncertainty_note="Kepler measurement reflects node/container energy during the execution window. Correlated with repeated attempts.",
                    suggested_action="Audit repeated inference loops to minimize unnecessary energy expenditure.",
                ))
        else:
            limitations.append("Kepler energy metrics were unavailable for this execution window. No energy anomaly conclusions can be drawn.")
            findings.append(Finding(
                finding_id=f"fnd-{uuid.uuid4().hex[:8]}",
                finding_type=FindingType.MISSING_DATA,
                description="Kepler energy metrics are unavailable. Check that the exporter is running, Prometheus is scraping it, and the host exposes supported energy sensors.",
                severity=Severity.LOW,
                evidence_refs=[e.evidence_id for e in evidence if not e.available],
                verified=True,
                confidence=1.0,
                uncertainty_note="Absence of energy metrics is an infrastructure limitation, not a workload failure.",
                suggested_action="Deploy Kepler daemonset in a supported Linux/Kubernetes environment to collect energy measurements.",
            ))

        # Overall confidence score calculation
        if findings:
            overall_confidence = sum(f.confidence for f in findings) / len(findings)
        else:
            overall_confidence = 0.5

        # Prepare evidence package for Gemma AI analysis
        available_metrics_names = [name for name in metrics.raw_available_metrics]
        evidence_package = {
            "run_id": run.id,
            "workflow_id": run.workflow_id,
            "status": run.status,
            "attempt_count": run.attempt_count,
            "failure_count": run.failure_count,
            "duration_seconds": run.duration_seconds,
            "findings": [f.model_dump() for f in findings],
            "evidence": [e.model_dump() for e in evidence],
            "baseline": baseline_comp,
            "available_metrics": available_metrics_names,
        }

        # AI analysis via Gemma (falls back gracefully if not configured)
        gemma_analysis = await self.gemma_service.generate_explanation(evidence_package)

        # Formulate report title & summary
        title = f"INVESTIGATION #{run_id[:8].upper()} — "
        if run.attempt_count > 1 or run.failure_count > 0:
            title += "RETRY & RESOURCE ANOMALY"
            summary = (
                f"Workload {run.workflow_id} experienced {run.attempt_count} activity execution attempts "
                f"with {run.failure_count} recorded failure(s). Temporal orchestration retried the activity, "
                f"completing the workflow in {run.duration_seconds or 0:.2f}s."
            )
        else:
            title += "NOMINAL EXECUTION"
            summary = (
                f"Workload {run.workflow_id} executed normally in {run.duration_seconds or 0:.2f}s "
                f"with 1 attempt and 0 failures."
            )

        report_id = str(uuid.uuid4())
        inc_id = incident_id or str(uuid.uuid4())

        report = InvestigationReport(
            report_id=report_id,
            incident_id=inc_id,
            run_id=run.id,
            title=title,
            summary=summary,
            findings=findings,
            evidence=evidence,
            gemma_analysis=gemma_analysis,
            overall_confidence=round(overall_confidence, 2),
            created_at=utcnow_iso(),
            limitations=limitations,
        )

        # Persist report to database
        async with AsyncSessionLocal() as session:
            report_repo = InvestigationReportRepository(session)
            await report_repo.create({
                "id": report_id,
                "incident_id": inc_id,
                "run_id": run.id,
                "summary": summary,
                "findings_json": json.dumps([f.model_dump() for f in findings]),
                "evidence_json": json.dumps([e.model_dump() for e in evidence]),
                "gemma_analysis_json": json.dumps(gemma_analysis.model_dump()) if gemma_analysis else None,
                "confidence": report.overall_confidence,
            })

        return report
