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


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = ROOT / "data" / "gold" / "global" / "runs"
POLICY_FILE = ROOT / "docs" / "planning" / "go_no_go_report.md"
TAXONOMY_FILES = ("job_title_mapping_v0.json", "skills_v0.json")


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
        .withColumn("month", F.date_format("posted_at", "yyyy-MM"))
        .withColumn("occupation", F.when(
            F.col("normalized_title").isNull() | (F.trim("normalized_title") == ""),
            F.lit("Other IT"),
        ).otherwise(F.col("normalized_title")))
        .withColumn("has_skill_evidence", F.col("skills").isNotNull() & (F.size("skills") > 0))
        .persist(StorageLevel.MEMORY_AND_DISK))
    if jobs.filter(
            F.col("month").isNull() | F.col("source").isNull() |
            F.col("provenance_source").isNull() |
            (F.col("source") != F.col("provenance_source")) |
            F.col("skills_origin").isNull()).limit(1).count():
        raise AssertionError("Silver/provenance source, skill origin or posted month invalid")
    if jobs.filter(F.col("taxonomy_version").isNull() |
                   (F.col("taxonomy_version") != F.lit(taxonomy_version))).limit(1).count():
        raise AssertionError("Provenance taxonomy version differs from ETL manifest")

    month_source = ["month", "source"]
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
    series_keys = ["source", "occupation", "skills_origin", "taxonomy_version"]
    skill_universe = skill_counts.select(*series_keys, "skill").distinct()
    observed_grid = skill_evidence_stats.join(skill_universe, series_keys)
    skill_stats = (observed_grid
        .join(skill_counts, skill_scope + ["skill"], "left")
        .withColumn("skill_job_count", F.coalesce(F.col("skill_job_count"), F.lit(0)))
        .withColumn("demand_rate", F.col("skill_job_count") / F.col("occupation_job_count"))
        .persist(StorageLevel.MEMORY_AND_DISK))
    window = Window.partitionBy("source", "occupation", "skills_origin", "taxonomy_version", "skill").orderBy("month")
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
                allow_scoped_inputs=False, audit_json=None):
    report, etl_sha256 = load_verified_etl_manifest(
        etl_manifest, expected_etl_sha256, allow_scoped_inputs,
    )
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

        tables = build_gold_tables(silver, provenance, report["taxonomy_version"])
        if (tables["market_stats"].agg(F.sum("job_count")).first()[0] != silver_count or
                tables["occupation_stats"].agg(F.sum("job_count")).first()[0] != silver_count or
                tables["skill_evidence_stats"].agg(F.sum("origin_job_count")).first()[0] != silver_count):
            raise AssertionError("Gold source/occupation/evidence job accounting failed")
        keys = {
            "market_stats": ["month", "source"],
            "occupation_stats": ["month", "source", "occupation"],
            "skill_evidence_stats": ["month", "source", "occupation", "skills_origin", "taxonomy_version"],
            "skill_stats": ["month", "source", "occupation", "skills_origin", "taxonomy_version", "skill"],
            "skill_trends": ["month", "source", "occupation", "skills_origin", "taxonomy_version", "skill"],
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
            outputs[name] = {"path": str(final / name), "rows": count, **_directory_evidence(stage_path)}

        occupation_rows = [row.asDict() for row in tables["occupation_stats"].select(
            "month", "source", "occupation", "job_count").collect()]
        gate = assess_predictive_gate(occupation_rows, report["input_runs"])
        source_occupation = [row.asDict() for row in tables["occupation_stats"].groupBy(
            "source", "occupation").agg(F.sum("job_count").alias("jobs")).orderBy("source", "occupation").collect()]
        occupation_totals = tables["occupation_stats"].groupBy("source", "occupation").agg(
            F.sum("job_count").alias("denominator_jobs"),
        )
        evidence_summary = [row.asDict() for row in tables["skill_evidence_stats"].groupBy(
            "source", "occupation", "skills_origin").agg(
                F.sum("origin_job_count").alias("origin_jobs"),
                F.sum("skill_evidence_jobs").alias("evidence_jobs"),
            ).join(occupation_totals, ["source", "occupation"])
            .orderBy("source", "occupation", "skills_origin").collect()]
        top_window = Window.partitionBy("source", "occupation", "skills_origin").orderBy(
            F.col("skill_job_count").desc(), F.col("skill").asc())
        top_skills = [row.asDict() for row in tables["skill_stats"].groupBy(
            "source", "occupation", "skills_origin", "skill").agg(
                F.sum("skill_job_count").alias("skill_job_count")
            ).withColumn("rank", F.row_number().over(top_window)).filter(F.col("rank") <= 3)
            .orderBy("source", "occupation", "skills_origin", "rank").collect()]
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "status": "completed",
            "completed_at": utc_now(),
            "analysis_type": "observed_descriptive_only",
            "input": {
                "etl_run_id": report["run_id"],
                "etl_manifest_path": str(Path(etl_manifest).resolve()),
                "etl_manifest_sha256": etl_sha256,
                "bronze_runs": report["input_runs"],
                "silver_rows": silver_count,
                "provenance_rows": provenance_count,
                "silver_sha256": report["outputs"]["silver"]["sha256"],
                "provenance_sha256": report["outputs"]["provenance"]["sha256"],
                "allow_scoped_inputs": allow_scoped_inputs,
            },
            "taxonomy_version": report["taxonomy_version"],
            "taxonomy_config_sha256": report.get("taxonomy_config_sha256") or {
                name: sha256_file(ROOT / "configs" / name) for name in TAXONOMY_FILES
            },
            "policy_sha256": sha256_file(POLICY_FILE),
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
        if audit_json:
            audit_path = Path(audit_json).resolve()
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            audit = {
                "schema_version": manifest["schema_version"],
                "run_id": run_id,
                "completed_at": manifest["completed_at"],
                "analysis_type": manifest["analysis_type"],
                "manifest_path": str(final / "manifest.json"),
                "manifest_sha256": sha256_file(final / "manifest.json"),
                "input": manifest["input"],
                "taxonomy_version": manifest["taxonomy_version"],
                "taxonomy_config_sha256": manifest["taxonomy_config_sha256"],
                "policy_sha256": manifest["policy_sha256"],
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
    parser.add_argument("--audit-json")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    result = run_phase03(
        args.etl_manifest, args.etl_manifest_sha256,
        output_root=args.output_root,
        allow_scoped_inputs=args.allow_scoped_inputs,
        audit_json=args.audit_json,
    )
    print(json.dumps({
        "run_id": result["run_id"],
        "input_rows": result["input"]["silver_rows"],
        "outputs": {name: item["rows"] for name, item in result["outputs"].items()},
        "predictive_gate": result["predictive_gate"]["decision"],
    }, ensure_ascii=False))
