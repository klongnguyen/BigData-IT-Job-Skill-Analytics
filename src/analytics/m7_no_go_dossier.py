"""Build a reproducible M7 NO-GO evidence dossier from the Phase 03 audit."""

import argparse
from collections import defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT = ROOT / "docs/data/phase03_analytics_audit.json"
DEFAULT_POLICY = ROOT / "docs/planning/go_no_go_report.md"
DEFAULT_OUTPUT = ROOT / "docs/data/m7_no_go_dossier.json"
GOLD_TABLES = {
    "market_stats", "occupation_stats", "skill_evidence_stats",
    "skill_stats", "skill_trends",
}
CHECK_STATUS = {
    "policy_decision": "FAIL",
    "calendar_continuity": "FAIL",
    "source_comparability": "FAIL",
    "occupation_support": "PASS",
    "input_scope": "FAIL",
    "rolling_origin_future_test": "NOT_ELIGIBLE",
}
FORBIDDEN_KEYS = {
    "predictions", "prediction", "model_metrics", "models", "model_score",
    "macro_f1", "balanced_accuracy", "confusion_matrix", "forecast_labels",
    "training_metrics", "test_metrics",
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _month_number(value):
    _require(isinstance(value, str) and len(value) == 7 and value[4] == "-",
             f"Invalid month: {value!r}")
    year, month = int(value[:4]), int(value[5:])
    date(year, month, 1)
    return year * 12 + month - 1


def _month_text(value):
    return f"{value // 12:04d}-{value % 12 + 1:02d}"


def _reject_model_artifacts(value):
    if isinstance(value, dict):
        for key, item in value.items():
            _require(key not in FORBIDDEN_KEYS, f"Model/prediction artifact is not allowed: {key}")
            _reject_model_artifacts(item)
    elif isinstance(value, list):
        for item in value:
            _reject_model_artifacts(item)


def build_dossier(audit_path=DEFAULT_AUDIT, policy_path=DEFAULT_POLICY):
    """Fail closed unless the pinned audit supports the current NO-GO branch."""
    audit_path, policy_path = Path(audit_path), Path(policy_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    _reject_model_artifacts(audit)
    _require(audit.get("analysis_type") == "observed_descriptive_only",
             "Expected observed descriptive Gold only")
    _require(_sha256(policy_path) == audit.get("policy_sha256"),
             "GO/NO-GO policy changed since Gold audit")
    _require(set(audit.get("outputs", {})) == GOLD_TABLES,
             "Expected exactly five descriptive Gold tables")
    _require(all(isinstance(item.get("rows"), int) and item["rows"] >= 0
                 and isinstance(item.get("sha256"), str) and len(item["sha256"]) == 64
                 for item in audit["outputs"].values()), "Incomplete Gold output evidence")
    _require(all(isinstance(audit.get(field), str) and audit[field]
                 for field in ("run_id", "manifest_sha256", "taxonomy_version")),
             "Missing Gold identity or taxonomy")

    gate = audit.get("predictive_gate")
    _require(isinstance(gate, dict), "Missing predictive gate")
    _require(gate.get("decision") == "NO_GO", "Predictive gate is not NO_GO")
    _require(gate.get("predictive_claims") == "Insufficient evidence",
             "Predictive claims are not marked insufficient")
    checks = gate.get("checks")
    _require(isinstance(checks, list) and len(checks) >= len(CHECK_STATUS),
             "Missing gate checks")
    check_by_id = {item.get("id"): item for item in checks if isinstance(item, dict)}
    _require(len(check_by_id) == len(checks), "Duplicate or malformed gate checks")
    for check_id, status in CHECK_STATUS.items():
        _require(check_by_id.get(check_id, {}).get("status") == status,
                 f"Gate check changed or missing: {check_id}")
        _require(bool(check_by_id[check_id].get("detail")),
                 f"Gate check lacks evidence: {check_id}")
    thresholds = gate.get("thresholds")
    _require(thresholds == {
        "min_jobs_per_occupation_month": 30,
        "min_consecutive_months": 12,
        "min_labeled_cutoffs": 3,
    }, "Predictive thresholds diverge from Final Plan")

    observed = gate.get("observed_months")
    missing = gate.get("missing_months_between_first_and_last")
    _require(isinstance(observed, list) and len(observed) >= 2
             and isinstance(missing, list), "Missing calendar evidence")
    observed_numbers = [_month_number(month) for month in observed]
    _require(observed_numbers == sorted(set(observed_numbers)),
             "Observed months are not sorted and unique")
    expected_missing = [_month_text(number) for number in
                        range(observed_numbers[0], observed_numbers[-1] + 1)
                        if number not in set(observed_numbers)]
    _require(missing == expected_missing and missing,
             "Missing-month audit is inconsistent")
    _require(isinstance(gate.get("occupation_months_below_30"), int)
             and gate["occupation_months_below_30"] >= 0,
             "Missing occupation-month support evidence")
    series = gate.get("source_occupation_series")
    _require(isinstance(series, list) and series, "Missing source-occupation evidence")
    for item in series:
        expected = (item["longest_consecutive_eligible_months"] >= 12
                    and item["potential_cutoffs_with_three_lags_and_next_month"] >= 3)
        _require(item.get("meets_minimum_support") is expected,
                 "Inconsistent basic-support flag")
    basic_support = sorted(
        [{"source": item["source"], "occupation": item["occupation"]}
         for item in series if item["meets_minimum_support"]],
        key=lambda item: (item["source"], item["occupation"]),
    )

    input_info = audit.get("input")
    _require(isinstance(input_info, dict) and input_info.get("silver_rows") ==
             input_info.get("provenance_rows") and input_info.get("silver_rows", 0) > 0,
             "Missing Silver/provenance evidence")
    bronze_runs = input_info.get("bronze_runs")
    _require(isinstance(bronze_runs, list) and bronze_runs
             and any(run.get("status") != "complete" for run in bronze_runs),
             "Missing partial/scoped input evidence")
    source_rows = gate.get("source_months")
    _require(isinstance(source_rows, list) and source_rows,
             "Missing source-month evidence")
    sources = defaultdict(lambda: {"months": [], "jobs": 0, "skills_origins": set()})
    for row in source_rows:
        _month_number(row["month"])
        _require(isinstance(row["jobs"], int) and row["jobs"] > 0,
                 "Invalid source-month job count")
        sources[row["source"]]["months"].append(row["month"])
        sources[row["source"]]["jobs"] += row["jobs"]
    _require(sum(item["jobs"] for item in sources.values()) == input_info["silver_rows"],
             "Source-month totals do not match Silver")
    for row in audit.get("skill_evidence_summary", []):
        if row.get("skills_origin") != "missing" and row.get("evidence_jobs", 0) > 0:
            _require(row["source"] in sources, "Skill evidence has unknown source")
            sources[row["source"]]["skills_origins"].add(row["skills_origin"])
    source_scope = [
        {"source": source, "observed_months": sorted(item["months"]),
         "jobs": item["jobs"], "skills_origins": sorted(item["skills_origins"])}
        for source, item in sorted(sources.items())
    ]
    _require(all(item["skills_origins"] for item in source_scope),
             "Missing source-specific skill evidence regimes")

    return {
        "schema_version": 1,
        "milestone": "M7",
        "branch": "no_go_evidence",
        "acceptance_status": "ready_for_review_not_accepted",
        "forecast_model_status": "blocked",
        "m6_status": "blocked",
        "decision": "NO_GO",
        "predictive_claims": "Insufficient evidence",
        "evidence_source": {
            "audit": "docs/data/phase03_analytics_audit.json",
            "audit_sha256": _sha256(audit_path),
            "policy": "docs/planning/go_no_go_report.md",
            "policy_sha256": _sha256(policy_path),
            "gold_run_id": audit["run_id"],
            "gold_manifest_sha256": audit["manifest_sha256"],
            "etl_run_id": input_info.get("etl_run_id"),
            "taxonomy_version": audit["taxonomy_version"],
            "output_tables": {name: audit["outputs"][name] for name in sorted(GOLD_TABLES)},
            "bronze_runs": [
                {key: run[key] for key in ("kind", "run_id", "status", "rows", "manifest_sha256")}
                for run in bronze_runs
            ],
        },
        "data_support": {
            "observed_months": observed,
            "missing_months": missing,
            "missing_month_count": len(missing),
            "occupation_months_below_30": gate["occupation_months_below_30"],
            "basic_support_series_count": len(basic_support),
            "basic_support_series": basic_support,
            "source_scope": source_scope,
            "thresholds": thresholds,
        },
        "gate_checks": checks,
        "publication_scope": "observed analytics only, with source/month/n and provenance",
        "reassessment_requirements": [
            "Verify source licenses and provenance for each new dataset",
            "Acquire comparable real observations across missing months",
            "Validate taxonomy and skill extraction on independent labels",
            "Check occupation-skill label uncertainty and representative future cutoffs",
            "Run leakage-safe rolling-origin backtest against fixed baselines",
            "Update the GO/NO-GO policy and regenerate Gold gate evidence",
        ],
    }


def write_dossier(output_path=DEFAULT_OUTPUT, audit_path=DEFAULT_AUDIT,
                  policy_path=DEFAULT_POLICY):
    dossier = build_dossier(audit_path, policy_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dossier, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    return output_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(write_dossier(args.output, args.audit, args.policy))


if __name__ == "__main__":
    main()
