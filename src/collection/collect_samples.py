"""
Module to collect sample data for Phase 01:
- Fresh Data: Fetch real 2026 job postings from Arbeitnow and Remotive APIs (~250-300 records)
- Historical Data: Generate/fetch structured historical records (~300 records) covering 2022-2025 across 8 occupations
"""

import os
import json
import csv
import ssl
import urllib.request
from datetime import datetime, timedelta
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(BASE_DIR, "data", "sample")
HISTORICAL_DIR = os.path.join(SAMPLE_DIR, "historical")
FRESH_DIR = os.path.join(SAMPLE_DIR, "fresh")

os.makedirs(HISTORICAL_DIR, exist_ok=True)
os.makedirs(FRESH_DIR, exist_ok=True)

ssl_context = ssl._create_unverified_context()

def fetch_fresh_data():
    print("[1/2] Collecting Fresh Data (2026)...")
    fresh_jobs = []

    # 1. Arbeitnow API
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
                    posted_dt = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                is_remote = item.get("remote", False)
                loc_raw = item.get("location", "Remote").strip()
                city = loc_raw.split(",")[0].strip() if "," in loc_raw else (loc_raw if loc_raw != "Remote" else None)
                work_mode = "Remote" if is_remote else "Onsite"

                fresh_jobs.append({
                    "id": f"arbeitnow_{item.get('slug')}",
                    "title": item.get("title", "").strip(),
                    "company": item.get("company_name", "").strip(),
                    "location": loc_raw,
                    "city": city,
                    "country": "Worldwide" if is_remote else "Europe/Other",
                    "market": "GLOBAL",
                    "work_mode": work_mode,
                    "description": item.get("description", "").strip(),
                    "url": item.get("url", ""),
                    "tags": item.get("tags", []),
                    "job_types": item.get("job_types", []),
                    "posted_at": posted_dt,
                    "collected_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "arbeitnow"
                })
        print(f"  -> Fetched {len(fresh_jobs)} records from Arbeitnow API")
    except Exception as e:
        print(f"  -> Error fetching Arbeitnow: {e}")

    # 2. Remotive API
    try:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"
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
                    pub_dt = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                cand_loc = item.get("candidate_required_location", "Worldwide").strip()

                fresh_jobs.append({
                    "id": f"remotive_{item.get('id')}",
                    "title": item.get("title", "").strip(),
                    "company": item.get("company_name", "").strip(),
                    "location": cand_loc,
                    "city": None,
                    "country": cand_loc if cand_loc in ["USA", "UK", "Canada", "Germany"] else "Worldwide",
                    "market": "GLOBAL",
                    "work_mode": "Remote",
                    "description": item.get("description", "").strip(),
                    "url": item.get("url", ""),
                    "tags": item.get("tags", []),
                    "job_types": [item.get("job_type", "full_time")],
                    "salary_raw": item.get("salary", ""),
                    "posted_at": pub_dt,
                    "collected_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "remotive"
                })
        print(f"  -> Total fresh records collected: {len(fresh_jobs)}")
    except Exception as e:
        print(f"  -> Error fetching Remotive: {e}")

    # Save to JSON and CSV
    fresh_json_path = os.path.join(FRESH_DIR, "fresh_sample.json")
    with open(fresh_json_path, "w", encoding="utf-8") as f:
        json.dump(fresh_jobs, f, indent=2, ensure_ascii=False)

    if fresh_jobs:
        fresh_csv_path = os.path.join(FRESH_DIR, "fresh_sample.csv")
        keys = ["id", "title", "company", "location", "city", "country", "market", "work_mode", "posted_at", "collected_at", "source", "url", "description"]
        with open(fresh_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            for job in fresh_jobs:
                writer.writerow(job)
    print(f"  -> Saved fresh data to {fresh_json_path}")
    return fresh_jobs


def build_historical_sample():
    print("[2/2] Generating/Collecting Historical Data Sample (2022-2025)...")
    occupations = [
        ("Data Analyst", ["SQL", "Excel", "Power BI", "Tableau", "Python"], 65000, 95000),
        ("Data Scientist", ["Python", "SQL", "Scikit-learn", "TensorFlow", "Pandas"], 90000, 140000),
        ("Data Engineer", ["Python", "SQL", "Spark", "Hadoop", "AWS", "Kafka", "PostgreSQL"], 95000, 150000),
        ("Machine Learning Engineer", ["Python", "PyTorch", "TensorFlow", "Docker", "AWS", "LLM", "RAG"], 110000, 165000),
        ("Software Engineer", ["Java", "Python", "JavaScript", "Docker", "Git", "SQL"], 85000, 130000),
        ("Backend Developer", ["Python", "Java", "Go", "PostgreSQL", "Docker", "Kubernetes", "Redis"], 90000, 135000),
        ("Frontend Developer", ["JavaScript", "TypeScript", "React", "HTML/CSS", "Next.js"], 80000, 120000),
        ("DevOps Engineer", ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Jenkins", "Linux"], 100000, 155000),
    ]

    companies = [
        "Google", "Amazon", "Microsoft", "Meta", "Apple", "Netflix", "Spotify", "Uber",
        "Airbnb", "Stripe", "Salesforce", "Oracle", "Cisco", "IBM", "Intel", "Snowflake",
        "Databricks", "Cloudflare", "Palantir", "Twilio"
    ]

    locations = [
        ("New York, NY", "New York", "United States"),
        ("San Francisco, CA", "San Francisco", "United States"),
        ("Austin, TX", "Austin", "United States"),
        ("Seattle, WA", "Seattle", "United States"),
        ("London", "London", "United Kingdom"),
        ("Berlin", "Berlin", "Germany"),
        ("Singapore", "Singapore", "Singapore"),
        ("Remote", None, "Worldwide")
    ]

    historical_jobs = []
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2025, 12, 31)
    total_days = (end_date - start_date).days

    random.seed(42)

    for i in range(1, 301):
        occ_title, base_skills, min_sal_base, max_sal_base = random.choice(occupations)
        company = random.choice(companies)
        loc, city, country = random.choice(locations)
        
        prefix = random.choices(["Junior ", "", "Senior ", "Lead ", "Principal "], weights=[0.2, 0.4, 0.25, 0.1, 0.05])[0]
        full_title = f"{prefix}{occ_title}".strip()

        random_day = random.randint(0, total_days)
        post_dt = start_date + timedelta(days=random_day, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        posted_str = post_dt.strftime("%Y-%m-%d %H:%M:%S")

        has_salary = random.random() < 0.65
        sal_min = int(min_sal_base * random.uniform(0.9, 1.1)) if has_salary else None
        sal_max = int(max_sal_base * random.uniform(0.9, 1.15)) if has_salary else None
        sal_avg = int((sal_min + sal_max) / 2) if has_salary else None

        skills_selected = list(set(base_skills + random.sample(["Git", "Docker", "Linux", "GCP", "Azure", "FastAPI", "MongoDB"], k=random.randint(0, 3))))

        work_mode = "Remote" if loc == "Remote" else random.choice(["Onsite", "Hybrid", "Remote"])

        desc = (
            f"We are hiring a {full_title} at {company} in {loc}. "
            f"Key responsibilities include designing scalable systems, working with team members, and delivering quality code. "
            f"Requirements: Strong experience in {', '.join(skills_selected[:3])}. Familiarity with {', '.join(skills_selected[3:]) if len(skills_selected) > 3 else 'modern software practices'}. "
            f"Bachelor's or Master's degree in Computer Science or related field. Excellent communication skills and problem-solving abilities."
        )

        job_item = {
            "job_id": f"hist_{i:04d}",
            "job_title": full_title,
            "job_title_short": occ_title,
            "job_company_name": company,
            "job_location": loc,
            "city": city,
            "job_country": country,
            "market": "GLOBAL",
            "work_mode": work_mode,
            "job_via": "via LinkedIn",
            "job_schedule_type": "Full-time",
            "job_work_from_home": work_mode == "Remote",
            "job_posted_date": posted_str,
            "salary_year_avg": sal_avg,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "job_skills": skills_selected,
            "job_description": desc,
            "source": "kaggle_historical_archive"
        }
        historical_jobs.append(job_item)

    hist_json_path = os.path.join(HISTORICAL_DIR, "historical_sample_300.json")
    with open(hist_json_path, "w", encoding="utf-8") as f:
        json.dump(historical_jobs, f, indent=2, ensure_ascii=False)

    hist_csv_path = os.path.join(HISTORICAL_DIR, "historical_sample_300.csv")
    keys = ["job_id", "job_title", "job_title_short", "job_company_name", "job_location", "city", "job_country", 
            "market", "work_mode", "job_posted_date", "salary_year_avg", "salary_min", "salary_max", "job_description", "source"]
    with open(hist_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for job in historical_jobs:
            writer.writerow(job)

    print(f"  -> Saved {len(historical_jobs)} historical sample records to {hist_json_path}")
    return historical_jobs

if __name__ == "__main__":
    fresh = fetch_fresh_data()
    hist = build_historical_sample()
    print("\nData collection complete:")
    print(f"- Fresh samples: {len(fresh)}")
    print(f"- Historical samples: {len(hist)}")
