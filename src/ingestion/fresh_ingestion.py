"""Capture public API snapshots into an immutable, source-audited Bronze run."""

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.common.run_manifest import discard_stage, file_entry, publish_run, start_run, utc_now


BASE_DIR = Path(__file__).resolve().parents[2]
BRONZE_FRESH_DIR = BASE_DIR / "data" / "bronze" / "global" / "fresh"
DEFAULT_SOURCES = (
    ("arbeitnow", "https://www.arbeitnow.com/api/job-board-api"),
    ("remotive", "https://remotive.com/api/remote-jobs?category=software-dev&limit=150"),
)


def _fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "BigDataJobSkillAnalytics/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _checksum(record):
    raw = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _next_page(payload, current_url, first_url):
    """Return (next URL, coverage) without assuming an undocumented final page."""
    links = payload.get("links")
    if isinstance(links, dict) and "next" in links:
        next_value = links["next"]
    elif "next" in payload:
        next_value = payload["next"]
    else:
        return None, "scoped" if "limit=" in first_url else "unknown"
    if not next_value:
        return None, "complete"
    next_url = urllib.parse.urljoin(current_url, str(next_value))
    current = urllib.parse.urlparse(first_url)
    candidate = urllib.parse.urlparse(next_url)
    if candidate.scheme != "https" or candidate.netloc != current.netloc:
        raise ValueError("Pagination URL must stay on the source HTTPS host")
    return next_url, "in_progress"


def _normalize_job(source, item, ingestion_id, collected_at):
    source_id = item.get("slug") if source == "arbeitnow" else item.get("id")
    if source_id is None or not str(source_id).strip():
        return None
    if source == "arbeitnow":
        epoch = item.get("created_at")
        posted_at = (datetime.fromtimestamp(int(epoch), timezone.utc).isoformat()
                     .replace("+00:00", "Z")) if epoch else None
        location = (item.get("location") or "").strip() or None
        remote = bool(item.get("remote", False))
        job_types = item.get("job_types") or []
        salary_raw = None
    elif source == "remotive":
        posted_at = item.get("publication_date") or None
        location = (item.get("candidate_required_location") or "").strip() or None
        remote = True
        job_types = [item["job_type"]] if item.get("job_type") else []
        salary_raw = item.get("salary") or None
    else:
        raise ValueError(f"Unknown source: {source}")
    return {
        "ingestion_id": ingestion_id,
        "market": "GLOBAL",
        "source": source,
        "source_record_id": str(source_id),
        "source_url": item.get("url") or None,
        "raw_checksum": _checksum(item),
        "collected_at": collected_at,
        "posted_at": posted_at,
        "title": (item.get("title") or "").strip(),
        "company": (item.get("company_name") or "").strip() or None,
        "location": location,
        "country": None,
        "remote": remote,
        "description": (item.get("description") or "").strip() or None,
        "tags": item.get("tags") or [],
        "job_types": job_types,
        "salary_raw": salary_raw,
        "currency": None,
    }


def ingest_fresh_data(bronze_dir=BRONZE_FRESH_DIR, sources=DEFAULT_SOURCES,
                      fetch=_fetch, max_pages=100):
    if max_pages <= 0:
        raise ValueError("max_pages must be positive")
    started_at = utc_now()
    run_id, stage, final = start_run(bronze_dir)
    ingestion_id = str(uuid.uuid4())
    collected_at = utc_now()
    jobs = []
    source_results = []
    try:
        for source, first_url in sources:
            result = {"source": source, "requested_url": first_url, "rows": 0,
                      "pages": 0, "skipped_rows": 0, "errors": [], "coverage": "unknown"}
            seen_urls = set()
            current_url = first_url
            while current_url and result["pages"] < max_pages:
                if current_url in seen_urls:
                    result["errors"].append("Pagination URL repeated")
                    break
                seen_urls.add(current_url)
                try:
                    payload = fetch(current_url)
                    items = payload.get("data", []) if source == "arbeitnow" else payload.get("jobs", [])
                    if not isinstance(items, list):
                        raise ValueError("API record list is not an array")
                    result["pages"] += 1
                    for item in items:
                        try:
                            job = _normalize_job(source, item, ingestion_id, collected_at)
                            if job is None:
                                result["skipped_rows"] += 1
                            else:
                                jobs.append(job)
                                result["rows"] += 1
                        except (KeyError, TypeError, ValueError, OverflowError) as error:
                            result["skipped_rows"] += 1
                            result["errors"].append(f"Invalid record: {error}")
                    current_url, result["coverage"] = _next_page(payload, current_url, first_url)
                except Exception as error:
                    result["errors"].append(f"Fetch/page error: {error}")
                    break
            if current_url and result["pages"] >= max_pages:
                result["coverage"] = "page_limit"
            result["status"] = ("complete" if not result["errors"] and
                                result["coverage"] == "complete" else "partial")
            source_results.append(result)

        if not jobs:
            publish_run(stage, final, {
                "run_id": run_id,
                "kind": "fresh",
                "source": "public_api_snapshot",
                "status": "failed",
                "started_at": started_at,
                "finished_at": utc_now(),
                "ingestion_id": ingestion_id,
                "sources": source_results,
                "files": [],
                "total_rows": 0,
            })
            raise RuntimeError("No API returned usable records; a failed run was recorded")
        path = stage / "records" / "fresh_batch_001.json"
        with path.open("x", encoding="utf-8") as stream:
            json.dump(jobs, stream, indent=2, ensure_ascii=False)
        manifest = {
            "run_id": run_id,
            "kind": "fresh",
            "source": "public_api_snapshot",
            "status": "complete" if all(item["status"] == "complete" for item in source_results) else "partial",
            "started_at": started_at,
            "finished_at": utc_now(),
            "ingestion_id": ingestion_id,
            "sources": source_results,
            "files": [file_entry(stage, path, len(jobs))],
            "total_rows": len(jobs),
        }
        manifest_path = publish_run(stage, final, manifest)
    except Exception:
        discard_stage(stage)
        raise
    print(f"[Fresh Ingestion] {len(jobs)} rows; {manifest['status']} run: {manifest_path}")
    return len(jobs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bronze-dir", default=BRONZE_FRESH_DIR)
    parser.add_argument("--max-pages", type=int, default=100)
    args = parser.parse_args()
    ingest_fresh_data(bronze_dir=args.bronze_dir, max_pages=args.max_pages)
