"""Audit verified 2026 Bronze runs by source, occupation and observed month."""

import argparse
import json
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from src.common.run_manifest import load_bronze_run
from src.common.taxonomy import TAXONOMY_VERSION, load_dictionaries, normalize_title


def _month(posted_at):
    if not posted_at:
        return None
    try:
        return datetime.fromisoformat(str(posted_at).replace("Z", "+00:00")).strftime("%Y-%m")
    except ValueError:
        return None


def audit_runs(run_dirs, through_month):
    if len(through_month) != 7 or through_month[:5] != "2026-":
        raise ValueError("through_month must be YYYY-MM in 2026")
    last_month = date.fromisoformat(through_month + "-01").month
    if not run_dirs:
        raise ValueError("Select at least one Bronze run")
    selected = {}
    run_evidence = []
    raw_rows = duplicate_rows = invalid_identity_rows = 0
    for run_dir in run_dirs:
        manifest, files, manifest_sha = load_bronze_run(run_dir, "fresh", allow_partial=True)
        if manifest.get("status") == "failed":
            raise ValueError("Cannot audit a failed Bronze run")
        run_evidence.append({
            "run_id": manifest["run_id"], "source": manifest.get("source"),
            "status": manifest["status"], "market_scope": manifest.get("market_scope"),
            "rows": manifest["total_rows"], "manifest_sha256": manifest_sha,
            "sources": manifest.get("sources", []),
        })
        for path in files:
            for row in json.loads(Path(path).read_text(encoding="utf-8")):
                raw_rows += 1
                source, source_id = row.get("source"), row.get("source_record_id")
                if not source or not source_id:
                    invalid_identity_rows += 1
                    continue
                key = (str(source), str(source_id))
                if key in selected:
                    duplicate_rows += 1
                selected[key] = row

    grouped = Counter()
    source_months = Counter()
    occupation_counts = Counter()
    invalid_posted_at_rows = other_year_rows = 0
    sources = set()
    title_mapping = load_dictionaries()[0]
    for row in selected.values():
        source = str(row["source"])
        sources.add(source)
        month = _month(row.get("posted_at"))
        if not month:
            invalid_posted_at_rows += 1
            continue
        if not month.startswith("2026-"):
            other_year_rows += 1
            continue
        occupation = normalize_title(row.get("title"), title_mapping)
        market = row.get("market") or "UNSPECIFIED"
        grouped[(source, market, month, occupation)] += 1
        source_months[(source, market, month)] += 1
        occupation_counts[(source, market, occupation)] += 1

    calendar = [f"2026-{month:02d}" for month in range(1, last_month + 1)]
    federal_windows = sorted((
        (date.fromisoformat(source_result["start_date"]),
         date.fromisoformat(source_result["end_date"]),
         evidence["status"] == "complete" and source_result.get("coverage") == "complete")
        for evidence in run_evidence if evidence["source"] == "usajobs_historic"
        for source_result in evidence["sources"] if source_result["source"] == "usajobs_historic"
    ), key=lambda item: item[0])
    federal_seams = [
        {"previous_end": left[1].isoformat(), "next_start": right[0].isoformat(),
         "kind": "gap" if right[0] > left[1] + timedelta(days=1) else "overlap"}
        for left, right in zip(federal_windows, federal_windows[1:])
        if right[0] != left[1] + timedelta(days=1)
    ]
    return {
        "audit_kind": "2026_bronze_source_occupation_month",
        "taxonomy_version": TAXONOMY_VERSION,
        "through_month": through_month,
        "input_runs": run_evidence,
        "raw_rows": raw_rows,
        "unique_source_records": len(selected),
        "duplicate_source_records_removed": duplicate_rows,
        "invalid_identity_rows": invalid_identity_rows,
        "invalid_posted_at_rows": invalid_posted_at_rows,
        "other_year_rows": other_year_rows,
        "us_federal_window_coverage": {
            "window_count": len(federal_windows),
            "first_date": federal_windows[0][0].isoformat() if federal_windows else None,
            "last_date": federal_windows[-1][1].isoformat() if federal_windows else None,
            "all_windows_complete": bool(federal_windows) and all(item[2] for item in federal_windows),
            "seams": federal_seams,
        },
        "title_classification": {
            "classified_occupation_jobs": sum(count for (_, _, occupation), count in occupation_counts.items()
                                              if occupation != "Other IT"),
            "unclassified_title_jobs": sum(count for (_, _, occupation), count in occupation_counts.items()
                                           if occupation == "Other IT"),
            "note": "Other IT means taxonomy v0.1 did not match a title; it does not prove the job is IT.",
        },
        "source_occupation_counts": [
            {"source": source, "market": market, "occupation": occupation, "jobs": count}
            for (source, market, occupation), count in sorted(occupation_counts.items())
        ],
        "source_month_counts": [
            {"source": source, "market": market, "month": month, "jobs": count}
            for (source, market, month), count in sorted(source_months.items())
        ],
        "source_occupation_month_counts": [
            {"source": source, "market": market, "month": month,
             "occupation": occupation, "jobs": count}
            for (source, market, month, occupation), count in sorted(grouped.items())
        ],
        "months_without_observed_postings": {
            source: [month for month in calendar if not any(
                s == source and m == month for s, _, m in source_months
            )] for source in sorted(sources)
        },
        "interpretation": "Unobserved months are gaps in source coverage, not zero hiring demand. "
                          "US_FEDERAL and GLOBAL are separate markets; active-job snapshots are not historical backfill.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", help="Explicit immutable Bronze run directories")
    parser.add_argument("--through-month", required=True, help="YYYY-MM in 2026")
    parser.add_argument("--output", required=True, help="Audit JSON output path")
    args = parser.parse_args()
    audit = audit_runs(args.run_dirs, args.through_month)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[2026 Bronze audit] {audit['unique_source_records']} unique records; {output}")
