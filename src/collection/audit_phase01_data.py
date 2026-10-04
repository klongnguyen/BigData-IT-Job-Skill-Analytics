"""Read-only, reproducible audit of the historical archive and saved fresh snapshot."""

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.common.taxonomy import TAXONOMY_VERSION, load_dictionaries, normalize_title

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "data_jobs.csv"
FRESH = ROOT / "data" / "sample" / "fresh" / "fresh_sample.json"
HIST_SAMPLE = ROOT / "data" / "sample" / "historical" / "historical_sample_300.json"
OUTPUT = ROOT / "docs" / "data" / "phase01_data_audit.json"


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_historical(path=RAW):
    title_mapping, _ = load_dictionaries()
    total = 0
    months = Counter()
    titles_by_month = Counter()
    source_tag_present = 0
    timestamp_missing = 0
    field_present = Counter()
    fields = None
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        for record in reader:
            total += 1
            for name, value in record.items():
                if value is not None and str(value).strip():
                    field_present[name] += 1
            posted = (record.get("job_posted_date") or "").strip()
            if not posted:
                timestamp_missing += 1
                month = "unknown"
            else:
                month = posted[:7]
            months[month] += 1
            titles_by_month[(record.get("job_title") or "", month)] += 1
            raw_skills = (record.get("job_skills") or "").strip()
            source_tag_present += bool(raw_skills and raw_skills not in ("[]", "null", "None"))
    roles_by_month = Counter()
    for (title, month), count in titles_by_month.items():
        roles_by_month[(normalize_title(title, title_mapping), month)] += count
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha256_file(path),
        "row_count": total,
        "columns": fields,
        "has_job_description": "job_description" in fields,
        "date_range": {"first_month": min((m for m in months if m != "unknown"), default=None), "last_month": max((m for m in months if m != "unknown"), default=None)},
        "month_counts": dict(sorted(months.items())),
        "occupation_month_counts": {f"{role}|{month}": count for (role, month), count in sorted(roles_by_month.items())},
        "missing_posted_at_count": timestamp_missing,
        "source_tags_present_count": source_tag_present,
        "field_nonempty_counts": dict(sorted(field_present.items())),
    }


def audit_fresh(path=FRESH):
    if not path.exists():
        return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "available": False}
    records = json.loads(path.read_text(encoding="utf-8"))
    months = Counter(str(row.get("posted_at") or "")[:7] or "unknown" for row in records)
    sources = Counter(row.get("source", "unknown") for row in records)
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha256_file(path),
        "available": True,
        "row_count": len(records),
        "month_counts": dict(sorted(months.items())),
        "source_counts": dict(sorted(sources.items())),
        "date_range": {
            "first": min((row.get("posted_at") for row in records if row.get("posted_at")), default=None),
            "last": max((row.get("posted_at") for row in records if row.get("posted_at")), default=None),
        },
    }


def build_audit():
    raw = audit_historical()
    fresh = audit_fresh()
    title_config = ROOT / "configs" / "job_title_mapping_v0.json"
    skill_config = ROOT / "configs" / "skills_v0.json"
    sample = json.loads(HIST_SAMPLE.read_text(encoding="utf-8")) if HIST_SAMPLE.exists() else []
    sample_month_counts = Counter(str(row.get("job_posted_date") or "")[:7] or "unknown" for row in sample)
    return {
        "audit_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "taxonomy_version": TAXONOMY_VERSION,
        "config_sha256": {
            "job_title_mapping_v0.json": sha256_file(title_config),
            "skills_v0.json": sha256_file(skill_config),
        },
        "synthetic_data_included": False,
        "historical_archive": raw,
        "historical_sample": {
            "path": str(HIST_SAMPLE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(HIST_SAMPLE) if HIST_SAMPLE.exists() else None,
            "row_count": len(sample),
            "selection": "deterministic reservoir sample, 25 rows per month in 2023, seed=42",
            "month_counts": dict(sorted(sample_month_counts.items())),
        },
        "fresh_saved_snapshot": fresh,
        "decision": {
            "prototype": "GO",
            "descriptive_analytics": "CONDITIONAL_GO",
            "predictive_claims": "NO_GO",
            "reason": "Current historical archive covers 2023 only and has no job-description column; saved fresh data is a limited snapshot.",
        },
    }


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(build_audit(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote data audit to {OUTPUT}")
