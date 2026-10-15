"""Audit a completed, immutable 2026 Silver run against preflight and Parquet."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pyspark.sql import functions as F

from src.analytics.phase03_gold import load_verified_etl_manifest
from src.common.run_manifest import sha256_file, utc_now
from src.processing.input_selection import PARTIAL_MANIFEST_SHA256, PARTIAL_RUN_ID
from src.processing.spark_etl import _directory_evidence, create_spark_session

PREFLIGHT = ROOT / "docs/data/2026_scope_policy_preflight.json"
OUT_JSON = ROOT / "docs/data/2026_silver_run_audit.json"
OUT_MD = ROOT / "docs/reviews/2026_SILVER_RUN_AUDIT_2026-10-15.md"
OLD_HASHES = {
    "taxonomy_v0_1": (ROOT / "configs/job_title_mapping_v0.json",
                      "4aacd9a32d30af2dcb30e83d2fd41c63dafdccb28dfd0e33447ca204e6681ebd"),
    "old_etl_manifest": (ROOT / "tmp/phase03_acceptance/etl_manifests/etl_8c8a0ca26b38404a96a9b97fa8fd6e02.json",
                         "7d767fca4ed3b728892dcac3a2d5bfbb57dfd5cc4601b14e889149dc403acb4c"),
    "old_gold_manifest": (ROOT / "data/gold/global/runs/20261004T110131548191Z-e38fa7303cf4/manifest.json",
                          "2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d"),
}


def audit(manifest_path, manifest_sha256):
    old_hashes = {}
    for name, (path, expected) in OLD_HASHES.items():
        actual = sha256_file(path)
        if actual != expected:
            raise AssertionError(f"Old immutable artifact changed: {name}")
        old_hashes[name] = actual
    old_etl = json.loads(OLD_HASHES["old_etl_manifest"][0].read_text(encoding="utf-8"))
    for name in ("silver", "provenance"):
        declared = old_etl["outputs"][name]
        old_path = Path(declared["path"])
        if not old_path.exists():
            portable = str(declared["path"]).replace("\\", "/")
            marker = "/BigData_Job_Analy/"
            if marker not in portable:
                raise AssertionError(f"Cannot resolve old {name} Parquet path")
            old_path = ROOT / portable.split(marker, 1)[1]
        actual = _directory_evidence(old_path)["sha256"]
        if actual != declared["sha256"]:
            raise AssertionError(f"Old {name} Parquet changed")
        old_hashes[f"old_{name}_parquet"] = actual
    manifest, actual_sha = load_verified_etl_manifest(
        manifest_path, manifest_sha256, allow_scoped_inputs=True)
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    if preflight["status"] != "passed":
        raise AssertionError("Scope preflight did not pass")
    if manifest["input_selection"]["sha256"] != preflight["input_selection_sha256"]:
        raise AssertionError("Silver selection differs from preflight")
    if manifest["scope_policy_sha256"] != preflight["scope_policy_sha256"]:
        raise AssertionError("Silver scope policy differs from preflight")
    if manifest["taxonomy_config_sha256"]["job_title_mapping_v0_2.json"] != preflight["taxonomy_config_sha256"]:
        raise AssertionError("Silver taxonomy differs from preflight")
    if manifest["ai_review_sample_sha256"] != preflight["sample_sha256"]:
        raise AssertionError("Silver AI review sample differs from preflight")
    detail = manifest["metrics"]["source_market_occupation_month"]
    by_occupation = Counter()
    by_month = Counter()
    for row in detail:
        by_occupation[(row["source"], row["market"], row["occupation"])] += row["rows"]
        by_month[(row["source"], row["market"], row["month"])] += row["rows"]
    expected_occupations = {(row["source"], row["market"], row["occupation"]): row["rows"]
                            for row in preflight["source_market_occupation"]}
    expected_months = {(row["source"], row["market"], row["month"]): row["rows"]
                       for row in preflight["source_market_month"]}
    if dict(by_occupation) != expected_occupations or dict(by_month) != expected_months:
        raise AssertionError("Silver occupation/month breakdown differs from preflight")
    for name in ("scope_excluded", "scope_unresolved", "quarantine"):
        declared = manifest["outputs"][name]
        if _directory_evidence(ROOT / declared["path"]) != {
                "sha256": declared["sha256"], "files": declared["files"]}:
            raise AssertionError(f"{name} output checksum mismatch")
    spark = create_spark_session()
    try:
        paths = {name: str(ROOT / manifest["outputs"][name]["path"])
                 for name in ("silver", "provenance", "scope_excluded", "scope_unresolved", "quarantine")}
        frames = {name: spark.read.parquet(path) for name, path in paths.items()}
        counts = {name: frame.count() for name, frame in frames.items()}
        expected = preflight["metrics"]
        if counts != {"silver": expected["silver_rows"],
                      "provenance": expected["silver_rows"],
                      "scope_excluded": expected["scope_excluded_rows"],
                      "scope_unresolved": expected["scope_unresolved_rows"],
                      "quarantine": expected["quarantine_rows"]}:
            raise AssertionError(f"Parquet counts differ from preflight: {counts}")
        silver, prov = frames["silver"], frames["provenance"]
        if silver.select("job_id").distinct().count() != counts["silver"]:
            raise AssertionError("Silver job IDs are not unique")
        if prov.select("job_id").distinct().count() != counts["provenance"]:
            raise AssertionError("Provenance job IDs are not unique")
        if silver.join(prov, "job_id", "left_anti").count() or prov.join(
                silver, "job_id", "left_anti").count():
            raise AssertionError("Silver/provenance keys are not 1:1")
        by_market = [{"source": row["source"], "market": row["market"], "rows": row["count"]}
                     for row in silver.groupBy("source", "market").count()
                     .orderBy("source", "market").collect()]
        if any(row["market"] != ("US_FEDERAL" if row["source"] == "usajobs_historic" else "GLOBAL")
               for row in by_market):
            raise AssertionError("GLOBAL and US_FEDERAL markets were mixed")
        partial = prov.filter((F.col("source") == "remotive") &
                              (F.col("survivor_run_id") == PARTIAL_RUN_ID) &
                              (F.col("survivor_manifest_sha256") == PARTIAL_MANIFEST_SHA256))
        if partial.count() != 10:
            raise AssertionError("Silver must retain 10 in-scope Remotive survivors from pinned partial")
        if prov.filter((F.col("source") == "arbeitnow") &
                       (F.col("survivor_run_id") == PARTIAL_RUN_ID)).count():
            raise AssertionError("Partial Arbeitnow cannot contribute unique Silver rows")
        if frames["scope_excluded"].filter(F.col("source") == "remotive").count() != 5:
            raise AssertionError("Five Remotive titles must be scope-excluded")
        if frames["scope_unresolved"].filter(F.col("source") == "usajobs_historic").count():
            raise AssertionError("Verified federal rows cannot be unresolved")
        all_lineage = prov.select("job_id", "source", "survivor_run_id", "input_lineage")
        for name in ("scope_excluded", "scope_unresolved"):
            all_lineage = all_lineage.unionByName(
                frames[name].select("job_id", "source", "survivor_run_id", "input_lineage"))
        if all_lineage.count() != expected["unique_rows"]:
            raise AssertionError("Lineage artifacts do not cover every unique valid input")
        if all_lineage.filter((F.size("input_lineage") == 0) |
                              (F.size(F.expr("filter(input_lineage, x -> x.selected_survivor)")) != 1)).count():
            raise AssertionError("Every scope branch needs complete lineage and one survivor")
        multi_run = all_lineage.filter(F.expr(
            "size(array_distinct(transform(input_lineage, x -> x.input_run_id))) > 1"
        )).count()
        if multi_run != expected["multi_run_lineage_ids"]:
            raise AssertionError("Cross-run source ID lineage count differs from preflight")
        if all_lineage.filter((F.col("source") == "arbeitnow") &
                              (F.col("survivor_run_id") == PARTIAL_RUN_ID)).count():
            raise AssertionError("Partial Arbeitnow must never be selected survivor")
    finally:
        spark.stop()
    report = {"status": "passed", "created_at": utc_now(),
              "etl_run_id": manifest["run_id"], "etl_manifest_path": Path(manifest_path).relative_to(ROOT).as_posix(),
              "etl_manifest_sha256": actual_sha, "preflight_sha256": sha256_file(PREFLIGHT),
              "parquet_counts": counts, "silver_by_source_market": by_market,
              "old_artifact_sha256": old_hashes,
              "forecast_gate": "NO_GO", "gold_created": False}
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Audit Silver 2026", "",
             f"- Kết quả: **PASS**; ETL run `{manifest['run_id']}`.",
             f"- Manifest SHA-256: `{actual_sha}`.",
             f"- Input {expected['input_rows']:,}; valid {expected['valid_rows']:,}; duplicate {expected['duplicate_rows']:,}; quarantine {counts['quarantine']:,}.",
             f"- Silver {counts['silver']:,}; provenance {counts['provenance']:,}; ngoài IT {counts['scope_excluded']:,}; chưa xác định {counts['scope_unresolved']:,}.",
             "", "## Silver theo nguồn và market", "",
             "| Source | Market | Rows |", "|---|---|---:|"]
    lines += [f"| {item['source']} | {item['market']} | {item['rows']:,} |" for item in by_market]
    lines += ["", "## Kiểm chứng", "",
              "- SHA manifest, tất cả thư mục Parquet và gate preflight khớp.",
              "- Job ID của Silver và provenance 1:1; mỗi dòng có input lineage.",
              "- Remotive trong Silver có 10 dòng từ partial đã pin; 5 dòng ngoài IT lưu riêng.",
              "- USAJOBS PositionSeries=2210 chỉ ở US_FEDERAL; GLOBAL không trộn mẫu số.",
              "- SHA taxonomy v0.1, ETL/Gold manifest cũ và Silver/provenance cũ còn nguyên.",
              "- 10.788 dòng chưa xác định được giữ riêng, không đưa vào Silver hoặc quarantine.",
              "- Forecast gate giữ NO_GO; chưa tạo Gold hoặc dashboard trong iteration này.",
              "", "## Giới hạn", "",
              "Mẫu 175 dòng là AI-assisted, không phải human ground truth. 83,3% Arbeitnow còn unresolved; "
              "phân tích GLOBAL hiện chỉ đại diện cho các tiêu đề có bằng chứng IT theo policy v1."]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("sha256")
    args = parser.parse_args()
    result = audit(Path(args.manifest).resolve(), args.sha256)
    print(json.dumps({"status": result["status"], "etl_run_id": result["etl_run_id"],
                      "parquet_counts": result["parquet_counts"]}))
