"""Capture a fresh public API snapshot into Bronze with verified HTTPS."""

import hashlib
import json
import os
import urllib.request
import uuid
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_FRESH_DIR = os.path.join(BASE_DIR, "data", "bronze", "global", "fresh")


def _fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "BigDataJobSkillAnalytics/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _checksum(record):
    raw = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ingest_fresh_data():
    ingestion_id = str(uuid.uuid4())
    collected_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    jobs = []
    errors = []
    sources = (
        ("arbeitnow", "https://www.arbeitnow.com/api/job-board-api"),
        ("remotive", "https://remotive.com/api/remote-jobs?category=software-dev&limit=150"),
    )

    for source, url in sources:
        try:
            payload = _fetch(url)
            items = payload.get("data", []) if source == "arbeitnow" else payload.get("jobs", [])
            for item in items:
                source_id = item.get("slug") if source == "arbeitnow" else item.get("id")
                if source_id is None:
                    continue
                if source == "arbeitnow":
                    epoch = item.get("created_at")
                    posted_at = datetime.fromtimestamp(epoch, timezone.utc).isoformat().replace("+00:00", "Z") if epoch else None
                    location = (item.get("location") or "").strip() or None
                    remote = bool(item.get("remote", False))
                    job_types = item.get("job_types") or []
                    salary_raw = None
                else:
                    posted_at = item.get("publication_date") or None
                    location = (item.get("candidate_required_location") or "").strip() or None
                    remote = True
                    job_types = [item["job_type"]] if item.get("job_type") else []
                    salary_raw = item.get("salary") or None
                jobs.append({
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
                })
        except Exception as exc:
            errors.append(f"{source}: {exc}")

    if not jobs:
        raise RuntimeError("No API returned usable records; no empty success batch was written. " + "; ".join(errors))

    os.makedirs(BRONZE_FRESH_DIR, exist_ok=True)
    output_file = os.path.join(BRONZE_FRESH_DIR, f"fresh_batch_{timestamp_str}.json")
    with open(output_file, "w", encoding="utf-8") as target:
        json.dump(jobs, target, indent=2, ensure_ascii=False)
    print(f"[Fresh Ingestion] Saved {len(jobs)} records to {output_file}")
    if errors:
        print("Some sources failed: " + "; ".join(errors))
    return len(jobs)


if __name__ == "__main__":
    ingest_fresh_data()
