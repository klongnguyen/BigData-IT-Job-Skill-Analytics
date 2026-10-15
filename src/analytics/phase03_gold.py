"""Build scoped, descriptive Gold tables from one verified Phase 02 ETL run."""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from pyspark.sql import Window
from pyspark.sql import functions as F
from pyspark import StorageLevel

from src.analytics.predictive_gate import assess_predictive_gate
from src.common.run_manifest import new_run_id, sha256_file, utc_now
from src.processing.spark_etl import _directory_evidence, create_spark_session
from src.processing.input_selection import (
    PARTIAL_MANIFEST_SHA256, PARTIAL_RUN_ID, load_input_selection,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "gold" / "global" / "runs"
POLICY_FILE = ROOT / "docs" / "planning" / "go_no_go_report.md"
TAXONOMY_FILES = ("job_title_mapping_v0.json", "skills_v0.json")
JOB_SCOPE_OUTPUT_ROOT = ROOT / "data" / "gold" / "jobscope" / "runs"
ETL_2026_RUN_ID = "10d0710787d2402186356858d3331e50"
ETL_2026_SHA256 = "817c24b15a12436ce47c2fce08a891ce50f31cb87221bc3ce2b74a028a7b15c9"
SILVER_2026_AUDIT = ROOT / "docs" / "data" / "2026_silver_run_audit.json"
SILVER_2026_SELECTION = ROOT / "docs" / "data" / "2026_silver_input_selection.json"
OLD_GOLD_MANIFEST = ROOT / "data/gold/global/runs/20261004T110131548191Z-e38fa7303cf4/manifest.json"
OLD_GOLD_SHA256 = "2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d"


def _workspace_relative(path):
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def verify_2026_silver_authorization(report, etl_path, expected_sha256):
    """Authorize only the audited 2026 Silver run, including its exact partial."""
    if (Path(etl_path).resolve() != (ROOT / "data/manifests/etl" / f"etl_{ETL_2026_RUN_ID}.json").resolve()
            or expected_sha256 != ETL_2026_SHA256 or report.get("run_id") != ETL_2026_RUN_ID):
        raise ValueError("Gold 2026 requires the exact audited ETL manifest")
    audit = json.loads(SILVER_2026_AUDIT.read_text(encoding="utf-8"))
    if (audit.get("status") != "passed" or audit.get("etl_run_id") != ETL_2026_RUN_ID
            or audit.get("etl_manifest_sha256") != ETL_2026_SHA256):
        raise ValueError("Silver 2026 audit is not passed for the exact ETL run")
    if report.get("input_selection", {}).get("sha256") != sha256_file(SILVER_2026_SELECTION):
        raise ValueError("Gold 2026 input-selection SHA mismatch")
    if (report.get("taxonomy_version") != "v0.2" or
            report.get("taxonomy_config_sha256", {}).get("job_title_mapping_v0_2.json") !=
            sha256_file(ROOT / "configs/job_title_mapping_v0_2.json") or
            report.get("scope_policy_version") != "2026_it_scope_v1" or
            report.get("scope_policy_sha256") != sha256_file(ROOT / "configs/job_scope_policy_2026_v1.json") or
            report.get("ai_review_sample_sha256") != sha256_file(ROOT / "docs/data/2026_it_scope_sample.csv")):
        raise ValueError("Gold 2026 taxonomy, scope policy or AI sample SHA mismatch")
    expected_counts = {"silver_rows": 8370, "provenance_rows": 8370,
                       "scope_excluded_rows": 548, "scope_unresolved_rows": 10788,
                       "quarantine_rows": 0, "unique_survivors": 19706}
    if any(report.get("metrics", {}).get(key) != value for key, value in expected_counts.items()):
        raise ValueError("Gold 2026 Silver scope accounting mismatch")
    if audit.get("parquet_counts") != {"silver": 8370, "provenance": 8370,
                                       "scope_excluded": 548, "scope_unresolved": 10788,
                                       "quarantine": 0}:
        raise ValueError("Gold 2026 Silver audit counts differ")
    for name, count in (("silver", 8370), ("provenance", 8370),
                        ("scope_excluded", 548), ("scope_unresolved", 10788), ("quarantine", 0)):
        output = report.get("outputs", {}).get(name, {})
        expected_dir = ROOT / "data" / name / "jobscope" / "runs" / ETL_2026_RUN_ID
        if Path(output.get("path", "")).resolve() != expected_dir.resolve():
            raise ValueError(f"Gold 2026 {name} path is outside audited namespace")
        if _directory_evidence(expected_dir) != {"sha256": output.get("sha256"),
                                                  "files": output.get("files")}:
            raise ValueError(f"Gold 2026 {name} output SHA mismatch")
    selected, _ = load_input_selection(SILVER_2026_SELECTION, sha256_file(SILVER_2026_SELECTION))
    declared = {run["run_id"]: run for run in report["input_runs"]}
    if len(declared) != len(selected) or any(
            declared.get(run["run_id"], {}).get("manifest_sha256") != run["manifest_sha256"]
            or declared[run["run_id"]]["status"] != run["status"] for run in selected):
        raise ValueError("Gold 2026 Bronze lineage differs from pinned selection")
    partials = {(run["run_id"], run["manifest_sha256"]) for run in report["input_runs"]
                if run["status"] == "partial"}
    if partials != {(PARTIAL_RUN_ID, PARTIAL_MANIFEST_SHA256)}:
        raise ValueError("Gold 2026 has an unauthorized partial Bronze run")
    return audit, sha256_file(SILVER_2026_AUDIT)


def load_verified_etl_manifest(path, expected_sha256, allow_scoped_inputs=False):
    """Lock the exact manifest and verify its Silver/provenance outputs."""
    path = Path(path).resolve()
    if not expected_sha256:
        raise ValueError("An expected ETL manifest SHA-256 is required")
    actual_sha256 = sha256_file(path)
    if actual_sha256.lower() != expected_sha256.lower():
        raise ValueError("ETL manifest SHA-256 mismatch")
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("schema_version") != 1 or report.get("status") != "completed":
        raise ValueError("Phase 03 requires a completed Phase 02 ETL manifest")
    input_runs = report.get("input_runs") or []
    if not input_runs:
        raise ValueError("ETL manifest has no declared Bronze input runs")
    if any(run.get("status") != "complete" for run in input_runs) and not allow_scoped_inputs:
        raise ValueError("Partial/scoped Bronze input requires --allow-scoped-inputs")
    metrics = report.get("metrics") or {}
    if metrics.get("silver_rows") != metrics.get("provenance_rows"):
        raise ValueError("ETL manifest does not declare 1:1 Silver/provenance counts")
    for name in ("silver", "provenance"):
        declared = (report.get("outputs") or {}).get(name) or {}
        root = Path(declared.get("path", "")).resolve()
        if not root.is_dir() or not declared.get("sha256"):
            raise ValueError(f"Missing {name} output in ETL manifest")
        actual = _directory_evidence(root)
        if actual != {"sha256": declared["sha256"], "files": declared.get("files")}:
            raise ValueError(f"{name} output checksum mismatch")
    return report, actual_sha256


def _assert_unique(frame, keys, label):
    rows = frame.count()
    if frame.select(*keys).distinct().count() != rows:
        raise AssertionError(f"Duplicate {label} key")
    return rows


def build_gold_tables(silver, provenance, taxonomy_version):
    """Return source-scoped monthly tables; unobserved months are never zero-filled."""
    provenance_fields = provenance.select(
        "job_id",
        F.col("source").alias("provenance_source"),
        "skills_origin",
        "taxonomy_version",
    )
    jobs = (silver.join(provenance_fields, "job_id", "inner")
        .withColumn("market", F.coalesce(F.col("market") if "market" in silver.columns else F.lit(None), F.lit("GLOBAL")))
        .withColumn("month", F.date_format("posted_at", "yyyy-MM"))
        .withColumn("occupation", F.when(
            F.col("normalized_title").isNull() | (F.trim("normalized_title") == ""),
            F.lit("Other IT"),
        ).otherwise(F.col("normalized_title")))
        .withColumn("has_skill_evidence", F.col("skills").isNotNull() & (F.size("skills") > 0))
        .persist(StorageLevel.MEMORY_AND_DISK))
    if jobs.filter(
            F.col("month").isNull() | F.col("source").isNull() | F.col("market").isNull() |
            F.col("provenance_source").isNull() |
            (F.col("source") != F.col("provenance_source")) |
            F.col("skills_origin").isNull()).limit(1).count():
        raise AssertionError("Silver/provenance source, skill origin or posted month invalid")
    if jobs.filter(F.col("taxonomy_version").isNull() |
                   (F.col("taxonomy_version") != F.lit(taxonomy_version))).limit(1).count():
        raise AssertionError("Provenance taxonomy version differs from ETL manifest")

    month_source = ["market", "month", "source"]
    occ_keys = month_source + ["occupation"]
    skill_scope = occ_keys + ["skills_origin", "taxonomy_version"]

    market_stats = jobs.groupBy(*month_source).agg(
        F.count("job_id").alias("job_count"),
        F.countDistinct("company").alias("distinct_companies"),
        F.sum(F.when(F.col("country").isNotNull() & (F.trim("country") != ""), 1).otherwise(0)).alias("known_country_jobs"),
        F.sum(F.when(F.col("work_mode").isNotNull() & (F.trim("work_mode") != ""), 1).otherwise(0)).alias("known_work_mode_jobs"),
        F.sum(F.when(F.col("experience_level").isNotNull() & (F.trim("experience_level") != ""), 1).otherwise(0)).alias("known_experience_jobs"),
        F.sum(F.col("has_skill_evidence").cast("int")).alias("skill_evidence_jobs"),
    ).persist(StorageLevel.MEMORY_AND_DISK)
    occupation_stats = (jobs.groupBy(*occ_keys).agg(F.count("job_id").alias("job_count"))
        .join(market_stats.select(*month_source, F.col("job_count").alias("source_month_jobs")), month_source)
        .withColumn("occupation_share", F.col("job_count") / F.col("source_month_jobs"))
        .persist(StorageLevel.MEMORY_AND_DISK))
    evidence = jobs.groupBy(*skill_scope).agg(
        F.count("job_id").alias("origin_job_count"),
        F.sum(F.col("has_skill_evidence").cast("int")).alias("skill_evidence_jobs"),
    ).persist(StorageLevel.MEMORY_AND_DISK)
    skill_evidence_stats = (evidence
        .join(occupation_stats.select(*occ_keys, F.col("job_count").alias("occupation_job_count")), occ_keys)
        .withColumn("skill_evidence_coverage", F.col("skill_evidence_jobs") / F.col("occupation_job_count"))
        .persist(StorageLevel.MEMORY_AND_DISK))
    skill_counts = (jobs.select(
            "job_id", *skill_scope, F.explode(F.array_distinct("skills")).alias("skill"),
        )
        .filter(F.col("skill").isNotNull() & (F.trim("skill") != ""))
        .groupBy(*(skill_scope + ["skill"]))
        .agg(F.countDistinct("job_id").alias("skill_job_count")))
    # A skill absent in an observed source/occupation/evidence month has rate 0.
    # Months without that observed evidence scope remain absent, never zero-filled.
    series_keys = ["market", "source", "occupation", "skills_origin", "taxonomy_version"]
    skill_universe = skill_counts.select(*series_keys, "skill").distinct()
    observed_grid = skill_evidence_stats.join(skill_universe, series_keys)
    skill_stats = (observed_grid
        .join(skill_counts, skill_scope + ["skill"], "left")
        .withColumn("skill_job_count", F.coalesce(F.col("skill_job_count"), F.lit(0)))
        .withColumn("demand_rate", F.col("skill_job_count") / F.col("occupation_job_count"))
        .persist(StorageLevel.MEMORY_AND_DISK))
    window = Window.partitionBy("market", "source", "occupation", "skills_origin", "taxonomy_version", "skill").orderBy("month")
    skill_trends = (skill_stats
        .withColumn("previous_observed_month", F.lag("month").over(window))
        .withColumn("previous_demand_rate", F.lag("demand_rate").over(window))
        .withColumn("consecutive_observed_month", F.when(
            F.months_between(
                F.to_date(F.concat(F.col("month"), F.lit("-01"))),
                F.to_date(F.concat(F.col("previous_observed_month"), F.lit("-01"))),
            ) == 1, F.lit(True),
        ).otherwise(F.lit(False)))
        .withColumn("observed_delta_pp", F.when(
            F.col("consecutive_observed_month"),
            (F.col("demand_rate") - F.col("previous_demand_rate")) * 100,
        )).persist(StorageLevel.MEMORY_AND_DISK))
    return {
        "market_stats": market_stats,
        "occupation_stats": occupation_stats,
        "skill_evidence_stats": skill_evidence_stats,
        "skill_stats": skill_stats,
        "skill_trends": skill_trends,
    }


def run_phase03(etl_manifest, expected_etl_sha256, output_root=DEFAULT_OUTPUT_ROOT,
                allow_scoped_inputs=False, audit_json=None, jobscope_2026=False):
    if jobscope_2026 and allow_scoped_inputs:
        raise ValueError("Gold 2026 authorization uses the exact audited run, not generic partial allowance")
    if (Path(etl_manifest).resolve().name == f"etl_{ETL_2026_RUN_ID}.json" and not jobscope_2026):
        raise ValueError("Gold 2026 requires explicit --jobscope-2026 authorization")
    report, etl_sha256 = load_verified_etl_manifest(
        etl_manifest, expected_etl_sha256, allow_scoped_inputs or jobscope_2026,
    )
    silver_audit, silver_audit_sha = (verify_2026_silver_authorization(
        report, etl_manifest, expected_etl_sha256) if jobscope_2026 else (None, None))
    if jobscope_2026:
        if Path(output_root).resolve() == DEFAULT_OUTPUT_ROOT.resolve():
            output_root = JOB_SCOPE_OUTPUT_ROOT
        if Path(output_root).resolve() != JOB_SCOPE_OUTPUT_ROOT.resolve():
            raise ValueError("Gold 2026 must publish in the immutable jobscope namespace")
        if sha256_file(OLD_GOLD_MANIFEST) != OLD_GOLD_SHA256:
            raise ValueError("Legacy Gold manifest changed")
    output_root = Path(output_root).resolve()
    input_dirs = [Path(report["outputs"][name]["path"]).resolve() for name in ("silver", "provenance")]
    for directory in input_dirs:
        if output_root == directory or output_root in directory.parents or directory in output_root.parents:
            raise ValueError("Gold output root must not overlap Silver or provenance")

    run_id = new_run_id()
    output_root.mkdir(parents=True, exist_ok=True)
    stage = output_root / f".staging-{run_id}"
    final = output_root / run_id
    stage.mkdir(exist_ok=False)
    spark = None
    try:
        spark = create_spark_session()
        silver = spark.read.parquet(str(input_dirs[0]))
        provenance = spark.read.parquet(str(input_dirs[1]))
        silver_count = _assert_unique(silver, ["job_id"], "Silver job_id")
        provenance_count = _assert_unique(provenance, ["job_id"], "provenance job_id")
        if (silver.filter(F.col("job_id").isNull()).limit(1).count() or
                provenance.filter(F.col("job_id").isNull()).limit(1).count() or
                silver_count != report["metrics"]["silver_rows"] or
                provenance_count != report["metrics"]["provenance_rows"] or
                silver.join(provenance, "job_id", "left_anti").limit(1).count() or
                provenance.join(silver, "job_id", "left_anti").limit(1).count()):
            raise AssertionError("Silver/provenance cardinality or ETL manifest count mismatch")

        observed = None
        if jobscope_2026:
            observed = {(r["market"], r["source"], r["month"]): r["count"]
                        for r in silver.withColumn("month", F.date_format("posted_at", "yyyy-MM"))
                        .groupBy("market", "source", "month").count().collect()}
            by_source = {}
            for (market, source, month_value), count in observed.items():
                by_source[(market, source)] = by_source.get((market, source), 0) + count
            if by_source != {("GLOBAL", "arbeitnow"): 1621,
                             ("GLOBAL", "remotive"): 10,
                             ("US_FEDERAL", "usajobs_historic"): 6739}:
                raise AssertionError("Gold 2026 source/market counts differ from Silver audit")
            if ({m for market, source, m in observed if source == "arbeitnow"} != {"2026-10"} or
                    {(m, n) for (market, source, m), n in observed.items() if source == "remotive"} !=
                    {("2026-09", 8), ("2026-10", 2)} or
                    {m for market, source, m in observed if source == "usajobs_historic"} !=
                    {f"2026-{m:02d}" for m in range(1, 11)}):
                raise AssertionError("Gold 2026 observed-month coverage differs from audit")

        tables = build_gold_tables(silver, provenance, report["taxonomy_version"])
        if (tables["market_stats"].agg(F.sum("job_count")).first()[0] != silver_count or
                tables["occupation_stats"].agg(F.sum("job_count")).first()[0] != silver_count or
                tables["skill_evidence_stats"].agg(F.sum("origin_job_count")).first()[0] != silver_count):
            raise AssertionError("Gold source/occupation/evidence job accounting failed")
        keys = {
            "market_stats": ["market", "month", "source"],
            "occupation_stats": ["market", "month", "source", "occupation"],
            "skill_evidence_stats": ["market", "month", "source", "occupation", "skills_origin", "taxonomy_version"],
            "skill_stats": ["market", "month", "source", "occupation", "skills_origin", "taxonomy_version", "skill"],
            "skill_trends": ["market", "month", "source", "occupation", "skills_origin", "taxonomy_version", "skill"],
        }
        outputs = {}
        for name, frame in tables.items():
            count = _assert_unique(frame, keys[name], name)
            if name == "occupation_stats" and frame.filter(
                    (F.col("occupation_share") < 0) | (F.col("occupation_share") > 1)).limit(1).count():
                raise AssertionError("Occupation share outside [0, 1]")
            if name == "skill_stats" and frame.filter(
                    (F.col("demand_rate") < 0) | (F.col("demand_rate") > 1) |
                    (F.col("skill_evidence_coverage") < 0) | (F.col("skill_evidence_coverage") > 1) |
                    (F.col("skill_job_count") > F.col("skill_evidence_jobs"))).limit(1).count():
                raise AssertionError("Skill demand/evidence accounting failed")
            stage_path = stage / name
            frame.write.mode("errorifexists").parquet(str(stage_path))
            if spark.read.parquet(str(stage_path)).count() != count:
                raise AssertionError(f"Written {name} row count mismatch")
            outputs[name] = {"path": _workspace_relative(final / name) if jobscope_2026 else str(final / name),
                             "rows": count, **_directory_evidence(stage_path)}

        occupation_rows = [row.asDict() for row in tables["occupation_stats"].select(
            "market", "month", "source", "occupation", "job_count").collect()]
        gate = assess_predictive_gate(occupation_rows, report["input_runs"])
        if gate["decision"] != "NO_GO":
            raise AssertionError("2026 Gold forecast gate must remain NO_GO")
        source_occupation = [row.asDict() for row in tables["occupation_stats"].groupBy(
            "market", "source", "occupation").agg(F.sum("job_count").alias("jobs")).orderBy("market", "source", "occupation").collect()]
        occupation_totals = tables["occupation_stats"].groupBy("market", "source", "occupation").agg(
            F.sum("job_count").alias("denominator_jobs"),
        )
        evidence_summary = [row.asDict() for row in tables["skill_evidence_stats"].groupBy(
            "market", "source", "occupation", "skills_origin").agg(
                F.sum("origin_job_count").alias("origin_jobs"),
                F.sum("skill_evidence_jobs").alias("evidence_jobs"),
            ).join(occupation_totals, ["market", "source", "occupation"])
            .orderBy("market", "source", "occupation", "skills_origin").collect()]
        top_window = Window.partitionBy("market", "source", "occupation", "skills_origin").orderBy(
            F.col("skill_job_count").desc(), F.col("skill").asc())
        top_skills = [row.asDict() for row in tables["skill_stats"].groupBy(
            "market", "source", "occupation", "skills_origin", "skill").agg(
                F.sum("skill_job_count").alias("skill_job_count")
            ).withColumn("rank", F.row_number().over(top_window)).filter(F.col("rank") <= 3)
            .orderBy("market", "source", "occupation", "skills_origin", "rank").collect()]
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "status": "completed",
            "completed_at": utc_now(),
            "analysis_type": "observed_descriptive_only",
            "input": {
                "etl_run_id": report["run_id"],
                "etl_manifest_path": _workspace_relative(etl_manifest) if jobscope_2026 else str(Path(etl_manifest).resolve()),
                "etl_manifest_sha256": etl_sha256,
                "bronze_runs": report["input_runs"],
                "silver_rows": silver_count,
                "provenance_rows": provenance_count,
                "silver_sha256": report["outputs"]["silver"]["sha256"],
                "provenance_sha256": report["outputs"]["provenance"]["sha256"],
                "allow_scoped_inputs": allow_scoped_inputs,
                "silver_audit_sha256": silver_audit_sha,
                "input_selection_sha256": report.get("input_selection", {}).get("sha256"),
            },
            "taxonomy_version": report["taxonomy_version"],
            "taxonomy_config_sha256": report.get("taxonomy_config_sha256") or {
                name: sha256_file(ROOT / "configs" / name) for name in TAXONOMY_FILES
            },
            "policy_sha256": sha256_file(POLICY_FILE),
            "scope_policy_version": report.get("scope_policy_version"),
            "scope_policy_sha256": report.get("scope_policy_sha256"),
            "ai_review_sample_sha256": report.get("ai_review_sample_sha256"),
            "scope_summary": ({"silver_rows": 8370, "scope_excluded_rows": 548,
                               "scope_unresolved_rows": 10788} if jobscope_2026 else None),
            "observed_source_market_month": ([{"market": market, "source": source,
                                               "month": month_value, "jobs": count}
                                              for (market, source, month_value), count in sorted(observed.items())]
                                             if observed is not None else None),
            "filters": {"posted_at": "valid Phase 02 Silver only", "dedup": "one survivor per job_id"},
            "environment": {
                "python": sys.version.split()[0],
                "spark": spark.version,
                "java": spark.sparkContext._jvm.java.lang.System.getProperty("java.version"),
                "spark_master": spark.sparkContext.master,
            },
            "outputs": outputs,
            "source_occupation_jobs": source_occupation,
            "skill_evidence_summary": evidence_summary,
            "top_skills_by_count": top_skills,
            "predictive_gate": gate,
        }
        (stage / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8",
        )
        os.replace(stage, final)
        if jobscope_2026 and sha256_file(OLD_GOLD_MANIFEST) != OLD_GOLD_SHA256:
            raise AssertionError("Legacy Gold changed during 2026 publication")
        if audit_json:
            audit_path = Path(audit_json).resolve()
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            audit = {
                "schema_version": manifest["schema_version"],
                "run_id": run_id,
                "completed_at": manifest["completed_at"],
                "analysis_type": manifest["analysis_type"],
                "manifest_path": _workspace_relative(final / "manifest.json") if jobscope_2026 else str(final / "manifest.json"),
                "manifest_sha256": sha256_file(final / "manifest.json"),
                "input": manifest["input"],
                "taxonomy_version": manifest["taxonomy_version"],
                "taxonomy_config_sha256": manifest["taxonomy_config_sha256"],
                "policy_sha256": manifest["policy_sha256"],
                "scope_policy_version": manifest["scope_policy_version"],
                "scope_policy_sha256": manifest["scope_policy_sha256"],
                "ai_review_sample_sha256": manifest["ai_review_sample_sha256"],
                "scope_summary": manifest["scope_summary"],
                "observed_source_market_month": manifest["observed_source_market_month"],
                "environment": manifest["environment"],
                "filters": manifest["filters"],
                "outputs": {name: {"rows": item["rows"], "sha256": item["sha256"]}
                            for name, item in outputs.items()},
                "source_occupation_jobs": source_occupation,
                "skill_evidence_summary": evidence_summary,
                "top_skills_by_count": top_skills,
                "predictive_gate": gate,
            }
            temporary = audit_path.with_suffix(audit_path.suffix + ".tmp")
            temporary.write_text(json.dumps(audit, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
            os.replace(temporary, audit_path)
        return manifest
    finally:
        if spark is not None:
            spark.stop()
        if stage.exists():
            shutil.rmtree(stage)


def _parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etl-manifest", required=True)
    parser.add_argument("--etl-manifest-sha256", required=True)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--allow-scoped-inputs", action="store_true")
    parser.add_argument("--jobscope-2026", action="store_true",
                        help="Authorize only the exact audited Silver 2026 run")
    parser.add_argument("--audit-json")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    result = run_phase03(
        args.etl_manifest, args.etl_manifest_sha256,
        output_root=args.output_root,
        allow_scoped_inputs=args.allow_scoped_inputs,
        audit_json=args.audit_json,
        jobscope_2026=args.jobscope_2026,
    )
    print(json.dumps({
        "run_id": result["run_id"],
        "input_rows": result["input"]["silver_rows"],
        "outputs": {name: item["rows"] for name, item in result["outputs"].items()},
        "predictive_gate": result["predictive_gate"]["decision"],
    }, ensure_ascii=False))
