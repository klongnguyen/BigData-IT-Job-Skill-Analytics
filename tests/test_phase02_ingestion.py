"""Regression checks for immutable, auditable Bronze runs."""

import csv
import json

import pytest

from src.common.run_manifest import load_bronze_run, sha256_file
from src.ingestion.fresh_ingestion import ingest_fresh_data
from src.ingestion.historical_ingestion import ingest_historical_data


def _manifest_for_only_run(root):
    runs = list((root / "runs").glob("*/manifest.json"))
    assert len(runs) == 1
    return runs[0], json.loads(runs[0].read_text(encoding="utf-8"))


def test_historical_runs_are_immutable_and_checksummed(tmp_path):
    csv_path = tmp_path / "raw.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["job_title", "job_posted_date", "job_skills"])
        writer.writeheader()
        for index in range(3):
            writer.writerow({"job_title": f"Analyst {index}", "job_posted_date": "2023-01-01",
                             "job_skills": "['Python']"})
    root = tmp_path / "bronze"
    assert ingest_historical_data(batch_size=2, limit=3, raw_csv_path=csv_path, bronze_dir=root) == 3
    first_path, first = _manifest_for_only_run(root)
    assert first["status"] == "partial" and first["total_rows"] == 3
    assert [item["rows"] for item in first["files"]] == [2, 1]
    assert first["input"]["sha256"] == sha256_file(csv_path)
    with pytest.raises(ValueError, match="partial"):
        load_bronze_run(first_path.parent, expected_kind="historical")
    loaded, paths, _ = load_bronze_run(first_path.parent, "historical", allow_partial=True)
    assert loaded["total_rows"] == 3 and len(paths) == 2
    first_records = json.loads(open(paths[0], encoding="utf-8").read())
    assert all(row["source_record_id"] == row["raw_checksum"] for row in first_records)
    original_checksum = sha256_file(first_path)

    assert ingest_historical_data(batch_size=2, limit=1, raw_csv_path=csv_path, bronze_dir=root) == 1
    manifests = list((root / "runs").glob("*/manifest.json"))
    assert len(manifests) == 2
    assert sha256_file(first_path) == original_checksum
    assert sorted(json.loads(path.read_text())["total_rows"] for path in manifests) == [1, 3]
    assert not list((root / "runs").glob(".staging-*"))

    record_path = first_path.parent / first["files"][0]["path"]
    record_path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_bronze_run(first_path.parent, "historical", allow_partial=True)


def test_fresh_partial_source_and_collision_safe_runs(tmp_path):
    sources = (("arbeitnow", "https://example.test/arbeitnow"),
               ("remotive", "https://example.test/remotive"))
    page = {"data": [{"slug": "one", "title": "Data Engineer", "created_at": 1704067200}],
            "links": {"next": None}}

    def fetch(url):
        if "remotive" in url:
            raise OSError("source temporarily unavailable")
        return page

    root = tmp_path / "fresh"
    assert ingest_fresh_data(root, sources, fetch) == 1
    assert ingest_fresh_data(root, sources, fetch) == 1
    manifests = list((root / "runs").glob("*/manifest.json"))
    assert len(manifests) == 2
    for path in manifests:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        assert manifest["status"] == "partial"
        assert manifest["total_rows"] == 1
        assert manifest["sources"][0]["coverage"] == "complete"
        assert manifest["sources"][1]["status"] == "partial"
        assert manifest["sources"][1]["errors"]
        load_bronze_run(path.parent, "fresh", allow_partial=True)


def test_fresh_pagination_and_unproven_coverage(tmp_path):
    sources = (("arbeitnow", "https://example.test/jobs"),)

    def fetch(url):
        if "page=2" in url:
            return {"data": [{"slug": "two", "title": "Engineer"}], "links": {"next": None}}
        return {"data": [{"slug": "one", "title": "Analyst"}],
                "links": {"next": "/jobs?page=2"}}

    root = tmp_path / "paged"
    assert ingest_fresh_data(root, sources, fetch) == 2
    _, manifest = _manifest_for_only_run(root)
    assert manifest["status"] == "complete"
    assert manifest["sources"][0]["pages"] == 2

    scoped = tmp_path / "scoped"
    assert ingest_fresh_data(scoped, sources, lambda _: {"data": [{"slug": "x"}]}) == 1
    _, scoped_manifest = _manifest_for_only_run(scoped)
    assert scoped_manifest["status"] == "partial"
    assert scoped_manifest["sources"][0]["coverage"] == "unknown"


def test_fresh_all_sources_fail_without_success_run(tmp_path):
    root = tmp_path / "fresh"

    def failing_fetch(_):
        raise OSError("offline")

    with pytest.raises(RuntimeError, match="No API returned usable records"):
        ingest_fresh_data(root, (("arbeitnow", "https://example.test/jobs"),), failing_fetch)
    _, manifest = _manifest_for_only_run(root)
    assert manifest["status"] == "failed" and manifest["total_rows"] == 0
    assert manifest["sources"][0]["errors"]
    assert manifest["files"] == []
    assert not list((root / "runs").glob(".staging-*"))
