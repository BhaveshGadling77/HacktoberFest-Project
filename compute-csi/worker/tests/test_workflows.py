from __future__ import annotations

import pytest
from activities.fault_injection import FaultInjectionConfig, InjectedFaultError
from activities.inference import _simulate_inference


def test_fault_injection_first_attempt_fail():
    # Attempt 1 should raise InjectedFaultError
    with pytest.raises(InjectedFaultError) as exc_info:
        FaultInjectionConfig.evaluate(fault_scenario="FIRST_ATTEMPT_FAIL", attempt=1)
    assert "Controlled activity failure on attempt 1" in str(exc_info.value)

    # Attempt 2 should succeed without error
    result = FaultInjectionConfig.evaluate(fault_scenario="FIRST_ATTEMPT_FAIL", attempt=2)
    assert result is None


def test_fault_injection_none():
    result = FaultInjectionConfig.evaluate(fault_scenario="NONE", attempt=1)
    assert result is None


def test_simulate_inference():
    res = _simulate_inference(50)
    assert "output_checksum" in res
    assert "dimensions" in res
    assert res["processed_tokens"] == 200
