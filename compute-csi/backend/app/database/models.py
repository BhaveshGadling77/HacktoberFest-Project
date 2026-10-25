from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import String, Float, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class WorkloadRun(Base):
    __tablename__ = "workload_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, index=True)
    workload_type: Mapped[str] = mapped_column(String(64))
    execution_mode: Mapped[str] = mapped_column(String(64))
    fault_scenario: Mapped[str] = mapped_column(String(64), default="NONE")
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    start_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    end_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=lambda: utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(String(64), default=lambda: utcnow().isoformat())

    baseline_samples: Mapped[list[BaselineSample]] = relationship("BaselineSample", back_populates="run")
    incidents: Mapped[list[Incident]] = relationship("Incident", back_populates="run")
    investigation_reports: Mapped[list[InvestigationReport]] = relationship("InvestigationReport", back_populates="run")


class BaselineSample(Base):
    __tablename__ = "baseline_samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workload_type: Mapped[str] = mapped_column(String(64))
    execution_mode: Mapped[str] = mapped_column(String(64))
    duration_seconds: Mapped[float] = mapped_column(Float)
    energy_joules: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpu_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workload_runs.id"), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=lambda: utcnow().isoformat())

    run: Mapped[Optional[WorkloadRun]] = relationship("WorkloadRun", back_populates="baseline_samples")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workload_runs.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(512))
    severity: Mapped[str] = mapped_column(String(32), default="LOW")
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    finding_types_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=lambda: utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(String(64), default=lambda: utcnow().isoformat())

    run: Mapped[Optional[WorkloadRun]] = relationship("WorkloadRun", back_populates="incidents")
    investigation_reports: Mapped[list[InvestigationReport]] = relationship("InvestigationReport", back_populates="incident")


class InvestigationReport(Base):
    __tablename__ = "investigation_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"))
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workload_runs.id"), nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    findings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gemma_analysis_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[str] = mapped_column(String(64), default=lambda: utcnow().isoformat())

    incident: Mapped[Incident] = relationship("Incident", back_populates="investigation_reports")
    run: Mapped[Optional[WorkloadRun]] = relationship("WorkloadRun", back_populates="investigation_reports")
