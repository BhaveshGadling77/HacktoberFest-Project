from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from app.integrations.temporal_client import get_workflow_history
from app.integrations.prometheus_client import PrometheusClient
from app.schemas.incident import EvidenceItem
from app.core.logging import get_logger

logger = get_logger(__name__)


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EvidenceCollector:
    def __init__(self) -> None:
        self.prometheus = PrometheusClient()

    async def collect_evidence(
        self,
        run_id: str,
        workflow_id: Optional[str],
        start_time: Optional[str],
        end_time: Optional[str],
    ) -> List[EvidenceItem]:
        """Collect evidence items from all available sources."""
        evidence: List[EvidenceItem] = []

        # Temporal evidence
        if workflow_id:
            temporal_evidence = await self._collect_temporal_evidence(run_id, workflow_id)
            evidence.extend(temporal_evidence)
        else:
            evidence.append(EvidenceItem(
                evidence_id=str(uuid.uuid4()),
                source="temporal",
                evidence_type="workflow_missing",
                timestamp=utcnow_iso(),
                run_id=run_id,
                description="No Temporal workflow ID associated with this run. Workflow history unavailable.",
                verified=False,
                available=False,
            ))

        # Prometheus evidence
        prometheus_evidence = await self._collect_prometheus_evidence(run_id, start_time, end_time)
        evidence.extend(prometheus_evidence)

        return evidence

    async def _collect_temporal_evidence(self, run_id: str, workflow_id: str) -> List[EvidenceItem]:
        """Collect evidence from Temporal workflow history."""
        evidence: List[EvidenceItem] = []
        try:
            events = await get_workflow_history(workflow_id)
            if not events:
                evidence.append(EvidenceItem(
                    evidence_id=str(uuid.uuid4()),
                    source="temporal",
                    evidence_type="history_unavailable",
                    timestamp=utcnow_iso(),
                    run_id=run_id,
                    description="Temporal workflow history could not be retrieved (Temporal may be offline).",
                    verified=False,
                    available=False,
                ))
                return evidence

            # Add general history availability evidence
            evidence.append(EvidenceItem(
                evidence_id=str(uuid.uuid4()),
                source="temporal",
                evidence_type="workflow_history",
                timestamp=utcnow_iso(),
                run_id=run_id,
                description=f"Temporal workflow history retrieved: {len(events)} events found.",
                raw_value={"event_count": len(events)},
                verified=True,
                available=True,
            ))

            # Track attempts and failures
            attempt_events = [e for e in events if "activity_task_started" in e.get("event_type", "").lower()]
            failure_events = [e for e in events if "activity_task_failed" in e.get("event_type", "").lower()
                              or "timed_out" in e.get("event_type", "").lower()]

            if attempt_events:
                evidence.append(EvidenceItem(
                    evidence_id=str(uuid.uuid4()),
                    source="temporal",
                    evidence_type="activity_attempts",
                    timestamp=attempt_events[0].get("timestamp", utcnow_iso()),
                    run_id=run_id,
                    description=f"Activity was attempted {len(attempt_events)} time(s).",
                    raw_value={"attempt_count": len(attempt_events)},
                    verified=True,
                    available=True,
                ))

            if failure_events:
                for fe in failure_events:
                    failure_msg = fe.get("attributes", {}).get("failure_message", "Unknown failure")
                    evidence.append(EvidenceItem(
                        evidence_id=str(uuid.uuid4()),
                        source="temporal",
                        evidence_type="activity_failure",
                        timestamp=fe.get("timestamp", utcnow_iso()),
                        run_id=run_id,
                        description=f"Activity failed: {failure_msg}",
                        raw_value={"failure_message": failure_msg},
                        verified=True,
                        available=True,
                    ))

        except Exception as e:
            logger.error("Failed to collect Temporal evidence", run_id=run_id, error=str(e))
            evidence.append(EvidenceItem(
                evidence_id=str(uuid.uuid4()),
                source="temporal",
                evidence_type="collection_error",
                timestamp=utcnow_iso(),
                run_id=run_id,
                description=f"Error collecting Temporal evidence: {str(e)}",
                verified=False,
                available=False,
            ))

        return evidence

    async def _collect_prometheus_evidence(
        self,
        run_id: str,
        start_time: Optional[str],
        end_time: Optional[str],
    ) -> List[EvidenceItem]:
        """Collect evidence from Prometheus."""
        evidence: List[EvidenceItem] = []
        try:
            is_connected = await self.prometheus.check_connection()
            if not is_connected:
                evidence.append(EvidenceItem(
                    evidence_id=str(uuid.uuid4()),
                    source="prometheus",
                    evidence_type="prometheus_unavailable",
                    timestamp=utcnow_iso(),
                    run_id=run_id,
                    description="Prometheus is not reachable. Metric-based evidence unavailable.",
                    verified=False,
                    available=False,
                ))
                return evidence

            available_metrics = await self.prometheus.get_available_metrics()
            evidence.append(EvidenceItem(
                evidence_id=str(uuid.uuid4()),
                source="prometheus",
                evidence_type="metrics_availability",
                timestamp=utcnow_iso(),
                run_id=run_id,
                description=f"Prometheus connected. {len(available_metrics)} metrics available.",
                raw_value={"metric_count": len(available_metrics)},
                verified=True,
                available=True,
            ))

        except Exception as e:
            logger.error("Failed to collect Prometheus evidence", run_id=run_id, error=str(e))
            evidence.append(EvidenceItem(
                evidence_id=str(uuid.uuid4()),
                source="prometheus",
                evidence_type="collection_error",
                timestamp=utcnow_iso(),
                run_id=run_id,
                description=f"Error collecting Prometheus evidence: {str(e)}",
                verified=False,
                available=False,
            ))

        return evidence
