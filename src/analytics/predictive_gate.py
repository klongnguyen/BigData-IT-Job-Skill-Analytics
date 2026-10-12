"""Evidence gate for predictive claims; descriptive Gold never implies forecast GO."""

from collections import defaultdict
from datetime import date
from pathlib import Path
import json


MIN_JOBS_PER_OCCUPATION_MONTH = 30
MIN_CONSECUTIVE_MONTHS = 12
MIN_LABELED_CUTOFFS = 3


def _month_number(month):
    year, number = (int(part) for part in str(month).split("-"))
    date(year, number, 1)  # Reject malformed calendar months.
    return year * 12 + number - 1


def _month_text(number):
    return f"{number // 12:04d}-{number % 12 + 1:02d}"


def assess_predictive_gate(occupation_rows, input_runs, policy_decision="NO_GO"):
    """Audit support without deriving future labels or training a model.

    A passing data profile would still require a separately approved rolling
    backtest and an explicit policy change. This function never grants GO.
    """
    groups = defaultdict(dict)
    observed_months = set()
    by_source_month = defaultdict(int)
    below_threshold = 0
    for row in occupation_rows:
        month = _month_number(row["month"])
        count = int(row["job_count"])
        if count < 0:
            raise ValueError("Occupation job count cannot be negative")
        key = (str(row["source"]), str(row["occupation"]))
        if month in groups[key]:
            raise ValueError(f"Duplicate occupation-month in gate input: {key}, {row['month']}")
        groups[key][month] = count
        observed_months.add(month)
        by_source_month[(key[0], month)] += count
        below_threshold += count < MIN_JOBS_PER_OCCUPATION_MONTH

    if not observed_months:
        raise ValueError("Predictive gate requires observed occupation-month counts")
    start, end = min(observed_months), max(observed_months)
    missing_months = [_month_text(value) for value in range(start, end + 1)
                      if value not in observed_months]
    series = []
    for (source, occupation), counts in sorted(groups.items()):
        eligible = {month for month, count in counts.items()
                    if count >= MIN_JOBS_PER_OCCUPATION_MONTH}
        longest = current = 0
        for month in sorted(eligible):
            current = current + 1 if month - 1 in eligible else 1
            longest = max(longest, current)
        # Count potential origins only; no t+1 labels are made here.
        cutoff_candidates = sum(
            all(month + offset in eligible for offset in (-3, -2, -1, 0, 1))
            for month in eligible
        )
        series.append({
            "source": source,
            "occupation": occupation,
            "observed_months": len(counts),
            "months_at_least_30_jobs": len(eligible),
            "longest_consecutive_eligible_months": longest,
            "potential_cutoffs_with_three_lags_and_next_month": cutoff_candidates,
            "meets_minimum_support": (
                longest >= MIN_CONSECUTIVE_MONTHS
                and cutoff_candidates >= MIN_LABELED_CUTOFFS
            ),
        })

    source_months = defaultdict(set)
    for source, month in by_source_month:
        source_months[source].add(month)
    source_overlap_months = len(set.intersection(*source_months.values())) if len(source_months) > 1 else 0
    scoped_inputs = [run["run_id"] for run in input_runs if run.get("status") != "complete"]
    checks = [
        {"id": "policy_decision", "status": "FAIL" if policy_decision != "GO" else "PASS",
         "detail": f"Current GO/NO-GO decision: {policy_decision}"},
        {"id": "calendar_continuity", "status": "FAIL" if missing_months else "PASS",
         "detail": f"{len(missing_months)} months without observed input between first and last month"},
        {"id": "source_comparability", "status": "FAIL" if len(source_months) > 1 and not source_overlap_months else "NOT_ELIGIBLE",
         "detail": f"{source_overlap_months} overlapping observed months across sources; no source-mix adjustment established"},
        {"id": "occupation_support", "status": "FAIL" if not any(row["meets_minimum_support"] for row in series) else "PASS",
         "detail": f"{sum(row['meets_minimum_support'] for row in series)} source-occupation series meet basic month/count support"},
        {"id": "input_scope", "status": "FAIL" if scoped_inputs else "PASS",
         "detail": f"{len(scoped_inputs)} selected Bronze runs are partial/scoped"},
        {"id": "rolling_origin_future_test", "status": "NOT_ELIGIBLE",
         "detail": "No representative fixed future test, uncertainty-qualified labels, or rolling-origin comparison was run"},
    ]
    return {
        "decision": "NO_GO",
        "predictive_claims": "Insufficient evidence",
        "thresholds": {
            "min_jobs_per_occupation_month": MIN_JOBS_PER_OCCUPATION_MONTH,
            "min_consecutive_months": MIN_CONSECUTIVE_MONTHS,
            "min_labeled_cutoffs": MIN_LABELED_CUTOFFS,
        },
        "observed_months": [_month_text(value) for value in sorted(observed_months)],
        "missing_months_between_first_and_last": missing_months,
        "source_months": [
            {"source": source, "month": _month_text(month), "jobs": count}
            for (source, month), count in sorted(by_source_month.items())
        ],
        "occupation_months_below_30": below_threshold,
        "source_occupation_series": series,
        "checks": checks,
    }


def require_predictive_go(gate_or_path):
    """Fail closed for any future feature, training, or prediction entrypoint."""
    if isinstance(gate_or_path, (str, Path)):
        gate = json.loads(Path(gate_or_path).read_text(encoding="utf-8"))
    else:
        gate = gate_or_path
    if gate.get("decision") != "GO":
        raise RuntimeError("Predictive gate is not GO; feature, model, and prediction outputs are blocked")
    return gate
