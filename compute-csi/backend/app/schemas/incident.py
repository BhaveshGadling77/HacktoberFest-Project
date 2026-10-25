from __future__ import annotations

from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingType(str, Enum):
    REPEATED_ATTEMPTS = "REPEATED_ATTEMPTS"
    FAILED_ATTEMPTS = "FAILED_ATTEMPTS"
    DURATION_ANOMALY = "DURATION_ANOMALY"
    ENERGY_ANOMALY = "ENERGY_ANOMALY"
    CPU_ANOMALY = "CPU_ANOMALY"
    MISSING_DATA = "MISSING_DATA"


class EvidenceItem(BaseModel):
    evidence_id: str
    source: str  # temporal, prometheus, kepler
    evidence_type: str
    timestamp: str
    run_id: Optional[str] = None
    description: str
    raw_value: Optional[Any] = None
    verified: bool = False
    available: bool = True


class Finding(BaseModel):
    finding_id: str
    finding_type: FindingType
    description: str
    severity: Severity
    evidence_refs: List[str] = []
    verified: bool = False
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    uncertainty_note: Optional[str] = None
    suggested_action: Optional[str] = None


class GemmaAnalysis(BaseModel):
    summary: str
    possible_causes: List[str] = []
    evidence_explanation: str
    alternative_explanations: List[str] = []
    recommended_steps: List[str] = []
    uncertainty_note: str = ""
    is_fallback: bool = False


class InvestigationReport(BaseModel):
    report_id: str
    incident_id: str
    run_id: Optional[str] = None
    title: str
    summary: str
    findings: List[Finding] = []
    evidence: List[EvidenceItem] = []
    gemma_analysis: Optional[GemmaAnalysis] = None
    overall_confidence: float = 0.0
    created_at: str
    limitations: List[str] = []


class IncidentSummary(BaseModel):
    incident_id: str
    run_id: Optional[str] = None
    title: str
    severity: str
    status: str
    finding_types: List[str] = []
    created_at: str
