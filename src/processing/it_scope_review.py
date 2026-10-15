"""Create a deterministic, unlabelled human review sample from pinned Bronze 2026."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from src.common.run_manifest import sha256_file
from src.common.taxonomy import load_dictionaries, normalize_title
from src.processing.input_selection import ROOT, load_input_selection


SAMPLE_SIZES = {"arbeitnow": 40, "usajobs_historic": 40}
FIELDS = (
    "sample_key", "source", "market", "source_record_id", "title", "company",
    "location", "taxonomy_label", "current_scope", "source_url",
    "input_run_id", "input_manifest_sha256", "manual_label", "in_scope_it",
    "review_reason",
)


def _hash_key(source, source_record_id):
    return hashlib.sha256(f"{source}\0{source_record_id}".encode("utf-8")).hexdigest()


def build_sample(selection_path, selection_sha256, output_path, workspace_root=ROOT):
    selected_runs, _ = load_input_selection(
        selection_path, selection_sha256, workspace_root=workspace_root,
    )
    # One source identity is one job. Prefer the complete observation so the
    # partial Arbeitnow snapshot never contributes a unique sample record.
    unique = {}
    for run in selected_runs:
        for file in run["files"]:
            for row in json.loads(Path(file).read_text(encoding="utf-8")):
                source = str(row.get("source") or "")
                source_id = str(row.get("source_record_id") or "")
                if not source or not source_id:
                    raise ValueError("Cannot sample a Bronze row without a source identity")
                key = (source, source_id)
                candidate = (int(run["status"] == "complete"),
                             str(row.get("collected_at") or ""),
                             str(row.get("raw_checksum") or ""), run["run_id"])
                if key not in unique or candidate > unique[key][0]:
                    unique[key] = (candidate, row, run)

    mapping = load_dictionaries()[0]
    groups = {}
    for (source, source_id), (_, row, run) in unique.items():
        taxonomy = normalize_title(row.get("title"), mapping)
        mapped = taxonomy != "Other IT"
        groups.setdefault((source, "mapped" if mapped else "Other IT"), []).append({
            "sample_key": _hash_key(source, source_id)[:16],
            "source": source, "market": row.get("market") or "GLOBAL",
            "source_record_id": source_id, "title": row.get("title") or "",
            "company": row.get("company") or "", "location": row.get("location") or "",
            "taxonomy_label": taxonomy,
            "current_scope": ("source_series_2210" if source == "usajobs_historic"
                              else "candidate_mapped_title" if mapped else "candidate_excluded_title"),
            "source_url": row.get("source_url") or "",
            "input_run_id": run["run_id"],
            "input_manifest_sha256": run["manifest_sha256"],
            "manual_label": "", "in_scope_it": "", "review_reason": "",
        })
    sample = []
    for (source, group), rows in sorted(groups.items()):
        ordered = sorted(rows, key=lambda row: (row["sample_key"], row["source_record_id"]))
        size = len(ordered) if source == "remotive" else SAMPLE_SIZES.get(source, 0)
        sample.extend(ordered[:size])
    if len([row for row in sample if row["source"] == "remotive"]) != 15:
        raise AssertionError("The human review sample must include all 15 Remotive records")
    for source in ("arbeitnow", "usajobs_historic"):
        has_other = any(row["source"] == source and row["taxonomy_label"] == "Other IT" for row in sample)
        has_mapped = any(row["source"] == source and row["taxonomy_label"] != "Other IT" for row in sample)
        if not (has_other and has_mapped):
            raise AssertionError(f"Both taxonomy classes must be sampled for {source}")
    output = Path(output_path).resolve()
    if not output.is_relative_to(Path(workspace_root).resolve()):
        raise ValueError("Review sample must be written inside the workspace")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite a possibly labelled sample: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sample)
    counts = Counter((row["source"], "mapped" if row["taxonomy_label"] != "Other IT" else "Other IT")
                     for row in sample)
    report = {
        "status": "pending_manual_review",
        "selection_sha256": selection_sha256,
        "sample_path": output.relative_to(Path(workspace_root).resolve()).as_posix(),
        "sample_sha256": sha256_file(output),
        "sample_rows": len(sample),
        "sample_by_source_and_title_class": [
            {"source": source, "title_class": group, "rows": count}
            for (source, group), count in sorted(counts.items())
        ],
        "manual_columns_initially_blank": ["manual_label", "in_scope_it", "review_reason"],
        "sampling_method": "source ID dedup, complete-run preference, SHA-256 rank by source and source_record_id",
        "note": "This is an unlabelled spot-check sample; no precision, recall or F1 is claimed.",
    }
    manifest_path = output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-selection", required=True)
    parser.add_argument("--input-selection-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(build_sample(args.input_selection, args.input_selection_sha256, args.output),
                     ensure_ascii=False, indent=2))
