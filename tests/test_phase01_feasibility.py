"""Legacy filename: generate Phase 01 coverage diagnostics, not accuracy tests.

Historical source tags and fresh JD-derived skills are reported separately.
No aggregate metric is calculated across these different evidence types.
"""

import json
import hashlib
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.taxonomy import TAXONOMY_VERSION, extract_skills, load_dictionaries, normalize_source_tags, normalize_title

HIST_PATH = ROOT / "data" / "sample" / "historical" / "historical_sample_300.json"
FRESH_PATH = ROOT / "data" / "sample" / "fresh" / "fresh_sample.json"
OUTPUT_PATH = ROOT / "docs" / "data" / "phase01_sample_diagnostics.json"


def _read(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _sha256(path):
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _coverage(records, title_key, date_key):
    titles = Counter()
    months = Counter()
    mapped = 0
    for row in records:
        role = normalize_title(row.get(title_key))
        titles[role] += 1
        mapped += role != "Other IT"
        month = str(row.get(date_key) or "")[:7]
        months[month if len(month) == 7 else "unknown"] += 1
    total = len(records)
    return {
        "rows": total,
        "title_role_coverage_pct": round(mapped * 100 / total, 2) if total else None,
        "role_counts": dict(titles),
        "month_counts": dict(sorted(months.items())),
    }


def run_evaluation():
    historical = _read(HIST_PATH)
    fresh = _read(FRESH_PATH)
    _, skill_dictionary = load_dictionaries()

    historical_coverage = _coverage(historical, "job_title", "job_posted_date")
    hist_has_description = sum(bool(row.get("job_description")) for row in historical)
    hist_has_tags = sum(bool(row.get("job_skills")) for row in historical)
    hist_tags_normalized = sum(bool(normalize_source_tags(row.get("job_skills"), skill_dictionary)) for row in historical)

    fresh_coverage = _coverage(fresh, "title", "posted_at")
    fresh_has_description = sum(bool(row.get("description")) for row in fresh)
    fresh_with_extracted_skills = sum(bool(extract_skills(row.get("description"), skill_dictionary)) for row in fresh)
    source_counts = Counter(row.get("source", "unknown") for row in fresh)

    results = {
        "diagnostic_type": "coverage_not_accuracy",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "taxonomy_version": TAXONOMY_VERSION,
        "config_sha256": {
            "job_title_mapping_v0.json": _sha256(ROOT / "configs" / "job_title_mapping_v0.json"),
            "skills_v0.json": _sha256(ROOT / "configs" / "skills_v0.json"),
        },
        "inputs": {
            "historical": "data/sample/historical/historical_sample_300.json",
            "historical_sha256": _sha256(HIST_PATH),
            "fresh_snapshot": "data/sample/fresh/fresh_sample.json",
            "fresh_snapshot_sha256": _sha256(FRESH_PATH),
            "synthetic_fixtures_included": False,
        },
        "historical_archive_sample": {
            **historical_coverage,
            "description_rows": hist_has_description,
            "source_tag_rows": hist_has_tags,
            "rows_with_recognized_source_tags": hist_tags_normalized,
            "skill_extraction_accuracy": None,
            "accuracy_reason": "Archive has source tags but no job descriptions or independently labeled truth.",
        },
        "fresh_saved_snapshot": {
            **fresh_coverage,
            "source_counts": dict(source_counts),
            "description_rows": fresh_has_description,
            "rows_with_rule_matched_skills": fresh_with_extracted_skills,
            "skill_extraction_accuracy": None,
            "accuracy_reason": "No independently labeled evaluation set is available.",
        },
        "combined_time_series": None,
        "combined_time_series_reason": "Historical archive and fresh snapshots differ in source and coverage; do not treat their gap as observed zero demand or a continuous series.",
    }
    OUTPUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote coverage diagnostics to {OUTPUT_PATH}")
    return results


if __name__ == "__main__":
    run_evaluation()
