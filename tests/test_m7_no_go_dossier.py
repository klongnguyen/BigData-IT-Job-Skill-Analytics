"""M7 evidence must remain tied to the actual NO-GO audit and policy."""

import json
from pathlib import Path

import pytest

from src.analytics.m7_no_go_dossier import (
    DEFAULT_AUDIT, DEFAULT_POLICY, build_dossier, write_dossier,
)


@pytest.fixture
def evidence_copy(tmp_path):
    audit_path = tmp_path / "phase03_analytics_audit.json"
    policy_path = tmp_path / "go_no_go_report.md"
    audit_path.write_bytes(DEFAULT_AUDIT.read_bytes())
    policy_path.write_bytes(DEFAULT_POLICY.read_bytes())
    return audit_path, policy_path


def test_real_audit_builds_no_go_branch_with_measured_support(tmp_path):
    dossier = build_dossier()
    support = dossier["data_support"]
    assert dossier["decision"] == "NO_GO"
    assert dossier["predictive_claims"] == "Insufficient evidence"
    assert dossier["acceptance_status"] == "ready_for_review_not_accepted"
    assert dossier["forecast_model_status"] == dossier["m6_status"] == "blocked"
    assert (support["missing_month_count"], support["occupation_months_below_30"],
            support["basic_support_series_count"]) == (32, 19, 8)
    assert set(support["missing_months"]) >= {"2024-01", "2025-12"}
    assert {item["source"] for item in support["basic_support_series"]} == {
        "kaggle_historical_archive"}
    assert {item["source"]: item["skills_origins"] for item in support["source_scope"]} == {
        "arbeitnow": ["extracted_from_jd"],
        "kaggle_historical_archive": ["source_tags"],
        "remotive": ["extracted_from_jd"],
    }
    assert set(dossier["evidence_source"]["output_tables"]) == {
        "market_stats", "occupation_stats", "skill_evidence_stats",
        "skill_stats", "skill_trends"}
    assert "model_metrics" not in json.dumps(dossier)
    first, second = tmp_path / "one.json", tmp_path / "two.json"
    write_dossier(first)
    write_dossier(second)
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.parametrize("mutation", [
    "go", "missing_claims", "missing_check", "thresholds", "predictions",
    "missing_scope", "calendar", "false_support",
])
def test_rejects_corrupted_or_promoted_gate(evidence_copy, mutation, tmp_path):
    audit_path, policy_path = evidence_copy
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    gate = audit["predictive_gate"]
    if mutation == "go":
        gate["decision"] = "GO"
    elif mutation == "missing_claims":
        gate.pop("predictive_claims")
    elif mutation == "missing_check":
        gate["checks"] = [item for item in gate["checks"]
                          if item["id"] != "rolling_origin_future_test"]
    elif mutation == "thresholds":
        gate["thresholds"]["min_consecutive_months"] = 1
    elif mutation == "predictions":
        audit["outputs"]["predictions"] = {"rows": 1, "sha256": "a" * 64}
    elif mutation == "missing_scope":
        audit["input"]["bronze_runs"][1]["status"] = "complete"
    elif mutation == "calendar":
        gate["missing_months_between_first_and_last"].pop()
    else:
        gate["source_occupation_series"][0]["meets_minimum_support"] = True
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    output = tmp_path / "must_not_exist.json"
    with pytest.raises(ValueError):
        write_dossier(output, audit_path, policy_path)
    assert not output.exists()


def test_rejects_policy_file_changed_after_audit(evidence_copy):
    audit_path, policy_path = evidence_copy
    policy_path.write_text(policy_path.read_text(encoding="utf-8") + "\nchanged", encoding="utf-8")
    with pytest.raises(ValueError, match="policy changed"):
        build_dossier(audit_path, policy_path)


def test_committed_dossier_matches_current_audit():
    path = Path(__file__).resolve().parents[1] / "docs/data/m7_no_go_dossier.json"
    expected = build_dossier()
    assert json.loads(path.read_text(encoding="utf-8")) == expected
