"""Prepare independent JD labels and evaluate the frozen v0.1 taxonomy."""

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from src.common.run_manifest import load_bronze_run
from src.common.taxonomy import extract_skills, load_dictionaries, normalize_title


ROOT = Path(__file__).resolve().parents[2]
FIELDS = ["source", "source_record_id", "market", "posted_at", "title", "description",
          "predicted_occupation", "predicted_skills", "is_it", "gold_occupation",
          "gold_skills", "annotator", "annotation_notes"]


def _run_path(source, run_id):
    market = "us_federal/historic" if source == "usajobs_historic" else "global/fresh"
    return ROOT / "data/bronze" / market / "runs" / run_id


def prepare_sample(audit_path, output_path, per_stratum=20, seed=42):
    """Sample matched and unmatched titles per source; keep raw JD local."""
    audit = json.loads(Path(audit_path).read_text(encoding="utf-8"))
    if audit.get("audit_kind") != "2026_bronze_source_occupation_month":
        raise ValueError("Expected the verified 2026 Bronze audit")
    records = {}
    for run in audit["input_runs"]:
        path = _run_path(run["source"], run["run_id"])
        _, files, checksum = load_bronze_run(path, expected_kind="fresh", allow_partial=True)
        if checksum != run["manifest_sha256"]:
            raise ValueError(f"Bronze manifest changed: {run['run_id']}")
        for file in files:
            for row in json.loads(Path(file).read_text(encoding="utf-8")):
                records[(row["source"], str(row["source_record_id"]))] = row
    if len(records) != audit["unique_source_records"]:
        raise ValueError("Bronze identity count differs from audit")
    title_mapping, skill_dictionary = load_dictionaries()
    groups = defaultdict(list)
    for row in records.values():
        prediction = normalize_title(row.get("title"), title_mapping)
        group = (row["source"], "unmatched" if prediction == "Other IT" else "matched")
        groups[group].append({
            "source": row["source"], "source_record_id": str(row["source_record_id"]),
            "market": row.get("market") or "", "posted_at": row.get("posted_at") or "",
            "title": row.get("title") or "", "description": row.get("description") or "",
            "predicted_occupation": prediction,
            "predicted_skills": "",
            "is_it": "", "gold_occupation": "", "gold_skills": "",
            "annotator": "", "annotation_notes": "",
        })
    rng = random.Random(seed)
    sampled = []
    for group in sorted(groups):
        values = sorted(groups[group], key=lambda row: row["source_record_id"])
        sampled.extend(rng.sample(values, min(per_stratum, len(values))))
    for row in sampled:
        row["predicted_skills"] = ";".join(extract_skills(row["description"], skill_dictionary))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sampled)
    return {"output": str(output), "rows": len(sampled),
            "strata": {f"{source}/{kind}": min(per_stratum, len(values))
                       for (source, kind), values in sorted(groups.items())}}


def _scores(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = None if tp + fp + fn == 0 else (
        2 * tp / (2 * tp + fp + fn) if tp else 0.0
    )
    return {"precision": precision, "recall": recall,
            "f1": f1,
            "tp": tp, "fp": fp, "fn": fn}


def evaluate_labels(path):
    """Only rows with a named annotator count as independent labels."""
    rows = list(csv.DictReader(Path(path).open(encoding="utf-8-sig", newline="")))
    taxonomy, skills = load_dictionaries()
    allowed_skills = set(skills)
    source_groups = defaultdict(list)
    for row in rows:
        if not row.get("annotator", "").strip():
            continue
        source_groups[row["source"]].append(row)
    results = {}
    for source, group in sorted(source_groups.items()):
        in_scope = []
        skill_counts = Counter()
        for row in group:
            if row["is_it"] not in {"0", "1"}:
                raise ValueError(f"is_it must be 0 or 1: {source}/{row['source_record_id']}")
            if row["is_it"] == "0":
                if row["gold_occupation"] not in {"", "Out of scope"}:
                    raise ValueError("Out-of-scope row must not carry an IT occupation")
                continue
            if row["gold_occupation"] not in set(taxonomy) | {"Other IT"}:
                raise ValueError(f"Invalid gold occupation: {row['gold_occupation']}")
            in_scope.append(row)
            if row["description"].strip():
                gold = {item.strip() for item in row["gold_skills"].split(";") if item.strip()}
                predicted = {item.strip() for item in row["predicted_skills"].split(";") if item.strip()}
                if not gold <= allowed_skills or not predicted <= allowed_skills:
                    raise ValueError("Unknown skill ID in label file")
                skill_counts["jd_rows"] += 1
                skill_counts["tp"] += len(gold & predicted)
                skill_counts["fp"] += len(predicted - gold)
                skill_counts["fn"] += len(gold - predicted)
        classes = sorted(set(taxonomy) | {"Other IT"})
        per_class = {}
        for label in classes:
            tp = sum(row["predicted_occupation"] == label == row["gold_occupation"] for row in in_scope)
            fp = sum(row["predicted_occupation"] == label and row["gold_occupation"] != label for row in in_scope)
            fn = sum(row["predicted_occupation"] != label and row["gold_occupation"] == label for row in in_scope)
            per_class[label] = _scores(tp, fp, fn)
        defined_f1 = [score["f1"] for score in per_class.values() if score["f1"] is not None]
        results[source] = {
            "labeled_rows": len(group), "in_scope_it_rows": len(in_scope),
            "out_of_scope_rows": len(group) - len(in_scope),
            "title_coverage": sum(row["predicted_occupation"] != "Other IT" for row in in_scope) / len(in_scope)
                              if in_scope else None,
            "occupation_accuracy": sum(row["predicted_occupation"] == row["gold_occupation"]
                                       for row in in_scope) / len(in_scope) if in_scope else None,
            "occupation_macro_f1": sum(defined_f1) / len(defined_f1) if defined_f1 else None,
            "occupation_per_class": per_class,
            "skill_jd_rows": skill_counts["jd_rows"],
            "skill_micro": _scores(skill_counts["tp"], skill_counts["fp"], skill_counts["fn"])
                           if skill_counts["jd_rows"] else None,
        }
    return {"sample_rows": len(rows), "labeled_rows": sum(len(group) for group in source_groups.values()),
            "status": "evaluated" if source_groups else "awaiting_independent_labels", "sources": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sample = sub.add_parser("sample")
    sample.add_argument("--audit", default=str(ROOT / "docs/data/2026_ingestion_audit.json"))
    sample.add_argument("--output", required=True)
    sample.add_argument("--per-stratum", type=int, default=20)
    sample.add_argument("--seed", type=int, default=42)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--labels", required=True)
    evaluate.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "sample":
        result = prepare_sample(args.audit, args.output, args.per_stratum, args.seed)
    else:
        result = evaluate_labels(args.labels)
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
