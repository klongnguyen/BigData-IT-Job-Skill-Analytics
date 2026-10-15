"""Forecast permission must not be inferred from descriptive monthly counts."""

import pytest

from src.analytics.predictive_gate import assess_predictive_gate, require_predictive_go


def test_gap_and_changed_source_keep_predictive_gate_closed():
    rows = [
        {"source": "archive", "occupation": "Data Engineer", "month": f"2023-{month:02d}", "job_count": 35}
        for month in range(1, 13)
    ]
    rows += [
        {"source": "fresh", "occupation": "Data Engineer", "month": f"2026-{month:02d}", "job_count": 35}
        for month in (9, 10)
    ]
    gate = assess_predictive_gate(rows, [{"run_id": "scoped", "status": "partial"}])
    assert gate["decision"] == "NO_GO"
    assert gate["predictive_claims"] == "Insufficient evidence"
    assert "2024-01" in gate["missing_months_between_first_and_last"]
    assert "2025-12" in gate["missing_months_between_first_and_last"]
    assert next(check for check in gate["checks"] if check["id"] == "source_comparability")["status"] == "FAIL"
    assert next(check for check in gate["checks"] if check["id"] == "input_scope")["status"] == "FAIL"
    assert any(series["meets_minimum_support"] for series in gate["source_occupation_series"])
    with pytest.raises(RuntimeError, match="not GO"):
        require_predictive_go(gate)


def test_gate_rejects_duplicate_month_and_never_grants_go_from_counts():
    row = {"source": "archive", "occupation": "Data Analyst", "month": "2023-01", "job_count": 40}
    with pytest.raises(ValueError, match="Duplicate occupation-month"):
        assess_predictive_gate([row, row], [])
    gate = assess_predictive_gate([row], [], policy_decision="GO")
    assert gate["decision"] == "NO_GO"
    with pytest.raises(RuntimeError, match="not GO"):
        require_predictive_go(gate)


def test_market_is_part_of_predictive_identity_and_comparability():
    rows = [
        {"market": "GLOBAL", "source": "same", "occupation": "Data Engineer",
         "month": "2026-10", "job_count": 50},
        {"market": "US_FEDERAL", "source": "same", "occupation": "Data Engineer",
         "month": "2026-10", "job_count": 500},
    ]
    gate = assess_predictive_gate(rows, [])
    assert gate["decision"] == "NO_GO"
    assert len(gate["source_occupation_series"]) == 2
    assert {(row["market"], row["jobs"]) for row in gate["source_months"]} == {
        ("GLOBAL", 50), ("US_FEDERAL", 500)}
    assert next(check for check in gate["checks"] if check["id"] == "source_comparability")["status"] == "NOT_ELIGIBLE"
