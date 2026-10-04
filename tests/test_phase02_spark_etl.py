"""Small end-to-end Spark fixture for identity, quarantine and provenance."""

import json

import pytest

from src.common.run_manifest import file_entry
from src.processing.spark_etl import create_spark_session, run_etl


def _bronze_run(root, kind, rows):
    run_id = f"test_{kind}"
    run_dir = root / kind / "runs" / run_id
    records = run_dir / "records"
    records.mkdir(parents=True)
    path = records / "batch_001.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    manifest = {
        "schema_version": 1, "run_id": run_id, "kind": kind,
        "status": "complete", "total_rows": len(rows),
        "files": [file_entry(run_dir, path, len(rows))],
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return run_dir


@pytest.fixture(scope="module")
def spark_available():
    try:
        spark = create_spark_session()
    except Exception as error:
        pytest.skip(f"SparkContext cannot start in this environment: {type(error).__name__}")
    else:
        spark.stop()


def test_identity_first_etl_and_provenance(tmp_path, spark_available):
    hist = _bronze_run(tmp_path / "bronze", "historical", [{
        "source": "kaggle_historical_archive", "source_record_id": "archive-row",
        "raw_checksum": "archive-checksum", "job_title": "Data Analyst",
        "company_name": "Historical Co", "job_posted_date": "2023-01-01",
        "job_skills": "['Python']", "collected_at": "2026-09-01T00:00:00Z",
    }])
    fresh = _bronze_run(tmp_path / "bronze", "fresh", [
        {"source": "arbeitnow", "source_record_id": "job-A", "raw_checksum": "a-old",
         "title": "Old Title", "company": "Same Co", "location": "Remote",
         "posted_at": "2026-09-01T00:00:00Z", "collected_at": "2026-09-01T00:00:00Z",
         "description": "Python", "tags": []},
        {"source": "arbeitnow", "source_record_id": "job-A", "raw_checksum": "a-new",
         "title": "Data Engineer", "company": "Same Co", "location": "Remote",
         "posted_at": "2026-09-01T00:00:00Z", "collected_at": "2026-09-02T00:00:00Z",
         "description": "Python", "tags": []},
        {"source": "arbeitnow", "source_record_id": "job-B", "raw_checksum": "b",
         "title": "Data Engineer", "company": "Same Co", "location": "Remote",
         "posted_at": "2026-09-01T00:00:00Z", "collected_at": "2026-09-02T00:00:00Z",
         "description": "Python", "tags": []},
        {"source": "arbeitnow", "source_record_id": "job-C", "raw_checksum": "c",
         "title": "Data Engineer", "company": "Same Co", "location": "Remote",
         "posted_at": "not-a-date", "collected_at": "2026-09-02T00:00:00Z",
         "description": "Python", "tags": []},
        {"source": "arbeitnow", "source_record_id": "job-D", "raw_checksum": "same-payload",
         "title": "Platform Engineer", "company": "Same Co", "location": "Remote",
         "posted_at": "2026-09-01T00:00:00Z", "collected_at": "2026-09-02T00:00:00Z",
         "description": "Python", "tags": [], "ingestion_id": "ing-z"},
        {"source": "arbeitnow", "source_record_id": "job-D", "raw_checksum": "same-payload",
         "title": "Platform Engineer", "company": "Same Co", "location": "Remote",
         "posted_at": "2026-09-01T00:00:00Z", "collected_at": "2026-09-02T00:00:00Z",
         "description": "Python", "tags": [], "ingestion_id": "ing-a"},
    ])
    result = run_etl(
        historical_run=hist, fresh_run=fresh,
        silver_dir=tmp_path / "out" / "silver",
        provenance_dir=tmp_path / "out" / "provenance",
        quarantine_dir=tmp_path / "out" / "quarantine",
        manifest_dir=tmp_path / "out" / "manifests",
    )
    metrics = result["metrics"]
    assert metrics["input_rows"] == 7
    assert metrics["quarantine_rows"] == 1
    assert metrics["identity_duplicates_removed"] == 2
    assert metrics["silver_rows"] == metrics["provenance_rows"] == 4
    assert metrics["unique_job_ids"] == 4

    spark = create_spark_session()
    try:
        silver = spark.read.parquet(str(tmp_path / "out" / "silver"))
        provenance = spark.read.parquet(str(tmp_path / "out" / "provenance"))
        quarantine = spark.read.parquet(str(tmp_path / "out" / "quarantine"))
        assert silver.select("job_id").distinct().count() == silver.count() == 4
        assert silver.filter(silver.title == "Old Title").count() == 0
        assert silver.filter(silver.title == "Data Engineer").count() == 2
        assert silver.join(provenance, "job_id", "left_anti").count() == 0
        assert provenance.join(silver, "job_id", "left_anti").count() == 0
        tie_winner = provenance.filter(provenance.source_record_id == "job-D")
        assert [row.ingestion_id for row in tie_winner.select("ingestion_id").collect()] == ["ing-a"]
        assert quarantine.count() == 1
    finally:
        spark.stop()

    again = run_etl(
        historical_run=hist, fresh_run=fresh,
        silver_dir=tmp_path / "second" / "silver",
        provenance_dir=tmp_path / "second" / "provenance",
        quarantine_dir=tmp_path / "second" / "quarantine",
        manifest_dir=tmp_path / "second" / "manifests",
    )
    assert again["metrics"] == metrics
    spark = create_spark_session()
    try:
        provenance = spark.read.parquet(str(tmp_path / "second" / "provenance"))
        tie_winner = provenance.filter(provenance.source_record_id == "job-D")
        assert [row.ingestion_id for row in tie_winner.select("ingestion_id").collect()] == ["ing-a"]
    finally:
        spark.stop()


def test_rejects_implicit_bronze_scan(tmp_path):
    with pytest.raises(ValueError, match="implicit Bronze scans"):
        run_etl(silver_dir=tmp_path / "silver")


def test_rejects_forged_bronze_row_count_before_promotion(tmp_path):
    hist = _bronze_run(tmp_path / "bronze", "historical", [{"x": 1}, {"x": 2}])
    manifest_path = hist / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["rows"] = 1
    manifest["total_rows"] = 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    silver = tmp_path / "out" / "silver"
    with pytest.raises(ValueError, match="Bronze record row count mismatch"):
        run_etl(
            historical_run=hist,
            silver_dir=silver,
            provenance_dir=tmp_path / "out" / "provenance",
            quarantine_dir=tmp_path / "out" / "quarantine",
            manifest_dir=tmp_path / "out" / "manifests",
        )
    assert not silver.exists()
    assert not list((tmp_path / "out").rglob("etl_*.json"))
