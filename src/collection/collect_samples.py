"""Build a real 2023 historical sample and optionally capture live API samples.

Historical records are selected from the checked-in raw archive and retain its
source columns. Synthetic fixtures live under data/fixtures and are not used by
this collector or the feasibility metrics.
"""

import csv
import json
import os
import random
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(BASE_DIR, "data", "sample")
HISTORICAL_DIR = os.path.join(SAMPLE_DIR, "historical")
FRESH_DIR = os.path.join(SAMPLE_DIR, "fresh")
RAW_HISTORICAL_CSV = os.path.join(BASE_DIR, "data", "raw", "data_jobs.csv")


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_historical_sample(rows_per_month=25, seed=42):
    """Write a deterministic stratified sample of actual raw 2023 records."""
    if not os.path.isfile(RAW_HISTORICAL_CSV):
        raise FileNotFoundError(f"Raw historical archive not found: {RAW_HISTORICAL_CSV}")
    rng = random.Random(seed)
    reservoirs = defaultdict(list)
    seen_by_month = defaultdict(int)

    with open(RAW_HISTORICAL_CSV, "r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"job_title", "job_posted_date", "job_skills"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Raw archive is missing required fields: {sorted(required)}")
        for row in reader:
            posted_at = (row.get("job_posted_date") or "").strip()
            month = posted_at[:7]
            if len(month) != 7 or month[:4] != "2023" or month[4] != "-":
                continue
            seen_by_month[month] += 1
            bucket = reservoirs[month]
            if len(bucket) < rows_per_month:
                bucket.append(row)
            else:
                replacement = rng.randrange(seen_by_month[month])
                if replacement < rows_per_month:
                    bucket[replacement] = row

    expected_months = {f"2023-{month:02d}" for month in range(1, 13)}
    if set(reservoirs) != expected_months or any(len(reservoirs[m]) < rows_per_month for m in expected_months):
        raise ValueError("The raw archive does not have enough real rows in every 2023 month")

    sample = [row for month in sorted(reservoirs) for row in reservoirs[month]]
    os.makedirs(HISTORICAL_DIR, exist_ok=True)
    json_path = os.path.join(HISTORICAL_DIR, "historical_sample_300.json")
    csv_path = os.path.join(HISTORICAL_DIR, "historical_sample_300.csv")
    with open(json_path, "w", encoding="utf-8") as target:
        json.dump(sample, target, indent=2, ensure_ascii=False)
    with open(csv_path, "w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(sample[0].keys()), extrasaction="raise")
        writer.writeheader()
        writer.writerows(sample)
    print(f"Saved {len(sample)} real archive rows across 12 months to {json_path}")
    return sample


def _fetch_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "BigDataJobSkillAnalytics/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_fresh_data():
    """Fetch current public API samples using standard certificate validation."""
    collected_at = _utc_now()
    jobs = []
    errors = []
    sources = (
        ("arbeitnow", "https://www.arbeitnow.com/api/job-board-api"),
        ("remotive", "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"),
    )
    for source_name, url in sources:
        try:
            payload = _fetch_json(url)
            items = payload.get("data", []) if source_name == "arbeitnow" else payload.get("jobs", [])
            for item in items:
                if source_name == "arbeitnow":
                    posted = item.get("created_at")
                    posted_at = datetime.fromtimestamp(posted, timezone.utc).isoformat().replace("+00:00", "Z") if posted else None
                    record_id = item.get("slug")
                    location = (item.get("location") or "").strip() or None
                    country = None
                    remote = bool(item.get("remote", False))
                    salary_raw = None
                else:
                    posted_at = item.get("publication_date") or None
                    record_id = item.get("id")
                    location = (item.get("candidate_required_location") or "").strip() or None
                    country = None
                    remote = True
                    salary_raw = item.get("salary") or None
                if not record_id:
                    continue
                jobs.append({
                    "source": source_name,
                    "source_record_id": str(record_id),
                    "source_url": item.get("url") or None,
                    "collected_at": collected_at,
                    "title": (item.get("title") or "").strip(),
                    "company": (item.get("company_name") or "").strip() or None,
                    "location": location,
                    "country": country,
                    "remote": remote,
                    "description": (item.get("description") or "").strip() or None,
                    "tags": item.get("tags") or [],
                    "job_types": item.get("job_types") or ([item.get("job_type")] if item.get("job_type") else []),
                    "posted_at": posted_at,
                    "salary_raw": salary_raw,
                })
        except Exception as exc:
            errors.append(f"{source_name}: {exc}")

    if not jobs:
        raise RuntimeError("No API returned a usable sample; existing sample files were preserved. " + "; ".join(errors))
    os.makedirs(FRESH_DIR, exist_ok=True)
    json_path = os.path.join(FRESH_DIR, "fresh_sample.json")
    with open(json_path, "w", encoding="utf-8") as target:
        json.dump(jobs, target, indent=2, ensure_ascii=False)
    print(f"Saved {len(jobs)} live API sample records to {json_path}")
    if errors:
        print("Some sources were unavailable: " + "; ".join(errors))
    return jobs


if __name__ == "__main__":
    historical = build_historical_sample()
    print(f"Historical sample: {len(historical)}")
