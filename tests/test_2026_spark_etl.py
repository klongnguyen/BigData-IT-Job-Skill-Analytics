"""Small Spark integration fixture for multi-run lineage and scope accounting."""

import json

import pytest

from src.common.run_manifest import file_entry, sha256_file
from src.processing import spark_etl
from src.processing.input_selection import PARTIAL_RUN_ID


def _record(source, source_id, title, market="GLOBAL", posted="2026-10-01T00:00:00Z"):
    return {
        "source": source, "source_record_id": source_id, "title": title,
        "company": "Fixture Co", "market": market, "posted_at": posted,
        "collected_at": "2026-10-15T00:00:00Z", "raw_checksum": f"sha-{source_id}",
        "ingestion_id": f"ing-{source_id}", "description": "Python SQL", "tags": [],
    }


def _run(root, run_id, source, rows, status="complete"):
    directory = root / "bronze" / "runs" / run_id
    records = directory / "records"
    records.mkdir(parents=True)
    batch = records / "batch_001.json"
    batch.write_text(json.dumps(rows), encoding="utf-8")
    manifest = {
        "schema_version": 1, "run_id": run_id, "kind": "fresh", "source": source,
        "status": status, "total_rows": len(rows),
        "files": [file_entry(directory, batch, len(rows))],
    }
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return {
        "kind": "fresh", "run_id": run_id, "status": status, "rows": len(rows),
        "source": source, "market_scope": "US federal jobs" if source == "usajobs_historic" else None,
        "manifest_path": str(manifest_path), "manifest_sha256": sha256_file(manifest_path),
        "files": [str(batch)], "sources": [],
    }


@pytest.fixture(scope="module")
def spark_available():
    try:
        spark = spark_etl.create_spark_session()
    except Exception as error:
        pytest.skip(f"SparkContext cannot start in this environment: {type(error).__name__}")
    else:
        spark.stop()


def test_multi_run_lineage_scope_and_old_artifacts_immutable(tmp_path, monkeypatch, spark_available):
    partial_rows = [_record("arbeitnow", "A", "Data Engineer")] + [
        _record("remotive", f"R{i}", "Sales Manager" if i == 0 else "Data Analyst")
        for i in range(15)
    ]
    partial = _run(tmp_path, PARTIAL_RUN_ID, "public_api_snapshot", partial_rows, "partial")
    complete = _run(tmp_path, "complete_ar", "public_api_snapshot", [
        _record("arbeitnow", "A", "Data Engineer"),
        _record("arbeitnow", "B", "Sales Manager"),
        _record("arbeitnow", "C", "Backend Developer"),
        _record("arbeitnow", "D", "Data Scientist", posted="not-a-date"),
        _record("arbeitnow", "E", "Systems Engineer"),
    ])
    federal = _run(tmp_path, "federal_2210", "usajobs_historic", [
        _record("usajobs_historic", "F1", "IT Specialist", "US_FEDERAL"),
        _record("usajobs_historic", "F2", "Data Analyst", "US_FEDERAL"),
    ])
    selection = tmp_path / "selection.json"
    selection.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(spark_etl, "load_input_selection",
                        lambda *_: ([partial, complete, federal], {}))
    old_gold = tmp_path / "old_gold" / "manifest.json"
    old_gold.parent.mkdir()
    old_gold.write_text('{"run_id":"old"}', encoding="utf-8")
    old_hash = sha256_file(old_gold)
    old_silver = tmp_path / "old_silver" / "part-0000.parquet"
    old_silver.parent.mkdir()
    old_silver.write_bytes(b"immutable old Silver fixture")
    old_silver_hash = sha256_file(old_silver)
    out = tmp_path / "new"
    result = spark_etl.run_etl(
        input_selection=selection, input_selection_sha256=sha256_file(selection),
        silver_dir=out / "silver", provenance_dir=out / "provenance",
        quarantine_dir=out / "quarantine", scope_excluded_dir=out / "scope_excluded",
        scope_unresolved_dir=out / "scope_unresolved",
        manifest_dir=out / "manifests",
    )
    metrics = result["metrics"]
    assert {key: metrics[key] for key in (
        "input_rows", "valid_rows", "quarantine_rows", "identity_duplicates_removed",
        "unique_survivors", "silver_rows", "scope_excluded_rows",
        "scope_unresolved_rows", "provenance_rows",
    )} == {
        "input_rows": 23, "valid_rows": 22, "quarantine_rows": 1,
        "identity_duplicates_removed": 1, "unique_survivors": 21,
        "silver_rows": 18, "scope_excluded_rows": 2,
        "scope_unresolved_rows": 1, "provenance_rows": 18,
    }
    assert sha256_file(old_gold) == old_hash
    assert sha256_file(old_silver) == old_silver_hash
    assert {row["source"] for row in metrics["source_market_occupation_month"]} == {
        "arbeitnow", "remotive", "usajobs_historic",
    }
    assert {row["market"] for row in metrics["source_market_occupation_month"]} == {
        "GLOBAL", "US_FEDERAL",
    }
    spark = spark_etl.create_spark_session()
    try:
        provenance = spark.read.parquet(str(out / "provenance"))
        excluded = spark.read.parquet(str(out / "scope_excluded"))
        unresolved = spark.read.parquet(str(out / "scope_unresolved"))
        selected_a = provenance.filter(provenance.source_record_id == "A").first()
        assert selected_a.survivor_run_id == "complete_ar"
        assert selected_a.survivor_manifest_sha256 == complete["manifest_sha256"]
        assert {(item.input_run_id, item.input_manifest_sha256, item.selected_survivor)
                for item in selected_a.input_lineage} == {
            (PARTIAL_RUN_ID, partial["manifest_sha256"], False),
            ("complete_ar", complete["manifest_sha256"], True),
        }
        assert excluded.count() == 2
        assert unresolved.count() == 1
        assert unresolved.first().source_record_id == "E"
        assert unresolved.first().input_lineage
        assert excluded.filter(excluded.source_record_id == "B").first().input_lineage
        remotive = provenance.filter(provenance.source == "remotive").collect()
        assert len(remotive) == 14
        assert all(row.survivor_run_id == PARTIAL_RUN_ID and
                   row.survivor_manifest_sha256 == partial["manifest_sha256"]
                   for row in remotive)
        assert excluded.filter(excluded.source_record_id == "R0").first().survivor_run_id == PARTIAL_RUN_ID
    finally:
        spark.stop()
