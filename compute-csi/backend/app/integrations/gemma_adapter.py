from __future__ import annotations

import json
from typing import Optional

import httpx
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.incident import GemmaAnalysis

logger = get_logger(__name__)

_FALLBACK_ANALYSIS = GemmaAnalysis(
    summary="AI analysis unavailable — using deterministic findings only.",
    possible_causes=["See findings below for deterministic analysis."],
    evidence_explanation="Gemma model was not available or returned an invalid response.",
    alternative_explanations=[],
    recommended_steps=["Review the findings list for specific recommended actions."],
    uncertainty_note="This is a fallback response. No AI inference was performed.",
    is_fallback=True,
)


class GemmaAdapter:
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.endpoint = endpoint or settings.GEMMA_ENDPOINT
        self.api_key = api_key or settings.GEMMA_API_KEY
        self.model = model or settings.GEMMA_MODEL

    def _is_configured(self) -> bool:
        return bool(self.endpoint)

    def _build_prompt(self, evidence_package: dict) -> str:
        run_id = evidence_package.get("run_id", "unknown")
        findings_count = len(evidence_package.get("findings", []))
        evidence_count = len(evidence_package.get("evidence", []))

        evidence_summary = []
        for e in evidence_package.get("evidence", [])[:10]:
            evidence_summary.append(f"- [{e.get('source','?')}] {e.get('description','')}")

        findings_summary = []
        for f in evidence_package.get("findings", []):
            findings_summary.append(f"- {f.get('finding_type','?')}: {f.get('description','')}")

        prompt = f"""You are an AI infrastructure forensics assistant. Analyze this compute workload incident.

Run ID: {run_id}
Findings ({findings_count} total):
{chr(10).join(findings_summary) or 'None'}

Evidence ({evidence_count} items):
{chr(10).join(evidence_summary) or 'None'}

Baseline comparison: {json.dumps(evidence_package.get('baseline', {}), indent=2)}

Respond ONLY with valid JSON matching this schema:
{{
  "summary": "brief summary of what happened",
  "possible_causes": ["cause1", "cause2"],
  "evidence_explanation": "explain what the evidence shows",
  "alternative_explanations": ["alternative1"],
  "recommended_steps": ["step1", "step2"],
  "uncertainty_note": "what we cannot confirm from the available data"
}}

Only reference evidence items explicitly listed above. Do not invent metrics or events."""
        return prompt

    async def generate_analysis(self, evidence_package: dict) -> GemmaAnalysis:
        if not self._is_configured():
            logger.info("Gemma not configured, returning fallback")
            return _FALLBACK_ANALYSIS

        prompt = self._build_prompt(evidence_package)
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            # Try to extract response text
            response_text = ""
            if "response" in data:
                response_text = data["response"]
            elif "choices" in data and data["choices"]:
                response_text = data["choices"][0].get("text", "") or data["choices"][0].get("message", {}).get("content", "")
            elif "text" in data:
                response_text = data["text"]
            else:
                response_text = json.dumps(data)

            # Extract JSON from response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                parsed = json.loads(json_str)
                return GemmaAnalysis(
                    summary=str(parsed.get("summary", "")),
                    possible_causes=list(parsed.get("possible_causes", [])),
                    evidence_explanation=str(parsed.get("evidence_explanation", "")),
                    alternative_explanations=list(parsed.get("alternative_explanations", [])),
                    recommended_steps=list(parsed.get("recommended_steps", [])),
                    uncertainty_note=str(parsed.get("uncertainty_note", "")),
                    is_fallback=False,
                )
            else:
                logger.warning("Gemma returned non-JSON response")
                return _FALLBACK_ANALYSIS

        except httpx.TimeoutException:
            logger.warning("Gemma request timed out")
            return _FALLBACK_ANALYSIS
        except Exception as e:
            logger.error("Gemma analysis failed", error=str(e))
            return _FALLBACK_ANALYSIS

    async def check_connection(self) -> bool:
        if not self._is_configured():
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try a lightweight request
                response = await client.get(self.endpoint.replace("/generate", "/api/tags").replace("/v1/completions", "/v1/models"))
                return response.status_code < 500
        except Exception:
            return False
