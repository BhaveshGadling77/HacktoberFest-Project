from __future__ import annotations

from typing import Optional


class InjectedFaultError(Exception):
    """Explicit exception raised during controlled fault injection."""
    pass


class FaultInjectionConfig:
    @staticmethod
    def evaluate(fault_scenario: str, attempt: int, delay_seconds: int = 0) -> Optional[str]:
        """
        Evaluate if a fault should be triggered on this activity attempt.
        Returns a description string if fault injected, or None.
        """
        if fault_scenario == "FIRST_ATTEMPT_FAIL" and attempt == 1:
            raise InjectedFaultError(
                f"[FAULT INJECTION] Controlled activity failure on attempt {attempt}. "
                "Triggering Temporal retry policy."
            )
        elif fault_scenario == "TIMEOUT_THEN_RETRY" and attempt == 1:
            raise InjectedFaultError(
                f"[FAULT INJECTION] Simulated upstream timeout failure on attempt {attempt}."
            )
        return None
