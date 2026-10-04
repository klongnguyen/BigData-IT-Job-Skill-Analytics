"""Generate a profile for the real archive sample and the saved fresh snapshot."""

import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.common.taxonomy import normalize_source_tags

ROOT = Path(__file__).resolve().parents[2]
HIST = ROOT / "data" / "sample" / "historical" / "historical_sample_300.json"
FRESH = ROOT / "data" / "sample" / "fresh" / "fresh_sample.json"
AUDIT = ROOT / "docs" / "data" / "phase01_data_audit.json"
OUTPUT = ROOT / "docs" / "data" / "data_profile.md"


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _profile(records, title_key, company_key, date_key, description_key, source_key=None):
    total = len(records)
    dates = [str(row.get(date_key) or "") for row in records]
    months = Counter(value[:7] or "unknown" for value in dates)
    candidates = [
        f"{str(row.get(title_key) or '').strip().casefold()}|{str(row.get(company_key) or '').strip().casefold()}"
        for row in records
    ]
    duplicate_candidates = len(candidates) - len(set(candidates))
    descriptions = [len(str(row.get(description_key) or "")) for row in records if row.get(description_key)]
    tag_key = "job_skills" if title_key == "job_title" else "tags"
    tags_present = sum(bool(normalize_source_tags(row.get(tag_key))) for row in records)
    sources = Counter(row.get(source_key, "unknown") for row in records) if source_key else Counter()
    return {
        "rows": total,
        "months": months,
        "date_min": min((value for value in dates if value), default="n/a"),
        "date_max": max((value for value in dates if value), default="n/a"),
        "candidate_duplicate_count": duplicate_candidates,
        "description_rows": len(descriptions),
        "description_mean": round(statistics.mean(descriptions), 1) if descriptions else None,
        "tag_rows": tags_present,
        "sources": sources,
        "columns": sorted({key for row in records for key in row}),
    }


def main():
    historical = _read(HIST)
    fresh = _read(FRESH) if FRESH.exists() else []
    manifest = _read(AUDIT) if AUDIT.exists() else {}
    hist = _profile(historical, "job_title", "company_name", "job_posted_date", "job_description")
    new = _profile(fresh, "title", "company", "posted_at", "description", "source")
    lines = [
        "# Data Profile — Phase 01",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Taxonomy version: `{manifest.get('taxonomy_version', 'unknown')}`",
        f"Raw archive SHA-256: `{manifest.get('historical_archive', {}).get('sha256', 'not audited')}`",
        "",
        "> This profile distinguishes the real 2023 archive sample from the saved fresh snapshot. Synthetic fixtures are excluded. Coverage/count metrics are not extraction accuracy.",
        "",
        "## Sample summary",
        "",
        "| Measure | Historical archive sample | Saved fresh snapshot |",
        "|---|---:|---:|",
        f"| Rows | {hist['rows']} | {new['rows']} |",
        f"| Date range | {hist['date_min']} to {hist['date_max']} | {new['date_min']} to {new['date_max']} |",
        f"| Observed months | {len(hist['months'])} | {len(new['months'])} |",
        f"| Rows with source skill tags | {hist['tag_rows']} | {new['tag_rows']} |",
        f"| Rows with original description | {hist['description_rows']} | {new['description_rows']} |",
        f"| Mean description length (available rows only) | {hist['description_mean'] if hist['description_mean'] is not None else 'N/A — archive has no JD'} | {new['description_mean'] if new['description_mean'] is not None else 'N/A'} |",
        f"| Candidate duplicate pairs (same title + company heuristic) | {hist['candidate_duplicate_count']} | {new['candidate_duplicate_count']} |",
        "",
        "## Historical sample by month",
        "",
        "| Month | Rows |",
        "|---|---:|",
    ]
    lines.extend(f"| {month} | {count} |" for month, count in sorted(hist["months"].items()))
    lines += ["", "## Fresh snapshot by source and month", "", "Sources: " + (", ".join(f"{key}: {value}" for key, value in sorted(new["sources"].items())) or "none"), "", "| Month | Rows |", "|---|---:|"]
    lines.extend(f"| {month} | {count} |" for month, count in sorted(new["months"].items()))
    lines += [
        "",
        "## Interpretation and limitations",
        "",
        "- The historical sample is drawn from the checked-in archive and covers 2023 only. The archive has `job_skills` source tags but no `job_description`; these records cannot evaluate extraction from JD text.",
        "- The fresh data is a saved snapshot, not evidence of current API availability or a continuous time series.",
        "- Title/company duplicates are candidates for review, not exact deduplication counts.",
        "- Source-tag presence and rule-based skill coverage measure availability/coverage only. Precision, recall and accuracy require independent labels.",
        "- A missing month means no observation in that sample/source; it must not be interpreted as zero market demand.",
        "- Synthetic demo fixtures under `data/fixtures/synthetic/` are excluded from this report and all feasibility decisions.",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote profile to {OUTPUT}")


if __name__ == "__main__":
    main()
