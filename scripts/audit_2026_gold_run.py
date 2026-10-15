"""Independently verify immutable descriptive Gold 2026 before dashboard use."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pyspark.sql import functions as F

from src.analytics.phase03_gold import (
    ETL_2026_RUN_ID, ETL_2026_SHA256, JOB_SCOPE_OUTPUT_ROOT,
    OLD_GOLD_MANIFEST, OLD_GOLD_SHA256, verify_2026_silver_authorization,
    load_verified_etl_manifest,
)
from src.common.run_manifest import sha256_file, utc_now
from src.processing.spark_etl import _directory_evidence, create_spark_session

OUT_JSON = ROOT / "docs/data/2026_gold_run_audit.json"
OUT_MD = ROOT / "docs/reviews/2026_GOLD_RUN_AUDIT_2026-10-15.md"
TABLE_KEYS = {
    "market_stats": ["market", "month", "source"],
    "occupation_stats": ["market", "month", "source", "occupation"],
    "skill_evidence_stats": ["market", "month", "source", "occupation", "skills_origin", "taxonomy_version"],
    "skill_stats": ["market", "month", "source", "occupation", "skills_origin", "taxonomy_version", "skill"],
    "skill_trends": ["market", "month", "source", "occupation", "skills_origin", "taxonomy_version", "skill"],
}


def audit(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    run_dir = manifest_path.parent
    if run_dir.parent.resolve() != JOB_SCOPE_OUTPUT_ROOT.resolve() or manifest_path.name != "manifest.json":
        raise ValueError("Gold run is outside the immutable JobScope namespace")
    gold_sha = sha256_file(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("run_id") != run_dir.name or manifest.get("status") != "completed" or
            manifest.get("analysis_type") != "observed_descriptive_only" or
            manifest.get("predictive_gate", {}).get("decision") != "NO_GO"):
        raise AssertionError("Gold manifest is not a completed descriptive NO_GO run")
    if set(path.name for path in run_dir.iterdir()) != set(TABLE_KEYS) | {"manifest.json"}:
        raise AssertionError("Gold run has missing or unexpected artifacts")
    if sha256_file(OLD_GOLD_MANIFEST) != OLD_GOLD_SHA256:
        raise AssertionError("Legacy Gold manifest changed")
    etl_path = ROOT / "data/manifests/etl" / f"etl_{ETL_2026_RUN_ID}.json"
    etl, _ = load_verified_etl_manifest(etl_path, ETL_2026_SHA256, allow_scoped_inputs=True)
    _, silver_audit_sha = verify_2026_silver_authorization(etl, etl_path, ETL_2026_SHA256)
    gold_input = manifest["input"]
    if (gold_input.get("etl_run_id") != ETL_2026_RUN_ID or
            gold_input.get("etl_manifest_sha256") != ETL_2026_SHA256 or
            gold_input.get("silver_audit_sha256") != silver_audit_sha or
            gold_input.get("input_selection_sha256") != etl["input_selection"]["sha256"] or
            gold_input.get("silver_rows") != 8370 or gold_input.get("provenance_rows") != 8370 or
            gold_input.get("silver_sha256") != etl["outputs"]["silver"]["sha256"] or
            manifest.get("taxonomy_version") != "v0.2" or
            manifest.get("taxonomy_config_sha256") != etl["taxonomy_config_sha256"] or
            manifest.get("scope_policy_version") != "2026_it_scope_v1" or
            manifest.get("scope_policy_sha256") != etl["scope_policy_sha256"] or
            manifest.get("ai_review_sample_sha256") != etl["ai_review_sample_sha256"] or
            manifest.get("scope_summary") != {"silver_rows": 8370, "scope_excluded_rows": 548,
                                              "scope_unresolved_rows": 10788}):
        raise AssertionError("Gold lineage or scope evidence differs from audited Silver")
    for name in TABLE_KEYS:
        declared = manifest["outputs"][name]
        if (ROOT / declared["path"]).resolve() != (run_dir / name).resolve():
            raise AssertionError(f"Gold {name} path escaped run namespace")
        if _directory_evidence(run_dir / name) != {"sha256": declared["sha256"],
                                                    "files": declared["files"]}:
            raise AssertionError(f"Gold {name} SHA differs from manifest")
    spark = create_spark_session()
    try:
        frames = {name: spark.read.parquet(str(run_dir / name)) for name in TABLE_KEYS}
        counts = {}
        for name, frame in frames.items():
            count = frame.count()
            if count != manifest["outputs"][name]["rows"]:
                raise AssertionError(f"Gold {name} count mismatch")
            if frame.select(*TABLE_KEYS[name]).distinct().count() != count:
                raise AssertionError(f"Gold {name} key collision")
            if frame.filter(F.col("market").isNull() | F.col("source").isNull() |
                            F.col("month").isNull()).limit(1).count():
                raise AssertionError(f"Gold {name} has null scope key")
            counts[name] = count
        totals = {
            "market_jobs": frames["market_stats"].agg(F.sum("job_count")).first()[0],
            "occupation_jobs": frames["occupation_stats"].agg(F.sum("job_count")).first()[0],
            "skill_origin_jobs": frames["skill_evidence_stats"].agg(F.sum("origin_job_count")).first()[0],
        }
        if set(totals.values()) != {8370}:
            raise AssertionError(f"Gold accounting does not equal 8,370 Silver rows: {totals}")
        market_rows = [row.asDict() for row in frames["market_stats"].select(
            "market", "source", "month", "job_count").orderBy("market", "source", "month").collect()]
        source_totals = {}
        for row in market_rows:
            key = (row["market"], row["source"])
            source_totals[key] = source_totals.get(key, 0) + row["job_count"]
        if source_totals != {("GLOBAL", "arbeitnow"): 1621,
                             ("GLOBAL", "remotive"): 10,
                             ("US_FEDERAL", "usajobs_historic"): 6739}:
            raise AssertionError("Gold source/market totals differ from acceptance")
        if ({r["month"] for r in market_rows if r["source"] == "arbeitnow"} != {"2026-10"} or
                {(r["month"], r["job_count"]) for r in market_rows if r["source"] == "remotive"} !=
                {("2026-09", 8), ("2026-10", 2)} or
                {r["month"] for r in market_rows if r["source"] == "usajobs_historic"} !=
                {f"2026-{month:02d}" for month in range(1, 11)}):
            raise AssertionError("Gold contains a missing or synthetic month")
        if any((r["market"] == "US_FEDERAL") != (r["source"] == "usajobs_historic")
               for r in market_rows):
            raise AssertionError("GLOBAL and US_FEDERAL source scopes mixed")
        if frames["occupation_stats"].filter(F.col("occupation") == "Other IT").count() == 0:
            raise AssertionError("Accepted Other IT disappeared from Gold")
    finally:
        spark.stop()
    result = {
        "schema_version": 1, "status": "passed", "completed_at": utc_now(),
        "run_id": manifest["run_id"],
        "manifest_path": manifest_path.relative_to(ROOT).as_posix(),
        "manifest_sha256": gold_sha,
        "analysis_type": "observed_descriptive_only",
        "input": gold_input,
        "taxonomy_version": manifest["taxonomy_version"],
        "taxonomy_config_sha256": manifest["taxonomy_config_sha256"],
        "scope_policy_version": manifest["scope_policy_version"],
        "scope_policy_sha256": manifest["scope_policy_sha256"],
        "ai_review_sample_sha256": manifest["ai_review_sample_sha256"],
        "scope_summary": manifest["scope_summary"],
        "outputs": {name: {"rows": counts[name], "sha256": manifest["outputs"][name]["sha256"]}
                    for name in TABLE_KEYS},
        "market_source_month": market_rows,
        "accounting": totals,
        "predictive_gate": manifest["predictive_gate"],
        "old_gold_manifest_sha256": OLD_GOLD_SHA256,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Audit Gold JobScope 2026", "",
             f"- Kết quả: **PASS**; run `{manifest['run_id']}`.",
             f"- Manifest SHA-256: `{gold_sha}`.",
             "- Nguồn: Silver analytical 8.370 tin, taxonomy v0.2, scope policy 2026_it_scope_v1.",
             "- GLOBAL: 1.631 (Arbeitnow 1.621, Remotive 10); US_FEDERAL: 6.739 USAJOBS 2210.",
             "- Cả market, occupation, skill evidence đều cộng về 8.370; `market` nằm trong mọi khóa.",
             "- 548 excluded và 10.788 unresolved không đi vào mẫu số Gold.",
             "", "## Năm bảng Gold", "", "| Bảng | Rows |", "|---|---:|"]
    lines += [f"| {name} | {counts[name]:,} |" for name in TABLE_KEYS]
    lines += ["", "## Tháng quan sát", "", "| Market | Source | Month | Jobs |", "|---|---|---|---:|"]
    lines += [f"| {r['market']} | {r['source']} | {r['month']} | {r['job_count']:,} |"
              for r in market_rows]
    lines += ["", "## Giới hạn", "",
              "Gold là mô tả quan sát. GLOBAL 2026 chỉ gồm title có bằng chứng IT; 10.788 Arbeitnow unresolved không phải non-IT.",
              "US_FEDERAL là tin tuyển dụng liên bang PositionSeries=2210, không đại diện toàn thị trường Mỹ.",
              "Snapshot API không phải lịch sử liên tục; tháng không quan sát không được điền 0.",
              "Predictive gate vẫn **NO_GO**; không có bảng model hoặc prediction."]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    args = parser.parse_args()
    report = audit(args.manifest)
    print(json.dumps({"status": report["status"], "run_id": report["run_id"],
                      "manifest_sha256": report["manifest_sha256"],
                      "outputs": {k: v["rows"] for k, v in report["outputs"].items()}},
                     ensure_ascii=False))
