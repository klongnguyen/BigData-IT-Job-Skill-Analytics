"""Spark fixture for scoped Gold denominators, evidence and observed gaps."""

import json
from datetime import datetime, timezone

import pytest

from src.common.run_manifest import sha256_file
from src.processing.spark_etl import _directory_evidence, create_spark_session
from src.analytics.phase03_gold import (
    ETL_2026_RUN_ID, ETL_2026_SHA256, build_gold_tables,
    load_verified_etl_manifest, run_phase03, verify_2026_silver_authorization,
)


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


def test_market_is_in_every_gold_key_denominator_and_trend():
    spark = create_spark_session()
    try:
        rows = [
            {"job_id": "g1", "market": "GLOBAL", "source": "same_source",
             "normalized_title": "Data Engineer", "posted_at": datetime(2026, 1, 15, tzinfo=timezone.utc),
             "skills": ["python"], "company": "A", "country": "US",
             "work_mode": "Remote", "experience_level": "Mid"},
            {"job_id": "g2", "market": "GLOBAL", "source": "same_source",
             "normalized_title": "Data Engineer", "posted_at": datetime(2026, 3, 15, tzinfo=timezone.utc),
             "skills": ["python"], "company": "B", "country": "US",
             "work_mode": "Remote", "experience_level": "Mid"},
            {"job_id": "f1", "market": "US_FEDERAL", "source": "same_source",
             "normalized_title": "Data Engineer", "posted_at": datetime(2026, 2, 15, tzinfo=timezone.utc),
             "skills": ["sql"], "company": "C", "country": "US",
             "work_mode": "Remote", "experience_level": "Mid"},
            {"job_id": "f2", "market": "US_FEDERAL", "source": "same_source",
             "normalized_title": "Data Engineer", "posted_at": datetime(2026, 3, 15, tzinfo=timezone.utc),
             "skills": ["sql"], "company": "D", "country": "US",
             "work_mode": "Remote", "experience_level": "Mid"},
        ]
        silver = spark.createDataFrame(rows)
        provenance = spark.createDataFrame([
            {"job_id": row["job_id"], "source": row["source"],
             "skills_origin": "source_tags", "taxonomy_version": "v0.2"}
            for row in rows])
        tables = build_gold_tables(silver, provenance, "v0.2")
        for name, keys in {
            "market_stats": ["market", "month", "source"],
            "occupation_stats": ["market", "month", "source", "occupation"],
            "skill_evidence_stats": ["market", "month", "source", "occupation", "skills_origin", "taxonomy_version"],
            "skill_stats": ["market", "month", "source", "occupation", "skills_origin", "taxonomy_version", "skill"],
            "skill_trends": ["market", "month", "source", "occupation", "skills_origin", "taxonomy_version", "skill"],
        }.items():
            frame = tables[name]
            assert frame.count() == frame.select(*keys).distinct().count()
        market = tables["market_stats"].collect()
        assert {(row.market, row.month, row.job_count) for row in market} == {
            ("GLOBAL", "2026-01", 1), ("GLOBAL", "2026-03", 1),
            ("US_FEDERAL", "2026-02", 1), ("US_FEDERAL", "2026-03", 1),
        }
        trends = tables["skill_trends"]
        global_march = trends.filter((trends.market == "GLOBAL") &
                                     (trends.month == "2026-03") & (trends.skill == "python")).first()
        federal_march = trends.filter((trends.market == "US_FEDERAL") &
                                      (trends.month == "2026-03") & (trends.skill == "sql")).first()
        assert global_march.previous_observed_month == "2026-01"
        assert global_march.consecutive_observed_month is False
        assert federal_march.previous_observed_month == "2026-02"
        assert federal_march.consecutive_observed_month is True
        assert trends.filter(trends.month == "2026-04").count() == 0
    finally:
        spark.stop()


def test_2026_authorization_rejects_wrong_sha_and_partial(monkeypatch):
    from pathlib import Path
    from src.analytics import phase03_gold
    from src.analytics.phase03_gold import ROOT, OLD_GOLD_MANIFEST, OLD_GOLD_SHA256
    path = ROOT / "data/manifests/etl" / f"etl_{ETL_2026_RUN_ID}.json"
    report, _ = load_verified_etl_manifest(path, ETL_2026_SHA256, allow_scoped_inputs=True)
    audit, audit_sha = verify_2026_silver_authorization(report, path, ETL_2026_SHA256)
    assert audit["status"] == "passed" and len(audit_sha) == 64
    assert sha256_file(OLD_GOLD_MANIFEST) == OLD_GOLD_SHA256
    with pytest.raises(ValueError, match="exact audited"):
        verify_2026_silver_authorization(report, path, "0" * 64)
    changed = json.loads(json.dumps(report))
    changed["input_runs"][0]["run_id"] = "unexpected_partial"
    with pytest.raises(ValueError, match="Bronze lineage|unauthorized partial"):
        verify_2026_silver_authorization(changed, path, ETL_2026_SHA256)
    actual_evidence = phase03_gold._directory_evidence
    silver_dir = ROOT / "data/silver/jobscope/runs" / ETL_2026_RUN_ID

    def tampered_evidence(directory):
        evidence = actual_evidence(directory)
        if Path(directory).resolve() == silver_dir.resolve():
            return {**evidence, "sha256": "0" * 64}
        return evidence

    monkeypatch.setattr(phase03_gold, "_directory_evidence", tampered_evidence)
    with pytest.raises(ValueError, match="silver output SHA mismatch"):
        verify_2026_silver_authorization(report, path, ETL_2026_SHA256)
    with pytest.raises(ValueError, match="explicit --jobscope-2026"):
        run_phase03(path, ETL_2026_SHA256)
