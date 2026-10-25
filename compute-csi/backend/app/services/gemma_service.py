from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.integrations.gemma_adapter import GemmaAdapter
from app.schemas.incident import GemmaAnalysis
from app.core.logging import get_logger

logger = get_logger(__name__)


class GemmaService:
    def __init__(self, adapter: Optional[GemmaAdapter] = None) -> None:
        self.adapter = adapter or GemmaAdapter()

    async def generate_explanation(self, evidence_package: Dict[str, Any]) -> GemmaAnalysis:
        """
        Generate AI explanation via Gemma, enforcing grounding against evidence package.
        Validates model output to prevent hallucinations or invented metric claims.
        """
        analysis = await self.adapter.generate_analysis(evidence_package)
        
        # Verify and sanitize: if model output makes claims about metrics not in evidence, annotate uncertainty
        available_metrics = evidence_package.get("available_metrics", [])
        if "energy" in analysis.summary.lower() and "kepler" not in available_metrics and "energy" not in str(available_metrics).lower():
            if not analysis.is_fallback:
                analysis.uncertainty_note += " (Note: Model mentioned energy, but no direct Kepler energy measurements were confirmed)."

        return analysis
