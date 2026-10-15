"""Fail-closed preflight for pinned 2026 Bronze inputs and IT scope policy."""

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common.run_manifest import sha256_file, utc_now
from src.processing.input_selection import PARTIAL_RUN_ID, load_input_selection
from src.processing.scope_policy_2026 import (
    POLICY_PATH, classify_scope, load_scope_policy,
)

SELECTION = ROOT / "docs/data/2026_silver_input_selection.json"
SAMPLE = ROOT / "docs/data/2026_it_scope_sample.csv"
OUT_JSON = ROOT / "docs/data/2026_scope_policy_preflight.json"
OUT_MD = ROOT / "docs/reviews/2026_SCOPE_POLICY_PREFLIGHT_2026-10-15.md"
EXPECTED = {"input_rows": 21435, "unique_rows": 19706, "duplicate_rows": 1729,
            "quarantine_rows": 0}
EXPECTED_SOURCE = {"arbeitnow": 12952, "remotive": 15, "usajobs_historic": 6739}


def _parsed_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(
            tzinfo=timezone.utc) if len(str(value)) == 10 else datetime.fromisoformat(
                str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _sample_gate(policy):
    if sha256_file(SAMPLE) != policy["ai_review_sample_sha256"]:
        raise AssertionError("AI review sample SHA differs from pinned policy")
    with SAMPLE.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 175:
        raise AssertionError("AI review sample must have 175 rows")
    decisions = Counter()
    mismatches = []
    for row in rows:
        actual = classify_scope(row["title"], row["source"], row["market"],
                                policy=policy,
                                federal_series_2210_verified=row["source"] == "usajobs_historic")
        value = {"in_scope": "1", "excluded": "0", "unresolved": ""}[actual["scope_decision"]]
        decisions[actual["scope_decision"]] += 1
        if value != row["in_scope_it"] or actual["scope_label"] != row["manual_label"]:
            mismatches.append(row["sample_key"])
    if mismatches or decisions != {"in_scope": 142, "excluded": 27, "unresolved": 6}:
        raise AssertionError(f"AI review regression failed: {decisions}, {mismatches[:10]}")
    return dict(decisions)


def audit():
    policy = load_scope_policy()
    sample_counts = _sample_gate(policy)
    selected, _ = load_input_selection(SELECTION, sha256_file(SELECTION))
    by_id = defaultdict(list)
    source_rows = Counter()
    invalid = []
    for run in selected:
        for file in run["files"]:
            for row in json.loads(Path(file).read_text(encoding="utf-8")):
                source_rows[row.get("source")] += 1
                key = (row.get("source"), str(row.get("source_record_id")))
                posted = _parsed_date(row.get("posted_at"))
                if (not row.get("source") or not row.get("source_record_id") or
                        not str(row.get("title") or "").strip() or posted is None):
                    invalid.append({"run_id": run["run_id"], "source_record_id": row.get("source_record_id")})
                    continue
                by_id[key].append((run, row, posted))
    input_rows = sum(source_rows.values())
    valid_rows = input_rows - len(invalid)
    unique_rows = len(by_id)
    duplicates = valid_rows - unique_rows
    counts = Counter()
    rules = Counter()
    occupations = Counter()
    months = Counter()
    unresolved_titles = Counter()
    partial_winners = Counter()
    multi_run_lineage = 0
    for records in by_id.values():
        # The audited complete snapshot supersedes the pinned partial snapshot;
        # other repeated source IDs retain the latest collected observation.
        records.sort(key=lambda item: (
            item[0]["status"] == "complete", str(item[1].get("collected_at") or ""),
            str(item[1].get("raw_checksum") or "")), reverse=True)
        run, row, posted = records[0]
        if len({item[0]["run_id"] for item in records}) > 1:
            multi_run_lineage += 1
        if run["run_id"] == PARTIAL_RUN_ID:
            partial_winners[row["source"]] += 1
        classified = classify_scope(row["title"], row["source"], row["market"],
                                    policy=policy,
                                    federal_series_2210_verified=run["source"] == "usajobs_historic"
                                    and run["market_scope"] == "US federal jobs")
        source, market, decision = row["source"], row["market"], classified["scope_decision"]
        counts[(source, market, decision)] += 1
        rules[(source, classified["analysis_scope_basis"])] += 1
        if decision == "in_scope":
            occupations[(source, market, classified["normalized_title"])] += 1
            months[(source, market, posted.strftime("%Y-%m"))] += 1
        elif decision == "unresolved":
            unresolved_titles[(source, row["title"])] += 1
    by_source = Counter()
    for (source, _, _), count in counts.items():
        by_source[source] += count
    observed = {"input_rows": input_rows, "unique_rows": unique_rows,
                "duplicate_rows": duplicates, "quarantine_rows": len(invalid)}
    failures = []
    for key, expected in EXPECTED.items():
        if observed[key] != expected:
            failures.append(f"{key}: {observed[key]} != {expected}")
    if dict(by_source) != EXPECTED_SOURCE:
        failures.append(f"Source unique totals: {dict(by_source)} != {EXPECTED_SOURCE}")
    for (source, _, decision), count in counts.items():
        if source == "usajobs_historic" and decision != "in_scope":
            failures.append("USAJOBS must all be in scope")
    remotive = {decision: counts.get(("remotive", "GLOBAL", decision), 0)
                for decision in ("in_scope", "excluded", "unresolved")}
    if remotive != {"in_scope": 10, "excluded": 5, "unresolved": 0}:
        failures.append(f"Remotive scope mismatch: {remotive}")
    if dict(partial_winners) != {"remotive": 15}:
        failures.append(f"Partial survivor contribution mismatch: {dict(partial_winners)}")
    if input_rows != valid_rows + len(invalid) or valid_rows != unique_rows + duplicates:
        failures.append("Preflight row accounting failed")
    if sum(counts.values()) != unique_rows:
        failures.append("Scope decision accounting failed")
    def table(counter, names):
        return [dict(zip(names, key), rows=value) for key, value in sorted(counter.items())]
    result = {
        "status": "passed" if not failures else "failed", "created_at": utc_now(),
        "input_selection_sha256": sha256_file(SELECTION),
        "scope_policy_sha256": sha256_file(POLICY_PATH),
        "taxonomy_config_sha256": sha256_file(ROOT / "configs/job_title_mapping_v0_2.json"),
        "sample_sha256": sha256_file(SAMPLE), "sample_agreement_counts": sample_counts,
        "input_run_count": len(selected), "metrics": {**observed, "valid_rows": valid_rows,
            "silver_rows": sum(value for (source, market, decision), value in counts.items() if decision == "in_scope"),
            "scope_excluded_rows": sum(value for (source, market, decision), value in counts.items() if decision == "excluded"),
            "scope_unresolved_rows": sum(value for (source, market, decision), value in counts.items() if decision == "unresolved"),
            "multi_run_lineage_ids": multi_run_lineage,
            "partial_winners": dict(partial_winners)},
        "source_market_decision": table(counts, ["source", "market", "scope_decision"]),
        "source_rule": table(rules, ["source", "analysis_scope_basis"]),
        "source_market_occupation": table(occupations, ["source", "market", "occupation"]),
        "source_market_month": table(months, ["source", "market", "month"]),
        "top_unresolved_titles": [dict(source=s, title=t, rows=n)
                                  for (s, t), n in unresolved_titles.most_common(30)],
        "failures": failures,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Preflight phạm vi IT 2026", "",
             f"- Gate: **{result['status'].upper()}**", "- Nguồn: 23 Bronze run đã pin SHA; mẫu AI review 175 dòng.",
             f"- Input: {input_rows:,}; valid: {valid_rows:,}; quarantine: {len(invalid):,}; duplicate: {duplicates:,}; unique: {unique_rows:,}.",
             f"- Silver dự kiến: {result['metrics']['silver_rows']:,}; ngoài IT: {result['metrics']['scope_excluded_rows']:,}; chưa xác định: {result['metrics']['scope_unresolved_rows']:,}.",
             "", "## Source × market × quyết định", "",
             "| Source | Market | Quyết định | Rows |", "|---|---|---|---:|"]
    lines += [f"| {r['source']} | {r['market']} | {r['scope_decision']} | {r['rows']:,} |"
              for r in result["source_market_decision"]]
    lines += ["", "## Nghề trong Silver dự kiến", "",
              "| Source | Market | Nghề | Rows |", "|---|---|---|---:|"]
    lines += [f"| {r['source']} | {r['market']} | {r['occupation']} | {r['rows']:,} |"
              for r in result["source_market_occupation"]]
    lines += ["", "## Tháng quan sát", "",
              "| Source | Market | Tháng | Rows |", "|---|---|---|---:|"]
    lines += [f"| {r['source']} | {r['market']} | {r['month']} | {r['rows']:,} |"
              for r in result["source_market_month"]]
    lines += ["", "## Tiêu đề chưa xác định thường gặp", "",
              "| Source | Title | Rows |", "|---|---|---:|"]
    for item in result["top_unresolved_titles"][:15]:
        title = item["title"].replace("|", "\\|")
        lines.append(f"| {item['source']} | {title} | {item['rows']:,} |")
    lines += ["", "## Rule được kích hoạt", "",
              "| Source | Rule ID | Rows |", "|---|---|---:|"]
    lines += [f"| {r['source']} | {r['analysis_scope_basis']} | {r['rows']:,} |"
              for r in result["source_rule"]]
    lines += ["", "## Gate và giới hạn", "",
              "Các nhãn mẫu là AI-assisted, không phải human ground truth; số khớp mẫu không phải precision/recall/F1.",
              "Tháng không quan sát không được zero-fill. GLOBAL và US_FEDERAL có mẫu số riêng.",
              "Forecast gate vẫn NO_GO. Preflight chỉ đọc Bronze, chưa xuất bản Silver."]
    if failures:
        lines += ["", "## Lỗi gate", ""] + [f"- {x}" for x in failures]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failures:
        raise AssertionError("Preflight failed: " + "; ".join(failures))
    return result


if __name__ == "__main__":
    report = audit()
    print(json.dumps({"status": report["status"], "metrics": report["metrics"],
                      "source_market_decision": report["source_market_decision"]},
                     ensure_ascii=False, indent=2))
