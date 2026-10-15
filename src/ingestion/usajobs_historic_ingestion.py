"""Backfill USAJOBS federal IT announcements into a separate immutable Bronze run."""

import argparse
import json
import time
import urllib.parse
import uuid
from datetime import date
from pathlib import Path

from src.common.run_manifest import discard_stage, file_entry, publish_run, start_run, utc_now
from src.ingestion.fresh_ingestion import _checksum, _fetch


BASE_DIR = Path(__file__).resolve().parents[2]
BRONZE_ROOT = BASE_DIR / "data" / "bronze" / "us_federal" / "historic"
API_ROOT = "https://data.usajobs.gov/api/historicjoa"


def _first_url(start_date, end_date, position_series):
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if start.year != 2026 or end.year != 2026 or start > end:
        raise ValueError("Choose an ordered date range inside 2026")
    if not position_series.isdigit():
        raise ValueError("Position series must contain digits only")
    query = urllib.parse.urlencode({
        "PositionSeries": position_series,
        "StartPositionOpenDate": start.strftime("%m-%d-%Y"),
        "EndPositionOpenDate": end.strftime("%m-%d-%Y"),
    })
    return f"{API_ROOT}?{query}"


def _next_url(payload, current_url):
    paging = payload.get("paging") or {}
    next_value = paging.get("next")
    if not next_value:
        return None
    next_url = urllib.parse.urljoin(current_url, str(next_value))
    parsed = urllib.parse.urlparse(next_url)
    if parsed.scheme != "https" or parsed.netloc != "data.usajobs.gov" or parsed.path.lower() != "/api/historicjoa":
        raise ValueError("USAJOBS pagination URL left the historic HTTPS endpoint")
    return next_url


def _normalize(item, ingestion_id, collected_at, start, end):
    source_id = item.get("usajobsControlNumber")
    posted_raw = item.get("positionOpenDate")
    if source_id is None or not str(source_id).strip() or not posted_raw:
        raise ValueError("missing USAJOBS ID or positionOpenDate")
    posted = date.fromisoformat(str(posted_raw)[:10])
    if not start <= posted <= end:
        return None
    raw_locations = item.get("positionlocations") or item.get("positionLocations") or []
    locations = [place for place in raw_locations if isinstance(place, dict)]
    location_names = list(dict.fromkeys(
        ", ".join(str(place[key]).strip() for key in (
            "positionLocationCity", "positionLocationState", "positionLocationCountry"
        ) if place.get(key)) for place in locations
    ))
    location = "; ".join(name for name in location_names if name) or None
    countries = [str(place.get("positionLocationCountry") or "").strip() for place in locations]
    country = countries[0] if countries and all(value == countries[0] for value in countries) else None
    telework_value = str(item.get("teleworkEligible") or "").strip().upper()
    return {
        "ingestion_id": ingestion_id,
        "market": "US_FEDERAL",
        "source": "usajobs_historic",
        "source_record_id": str(source_id),
        "source_url": item.get("url") or None,
        "raw_checksum": _checksum(item),
        "collected_at": collected_at,
        "posted_at": posted.isoformat(),
        "title": (item.get("positionTitle") or "").strip(),
        "company": (item.get("hiringAgencyName") or "").strip() or None,
        "location": location,
        "locations_raw": locations,
        "country": country,
        "remote": None,
        "telework_eligible": {"Y": True, "N": False}.get(telework_value),
        "description": None,
        "tags": [],
        "job_types": [item["workSchedule"]] if item.get("workSchedule") else [],
        "salary_raw": None,
        "currency": None,
    }


def ingest_usajobs_historic(start_date, end_date, bronze_dir=BRONZE_ROOT,
                            position_series="2210", max_pages=50, fetch=_fetch,
                            request_delay_seconds=0.0, sleep=time.sleep):
    if max_pages <= 0 or request_delay_seconds < 0:
        raise ValueError("max_pages must be positive and request delay nonnegative")
    first_url = _first_url(start_date, end_date, position_series)
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    started_at = utc_now()
    run_id, stage, final = start_run(bronze_dir)
    ingestion_id = str(uuid.uuid4())
    collected_at = utc_now()
    result = {"source": "usajobs_historic", "requested_url": first_url,
              "market_scope": "US federal jobs", "position_series": position_series,
              "start_date": start_date, "end_date": end_date,
              "rows": 0, "raw_rows": 0, "pages": 0, "duplicate_rows": 0,
              "skipped_rows": 0, "errors": [], "coverage": "unknown"}
    jobs, seen_urls, seen_ids = [], set(), set()
    current_url = first_url
    try:
        while current_url and result["pages"] < max_pages:
            if current_url in seen_urls:
                result["errors"].append("Pagination URL repeated")
                break
            seen_urls.add(current_url)
            try:
                payload = fetch(current_url)
                items = payload.get("data")
                if not isinstance(items, list):
                    raise ValueError("API data is not an array")
                result["pages"] += 1
                result["raw_rows"] += len(items)
                for item in items:
                    try:
                        job = _normalize(item, ingestion_id, collected_at, start, end)
                        if job is None:
                            result["skipped_rows"] += 1
                        elif job["source_record_id"] in seen_ids:
                            result["duplicate_rows"] += 1
                        else:
                            seen_ids.add(job["source_record_id"])
                            jobs.append(job)
                            result["rows"] += 1
                    except (KeyError, TypeError, ValueError) as error:
                        result["skipped_rows"] += 1
                        result["errors"].append(f"Invalid record: {error}")
                current_url = _next_url(payload, current_url)
                result["coverage"] = "in_progress" if current_url else "complete"
                if current_url and request_delay_seconds:
                    sleep(request_delay_seconds)
            except Exception as error:
                result["errors"].append(f"Fetch/page error: {error}")
                break
        if current_url and result["pages"] >= max_pages:
            result["coverage"] = "page_limit"
        result["status"] = "complete" if not result["errors"] and result["coverage"] == "complete" else "partial"
        manifest = {
            "run_id": run_id, "kind": "fresh", "source": "usajobs_historic",
            "collection_mode": "historical_backfill", "market_scope": "US federal jobs",
            "status": result["status"] if jobs else "failed",
            "started_at": started_at, "finished_at": utc_now(),
            "ingestion_id": ingestion_id, "sources": [result],
            "files": [], "total_rows": len(jobs),
        }
        if jobs:
            path = stage / "records" / "usajobs_historic_batch_001.json"
            with path.open("x", encoding="utf-8") as stream:
                json.dump(jobs, stream, ensure_ascii=False, separators=(",", ":"))
            manifest["files"] = [file_entry(stage, path, len(jobs))]
        manifest_path = publish_run(stage, final, manifest)
        if not jobs:
            raise RuntimeError(f"USAJOBS returned no usable records; failed run: {manifest_path}")
    except Exception:
        discard_stage(stage)
        raise
    print(f"[USAJOBS Historic] {len(jobs)} rows; {manifest['status']} run: {manifest_path}")
    return len(jobs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True, help="YYYY-MM-DD in 2026")
    parser.add_argument("--end-date", required=True, help="YYYY-MM-DD in 2026")
    parser.add_argument("--bronze-dir", default=BRONZE_ROOT)
    parser.add_argument("--position-series", default="2210")
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--request-delay-seconds", type=float, default=1.0)
    args = parser.parse_args()
    ingest_usajobs_historic(args.start_date, args.end_date, args.bronze_dir,
                            args.position_series, args.max_pages,
                            request_delay_seconds=args.request_delay_seconds)
