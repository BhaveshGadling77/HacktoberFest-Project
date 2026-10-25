from __future__ import annotations

import json
import uuid
from typing import Optional, List

from app.database.repositories import IncidentRepository, WorkloadRunRepository, InvestigationReportRepository
from app.database.session import AsyncSessionLocal
from app.schemas.incident import IncidentSummary, InvestigationReport, Severity, FindingType
from app.schemas.common import PaginatedResponse
from app.services.investigation_engine import InvestigationEngine
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class IncidentService:
    def __init__(self) -> None:
        self.investigation_engine = InvestigationEngine()

    async def create_incident_for_run(self, run_id: str, title: Optional[str] = None) -> IncidentSummary:
        async with AsyncSessionLocal() as session:
            run_repo = WorkloadRunRepository(session)
            run = await run_repo.get_by_id(run_id)
            if not run:
                raise NotFoundError(f"Run {run_id} not found")

            inc_repo = IncidentRepository(session)
            existing = await inc_repo.get_by_run_id(run_id)
            if existing:
                finding_types = json.loads(existing.finding_types_json) if existing.finding_types_json else []
                return IncidentSummary(
                    incident_id=existing.id,
                    run_id=existing.run_id,
                    title=existing.title,
                    severity=existing.severity,
                    status=existing.status,
                    finding_types=finding_types,
                    created_at=existing.created_at,
                )

            severity = Severity.MEDIUM.value
            finding_types_list = []
            if run.failure_count > 0:
                severity = Severity.HIGH.value
                finding_types_list.append(FindingType.FAILED_ATTEMPTS.value)
            if run.attempt_count > 1:
                finding_types_list.append(FindingType.REPEATED_ATTEMPTS.value)
            if not finding_types_list:
                finding_types_list.append(FindingType.MISSING_DATA.value)

            inc_title = title or f"Incident #{run.id[:8].upper()} — Workflow Retries Detected"
            incident_id = str(uuid.uuid4())
            new_inc = await inc_repo.create({
                "id": incident_id,
                "run_id": run.id,
                "title": inc_title,
                "severity": severity,
                "status": "OPEN",
                "finding_types_json": json.dumps(finding_types_list),
            })

            return IncidentSummary(
                incident_id=new_inc.id,
                run_id=new_inc.run_id,
                title=new_inc.title,
                severity=new_inc.severity,
                status=new_inc.status,
                finding_types=finding_types_list,
                created_at=new_inc.created_at,
            )

    async def list_incidents(
        self,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[IncidentSummary]:
        async with AsyncSessionLocal() as session:
            inc_repo = IncidentRepository(session)
            incidents, total = await inc_repo.list_all(severity=severity, status=status, page=page, page_size=page_size)

        items = []
        for inc in incidents:
            ft = json.loads(inc.finding_types_json) if inc.finding_types_json else []
            items.append(
                IncidentSummary(
                    incident_id=inc.id,
                    run_id=inc.run_id,
                    title=inc.title,
                    severity=inc.severity,
                    status=inc.status,
                    finding_types=ft,
                    created_at=inc.created_at,
                )
            )
        return PaginatedResponse.build(items=items, total=total, page=page, page_size=page_size)

    async def get_incident_report(self, incident_id: str) -> InvestigationReport:
        """Fetch or generate report for an incident."""
        async with AsyncSessionLocal() as session:
            inc_repo = IncidentRepository(session)
            incident = await inc_repo.get_by_id(incident_id)
            if not incident:
                raise NotFoundError(f"Incident {incident_id} not found")

            report_repo = InvestigationReportRepository(session)
            saved_report = await report_repo.get_by_incident_id(incident_id)

        if saved_report:
            findings = [json.loads(f) if isinstance(f, str) else f for f in json.loads(saved_report.findings_json or "[]")]
            evidence = [json.loads(e) if isinstance(e, str) else e for e in json.loads(saved_report.evidence_json or "[]")]
            gemma_data = json.loads(saved_report.gemma_analysis_json) if saved_report.gemma_analysis_json else None

            return InvestigationReport(
                report_id=saved_report.id,
                incident_id=incident.id,
                run_id=incident.run_id,
                title=incident.title,
                summary=saved_report.summary,
                findings=findings,
                evidence=evidence,
                gemma_analysis=gemma_data,
                overall_confidence=saved_report.confidence,
                created_at=saved_report.created_at,
                limitations=[],
            )

        # If no report generated yet, run investigation
        if incident.run_id:
            return await self.investigation_engine.investigate_run(incident.run_id, incident_id=incident.id)

        raise NotFoundError(f"No run associated with incident {incident_id}")

    async def investigate_incident(self, incident_id: str) -> InvestigationReport:
        async with AsyncSessionLocal() as session:
            inc_repo = IncidentRepository(session)
            incident = await inc_repo.get_by_id(incident_id)
            if not incident:
                raise NotFoundError(f"Incident {incident_id} not found")

        if not incident.run_id:
            raise NotFoundError(f"No run linked to incident {incident_id}")

        return await self.investigation_engine.investigate_run(incident.run_id, incident_id=incident.id)
