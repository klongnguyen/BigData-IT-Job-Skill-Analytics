"""
Fresh Data Ingestion Module (Bronze Layer):
Fetches live job postings from Arbeitnow and Remotive APIs,
attaches Bronze Layer ingestion metadata, and saves into data/bronze/global/fresh/.
"""

import os
import json
import uuid
import ssl
import urllib.request
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_FRESH_DIR = os.path.join(BASE_DIR, "data", "bronze", "global", "fresh")

os.makedirs(BRONZE_FRESH_DIR, exist_ok=True)
ssl_context = ssl._create_unverified_context()

def ingest_fresh_data():
    ingestion_id = str(uuid.uuid4())
    collected_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    print(f"[Fresh Ingestion] Starting fresh data ingestion (ID: {ingestion_id})...")
    fresh_jobs = []

    # 1. Fetch Arbeitnow API
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("data", []):
                created_ts = item.get("created_at")
                if created_ts:
                    posted_dt = datetime.utcfromtimestamp(created_ts).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    posted_dt = collected_at

                fresh_jobs.append({
                    "ingestion_id": ingestion_id,
                    "market": "GLOBAL",
                    "source": "arbeitnow",
                    "collected_at": collected_at,
                    "raw_id": f"arbeitnow_{item.get('slug')}",
                    "title": item.get("title", "").strip(),
                    "company": item.get("company_name", "").strip(),
                    "location": item.get("location", "Remote").strip(),
                    "remote": item.get("remote", False),
                    "description": item.get("description", "").strip(),
                    "tags": item.get("tags", []),
                    "job_types": item.get("job_types", []),
                    "posted_at": posted_dt,
                    "salary_raw": None,
                    "currency": "USD"
                })
        print(f"  -> Fetched {len(fresh_jobs)} records from Arbeitnow API.")
    except Exception as e:
        print(f"  -> Error fetching Arbeitnow: {e}")

    # 2. Fetch Remotive API
    try:
        remotive_count = 0
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=150"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("jobs", []):
                pub_date = item.get("publication_date", "")
                if pub_date:
                    try:
                        pub_dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pub_dt = pub_date[:19].replace("T", " ")
                else:
                    pub_dt = collected_at

                fresh_jobs.append({
                    "ingestion_id": ingestion_id,
                    "market": "GLOBAL",
                    "source": "remotive",
                    "collected_at": collected_at,
                    "raw_id": f"remotive_{item.get('id')}",
                    "title": item.get("title", "").strip(),
                    "company": item.get("company_name", "").strip(),
                    "location": item.get("candidate_required_location", "Remote").strip(),
                    "remote": True,
                    "description": item.get("description", "").strip(),
                    "tags": item.get("tags", []),
                    "job_types": [item.get("job_type", "full_time")],
                    "posted_at": pub_dt,
                    "salary_raw": item.get("salary", ""),
                    "currency": "USD"
                })
                remotive_count += 1
        print(f"  -> Fetched {remotive_count} records from Remotive API.")
    except Exception as e:
        print(f"  -> Error fetching Remotive: {e}")

    # Save to Bronze Layer
    output_file = os.path.join(BRONZE_FRESH_DIR, f"fresh_batch_{timestamp_str}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(fresh_jobs, f, indent=2, ensure_ascii=False)

    print(f"[Fresh Ingestion] Completed! Saved {len(fresh_jobs)} records to {output_file}")
    return len(fresh_jobs)

if __name__ == "__main__":
    ingest_fresh_data()
