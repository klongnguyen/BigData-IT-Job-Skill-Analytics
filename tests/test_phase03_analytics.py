"""Spark fixture for scoped Gold denominators, evidence and observed gaps."""

import json
from datetime import datetime, timezone

import pytest

from src.common.run_manifest import sha256_file
from src.processing.spark_etl import _directory_evidence, create_spark_session
from src.analytics.phase03_gold import load_verified_etl_manifest, run_phase03


def _fixture_etl(tmp_path):
    spark = create_spark_session()
    try:
        def job(job_id, source, month, skills, occupation="Data Engineer"):
            return {
                "job_id": job_id, "source": source, "normalized_title": occupation,
                "posted_at": datetime.fromisoformat(month + "-15T00:00:00+00:00"),
                "skills": skills, "company": "A Co",
                "country": "United States" if source == "arbeitnow" else None,
                "work_mode": "Remote" if source == "arbeitnow" else None,
                "experience_level": "Mid" if source == "arbeitnow" else None,
            }

        silver_rows = [
            job("h1", "archive", "2023-01", ["python", "sql"]),
            job("h2", "archive", "2023-01", []),
            job("h3", "archive", "2023-02", ["python"]),
            job("h4", "archive", "2023-04", ["python", "sql"]),
            job("h5", "archive", "2023-01", [], "Other IT"),
            job("f1", "arbeitnow", "2026-09", ["python"]),
        ]
        provenance_rows = [
            {"job_id": row["job_id"], "source": row["source"],
             "skills_origin": "source_tags" if row["source"] == "archive" else "extracted_from_jd",
             "taxonomy_version": "v0.1"}
            for row in silver_rows
        ]
        silver_path = tmp_path / "etl" / "silver"
        provenance_path = tmp_path / "etl" / "provenance"
        spark.createDataFrame(silver_rows).write.parquet(str(silver_path))
        spark.createDataFrame(provenance_rows).write.parquet(str(provenance_path))
    finally:
        spark.stop()
    report = {
        "schema_version": 1, "run_id": "fixture-etl", "status": "completed",
        "input_runs": [{"run_id": "fixture-bronze", "status": "complete"}],
        "metrics": {"silver_rows": len(silver_rows), "provenance_rows": len(provenance_rows)},
        "taxonomy_version": "v0.1",
        "outputs": {
            "silver": {"path": str(silver_path), **_directory_evidence(silver_path)},
            "provenance": {"path": str(provenance_path), **_directory_evidence(provenance_path)},
        },
    }
    path = tmp_path / "etl" / "manifest.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path, sha256_file(path), silver_path


def test_gold_counts_evidence_origin_and_real_month_gap(tmp_path):
    path, checksum, _ = _fixture_etl(tmp_path)
    audit_path = tmp_path / "audit.json"
    result = run_phase03(path, checksum, output_root=tmp_path / "gold", audit_json=audit_path)
    assert result["input"]["silver_rows"] == result["input"]["provenance_rows"] == 6
    assert result["predictive_gate"]["decision"] == "NO_GO"
    assert not list((tmp_path / "gold").rglob("*prediction*"))
    evidence_summary = next(row for row in result["skill_evidence_summary"]
                            if row["source"] == "archive" and row["occupation"] == "Data Engineer")
    assert evidence_summary["denominator_jobs"] == 4
    assert evidence_summary["origin_jobs"] == 4
    assert evidence_summary["evidence_jobs"] == 3
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["analysis_type"] == "observed_descriptive_only"
    assert audit["taxonomy_version"] == "v0.1"
    assert audit["taxonomy_config_sha256"]
    assert audit["policy_sha256"]
    assert audit["environment"]["spark"]
    assert audit["filters"]["dedup"]

    spark = create_spark_session()
    try:
        occupation = spark.read.parquet(result["outputs"]["occupation_stats"]["path"])
        january = occupation.filter(
            (occupation.source == "archive") & (occupation.month == "2023-01") &
            (occupation.occupation == "Data Engineer")
        ).first()
        assert january.job_count == 2 and january.source_month_jobs == 3
        assert january.occupation_share == pytest.approx(2 / 3)

        skills = spark.read.parquet(result["outputs"]["skill_stats"]["path"])
        january_python = skills.filter(
            (skills.source == "archive") & (skills.month == "2023-01") &
            (skills.occupation == "Data Engineer") & (skills.skill == "python")
        ).first()
        assert january_python.skill_job_count == 1
        assert january_python.occupation_job_count == 2
        assert january_python.skill_evidence_jobs == 1
        assert january_python.demand_rate == pytest.approx(0.5)
        assert january_python.skill_evidence_coverage == pytest.approx(0.5)
        assert skills.filter((skills.source == "arbeitnow") & (skills.skills_origin == "extracted_from_jd")).count() == 1
        assert skills.filter((skills.source == "archive") & (skills.skills_origin == "extracted_from_jd")).count() == 0
        february_sql = skills.filter(
            (skills.source == "archive") & (skills.occupation == "Data Engineer") &
            (skills.month == "2023-02") & (skills.skill == "sql")
        ).first()
        assert february_sql.skill_job_count == 0
        assert february_sql.occupation_job_count == 1
        assert february_sql.demand_rate == 0
        assert skills.filter((skills.source == "archive") & (skills.month == "2023-03")).count() == 0

        evidence = spark.read.parquet(result["outputs"]["skill_evidence_stats"]["path"])
        no_skill = evidence.filter((evidence.occupation == "Other IT") & (evidence.month == "2023-01")).first()
        assert no_skill.origin_job_count == 1 and no_skill.skill_evidence_jobs == 0

        trends = spark.read.parquet(result["outputs"]["skill_trends"]["path"])
        february = trends.filter((trends.source == "archive") & (trends.month == "2023-02") & (trends.skill == "python")).first()
        april = trends.filter((trends.source == "archive") & (trends.month == "2023-04") & (trends.skill == "python")).first()
        assert february.consecutive_observed_month is True
        assert february.observed_delta_pp == pytest.approx(50)
        assert april.consecutive_observed_month is False
        assert april.observed_delta_pp is None
        february_sql_trend = trends.filter(
            (trends.source == "archive") & (trends.month == "2023-02") & (trends.skill == "sql")
        ).first()
        april_sql_trend = trends.filter(
            (trends.source == "archive") & (trends.month == "2023-04") & (trends.skill == "sql")
        ).first()
        assert february_sql_trend.consecutive_observed_month is True
        assert february_sql_trend.observed_delta_pp == pytest.approx(-50)
        assert april_sql_trend.skill_job_count == 1
        assert april_sql_trend.consecutive_observed_month is False
        assert april_sql_trend.observed_delta_pp is None
    finally:
        spark.stop()

    assert result["outputs"]["market_stats"]["rows"] == 4
    assert not list((tmp_path / "gold").glob(".staging-*"))


def test_rejects_unlocked_or_tampered_input(tmp_path):
    path, checksum, silver_path = _fixture_etl(tmp_path)
    with pytest.raises(ValueError, match="expected ETL manifest SHA-256"):
        load_verified_etl_manifest(path, "")
    report = json.loads(path.read_text(encoding="utf-8"))
    report["input_runs"][0]["status"] = "partial"
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="ETL manifest SHA-256 mismatch"):
        load_verified_etl_manifest(path, checksum)
    checksum = sha256_file(path)
    with pytest.raises(ValueError, match="Partial/scoped"):
        load_verified_etl_manifest(path, checksum)
    (silver_path / "unexpected.txt").write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="silver output checksum mismatch"):
        load_verified_etl_manifest(path, checksum, allow_scoped_inputs=True)


def test_rejects_duplicate_provenance_even_with_matching_file_checksums(tmp_path):
    path, _, _ = _fixture_etl(tmp_path)
    report = json.loads(path.read_text(encoding="utf-8"))
    spark = create_spark_session()
    try:
        provenance = spark.read.parquet(report["outputs"]["provenance"]["path"])
        bad_path = tmp_path / "etl" / "duplicate_provenance"
        provenance.unionByName(provenance.limit(1)).write.parquet(str(bad_path))
    finally:
        spark.stop()
    report["outputs"]["provenance"] = {"path": str(bad_path), **_directory_evidence(bad_path)}
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(AssertionError, match="Duplicate provenance job_id key"):
        run_phase03(path, sha256_file(path), output_root=tmp_path / "gold")
    assert not list((tmp_path / "gold").glob("*/manifest.json"))
