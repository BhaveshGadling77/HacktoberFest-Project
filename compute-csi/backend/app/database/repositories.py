from __future__ import annotations

import json
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import WorkloadRun, BaselineSample, Incident, InvestigationReport
from app.core.logging import get_logger

logger = get_logger(__name__)


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkloadRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: dict) -> WorkloadRun:
        run = WorkloadRun(**data)
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_by_id(self, run_id: str) -> Optional[WorkloadRun]:
        result = await self.session.execute(select(WorkloadRun).where(WorkloadRun.id == run_id))
        return result.scalar_one_or_none()

    async def get_by_workflow_id(self, workflow_id: str) -> Optional[WorkloadRun]:
        result = await self.session.execute(select(WorkloadRun).where(WorkloadRun.workflow_id == workflow_id))
        return result.scalar_one_or_none()

    async def list_all(self, page: int = 1, page_size: int = 20) -> tuple[List[WorkloadRun], int]:
        offset = (page - 1) * page_size
        count_result = await self.session.execute(select(func.count()).select_from(WorkloadRun))
        total = count_result.scalar_one()
        result = await self.session.execute(
            select(WorkloadRun).order_by(desc(WorkloadRun.created_at)).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def update(self, run_id: str, data: dict) -> Optional[WorkloadRun]:
        run = await self.get_by_id(run_id)
        if not run:
            return None
        data["updated_at"] = utcnow_iso()
        for k, v in data.items():
            setattr(run, k, v)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def count_by_status(self, status: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(WorkloadRun).where(WorkloadRun.status == status)
        )
        return result.scalar_one()

    async def get_recent(self, limit: int = 5) -> List[WorkloadRun]:
        result = await self.session.execute(
            select(WorkloadRun).order_by(desc(WorkloadRun.created_at)).limit(limit)
        )
        return list(result.scalars().all())

    async def sum_retries(self) -> int:
        result = await self.session.execute(select(func.sum(WorkloadRun.attempt_count)).select_from(WorkloadRun))
        val = result.scalar_one()
        return val or 0


class BaselineSampleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: dict) -> BaselineSample:
        sample = BaselineSample(**data)
        self.session.add(sample)
        await self.session.commit()
        await self.session.refresh(sample)
        return sample

    async def get_by_workload(self, workload_type: str, execution_mode: str) -> List[BaselineSample]:
        result = await self.session.execute(
            select(BaselineSample)
            .where(BaselineSample.workload_type == workload_type)
            .where(BaselineSample.execution_mode == execution_mode)
            .order_by(desc(BaselineSample.created_at))
            .limit(100)
        )
        return list(result.scalars().all())


class IncidentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: dict) -> Incident:
        incident = Incident(**data)
        self.session.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def get_by_id(self, incident_id: str) -> Optional[Incident]:
        result = await self.session.execute(select(Incident).where(Incident.id == incident_id))
        return result.scalar_one_or_none()

    async def get_by_run_id(self, run_id: str) -> Optional[Incident]:
        result = await self.session.execute(select(Incident).where(Incident.run_id == run_id))
        return result.scalar_one_or_none()

    async def list_all(
        self,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Incident], int]:
        query = select(Incident)
        count_query = select(func.count()).select_from(Incident)
        if severity:
            query = query.where(Incident.severity == severity.upper())
            count_query = count_query.where(Incident.severity == severity.upper())
        if status:
            query = query.where(Incident.status == status.upper())
            count_query = count_query.where(Incident.status == status.upper())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()
        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(desc(Incident.created_at)).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Incident))
        return result.scalar_one()

    async def get_recent(self, limit: int = 5) -> List[Incident]:
        result = await self.session.execute(
            select(Incident).order_by(desc(Incident.created_at)).limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, incident_id: str, data: dict) -> Optional[Incident]:
        incident = await self.get_by_id(incident_id)
        if not incident:
            return None
        data["updated_at"] = utcnow_iso()
        for k, v in data.items():
            setattr(incident, k, v)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident


class InvestigationReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: dict) -> InvestigationReport:
        report = InvestigationReport(**data)
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_by_incident_id(self, incident_id: str) -> Optional[InvestigationReport]:
        result = await self.session.execute(
            select(InvestigationReport)
            .where(InvestigationReport.incident_id == incident_id)
            .order_by(desc(InvestigationReport.created_at))
        )
        return result.scalars().first()
