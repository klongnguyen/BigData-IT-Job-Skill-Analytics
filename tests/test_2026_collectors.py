"""Source contracts for 2026 live snapshots and federal historical backfill."""

import io
import json
import urllib.error

import pytest

from src.common.run_manifest import load_bronze_run, sha256_file
from src.collection.audit_2026_bronze import audit_runs
from src.ingestion.fresh_ingestion import DEFAULT_SOURCES, _fetch, ingest_fresh_data
from src.ingestion.usajobs_historic_ingestion import _normalize, ingest_usajobs_historic


def _only_run(root):
    manifests = list((root / "runs").glob("*/manifest.json"))
    assert len(manifests) == 1
    path = manifests[0]
    return path, json.loads(path.read_text(encoding="utf-8"))


def test_fresh_uses_broad_remotive_and_source_posted_at(tmp_path):
    assert DEFAULT_SOURCES[1][1] == "https://remotive.com/api/remote-jobs"

    def fetch(url):
        if "arbeitnow" in url:
            return {"data": [{"slug": "a", "title": "Data Engineer", "created_at": 1792022400}],
                    "links": {"next": None}}
        return {"jobs": [{"id": 42, "title": "DevOps Engineer",
                          "publication_date": "2026-10-14T10:00:00", "url": "https://remotive.com/job/42"}]}

    root = tmp_path / "fresh"
    assert ingest_fresh_data(root, fetch=fetch) == 2
    manifest_path, manifest = _only_run(root)
    loaded, paths, _ = load_bronze_run(manifest_path.parent, "fresh", allow_partial=True)
    records = json.loads(open(paths[0], encoding="utf-8").read())
    assert loaded["status"] == "partial"  # Remotive has no proof of full historical coverage.
    by_source = {row["source"]: row for row in records}
    assert by_source["arbeitnow"]["posted_at"] == "2026-10-15T00:00:00Z"
    assert by_source["remotive"]["posted_at"] == "2026-10-14T10:00:00"
    assert all(row["posted_at"] != row["collected_at"] for row in records)


def test_fetch_retries_429_with_retry_after(monkeypatch):
    attempts, delays = [], []

    def urlopen(_request, timeout):
        attempts.append(timeout)
        if len(attempts) == 1:
            raise urllib.error.HTTPError("https://example.test", 429, "rate limit",
                                         {"Retry-After": "3"}, None)
        return io.BytesIO(b'{"data": []}')

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    assert _fetch("https://example.test", sleep=delays.append) == {"data": []}
    assert attempts == [30, 30] and delays == [3.0]


def test_fresh_deduplicates_source_identity_across_pages(tmp_path):
    def fetch(url):
        return {"data": [{"slug": "same-id", "title": "Data Engineer",
                          "created_at": 1792022400}],
                "links": {"next": "?page=2" if "page=2" not in url else None}}

    root = tmp_path / "fresh"
    assert ingest_fresh_data(root, sources=(DEFAULT_SOURCES[0],), fetch=fetch) == 1
    _, manifest = _only_run(root)
    assert manifest["status"] == "complete"
    assert manifest["sources"][0]["pages"] == 2
    assert manifest["sources"][0]["duplicate_rows"] == 1


def test_usajobs_backfill_paginates_preserves_scope_and_immutable_runs(tmp_path):
    urls = []

    def fetch(url):
        urls.append(url)
        if "continuationtoken=" in url:
            return {"paging": {"next": None}, "data": [
                {"usajobsControlNumber": 2, "positionOpenDate": "2026-02-04",
                 "positionTitle": "IT Specialist", "hiringAgencyName": "Agency B"}]}
        return {"paging": {"next": "/api/historicjoa?continuationtoken=abc"}, "data": [
            {"usajobsControlNumber": 1, "positionOpenDate": "2026-02-03",
             "positionTitle": "IT Specialist", "hiringAgencyName": "Agency A",
                 "teleworkEligible": "Y",
                 "positionlocations": [{"positionLocationCity": "Denver",
                                        "positionLocationCountry": "United States"},
                                       {"positionLocationCity": "Boulder",
                                        "positionLocationCountry": "United States"}]}]}

    root = tmp_path / "federal"
    assert ingest_usajobs_historic("2026-02-01", "2026-02-28", root, fetch=fetch) == 2
    first_path, manifest = _only_run(root)
    assert manifest["status"] == "complete" and manifest["market_scope"] == "US federal jobs"
    assert manifest["sources"][0]["pages"] == 2
    assert manifest["sources"][0]["raw_rows"] == 2
    assert "StartPositionOpenDate=02-01-2026" in urls[0]
    assert urls[1].startswith("https://data.usajobs.gov/api/historicjoa?continuationtoken=")
    _, paths, _ = load_bronze_run(first_path.parent, "fresh")
    records = json.loads(open(paths[0], encoding="utf-8").read())
    assert [row["source_record_id"] for row in records] == ["1", "2"]
    assert [row["posted_at"] for row in records] == ["2026-02-03", "2026-02-04"]
    assert all(row["market"] == "US_FEDERAL" and row["description"] is None for row in records)
    assert records[0]["location"] == "Denver, United States; Boulder, United States"
    assert len(records[0]["locations_raw"]) == 2
    assert records[0]["country"] == "United States"
    assert records[0]["telework_eligible"] is True
    assert records[0]["remote"] is None  # Telework eligibility is not a RemoteIndicator.
    original_sha = sha256_file(first_path)
    assert ingest_usajobs_historic("2026-02-01", "2026-02-28", root, fetch=fetch) == 2
    assert len(list((root / "runs").glob("*/manifest.json"))) == 2
    assert sha256_file(first_path) == original_sha


def test_usajobs_page_cap_and_invalid_date_are_not_complete(tmp_path):
    with pytest.raises(ValueError, match="inside 2026"):
        ingest_usajobs_historic("2025-01-01", "2026-02-01", tmp_path)

    root = tmp_path / "capped"
    response = {"paging": {"next": "/api/historicjoa?continuationtoken=next"},
                "data": [{"usajobsControlNumber": 3, "positionOpenDate": "2026-01-04",
                          "positionTitle": "IT Specialist"}]}
    assert ingest_usajobs_historic("2026-01-01", "2026-01-31", root,
                                   max_pages=1, fetch=lambda _: response) == 1
    _, manifest = _only_run(root)
    assert manifest["status"] == "partial"
    assert manifest["sources"][0]["coverage"] == "page_limit"


def test_usajobs_mixed_location_countries_remain_unknown():
    from datetime import date

    item = {"usajobsControlNumber": 9, "positionOpenDate": "2026-03-02",
            "positionTitle": "IT Specialist", "teleworkEligible": "Y",
            "positionlocations": [
                {"positionLocationCity": "Washington", "positionLocationCountry": "United States"},
                {"positionLocationCity": "Ottawa", "positionLocationCountry": "Canada"},
            ]}
    row = _normalize(item, "run", "2026-03-03T00:00:00Z",
                     date(2026, 3, 1), date(2026, 3, 3))
    assert row["country"] is None
    assert row["location"] == "Washington, United States; Ottawa, Canada"
    assert row["remote"] is None and row["telework_eligible"] is True


def test_2026_audit_dedups_snapshots_without_zero_filling(tmp_path):
    root = tmp_path / "federal"
    response = {"paging": {"next": None},
                "data": [{"usajobsControlNumber": 4, "positionOpenDate": "2026-02-04",
                          "positionTitle": "Data Engineer"}]}
    for _ in range(2):
        assert ingest_usajobs_historic("2026-02-01", "2026-02-28", root,
                                       fetch=lambda _: response) == 1
    runs = [path.parent for path in (root / "runs").glob("*/manifest.json")]
    audit = audit_runs(runs, "2026-03")
    assert audit["raw_rows"] == 2
    assert audit["unique_source_records"] == 1
    assert audit["duplicate_source_records_removed"] == 1
    assert audit["source_month_counts"] == [
        {"source": "usajobs_historic", "market": "US_FEDERAL", "month": "2026-02", "jobs": 1}
    ]
    assert audit["months_without_observed_postings"]["usajobs_historic"] == ["2026-01", "2026-03"]


def test_2026_audit_exposes_missing_federal_window(tmp_path):
    root = tmp_path / "federal"
    for day in ("2026-02-01", "2026-02-03"):
        item = {"usajobsControlNumber": day, "positionOpenDate": day,
                "positionTitle": "Data Engineer"}
        ingest_usajobs_historic(day, day, root,
                                fetch=lambda _, item=item: {"paging": {"next": None}, "data": [item]})
    runs = [path.parent for path in (root / "runs").glob("*/manifest.json")]
    coverage = audit_runs(runs, "2026-02")["us_federal_window_coverage"]
    assert coverage["all_windows_complete"] is True
    assert coverage["seams"] == [{"previous_end": "2026-02-01",
                                   "next_start": "2026-02-03", "kind": "gap"}]
