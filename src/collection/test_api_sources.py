import urllib.request
import json
import ssl

ssl_context = ssl._create_unverified_context()

print("--- 1. Testing Arbeitnow API ---")
try:
    req = urllib.request.Request(
        "https://www.arbeitnow.com/api/job-board-api",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
        data = json.loads(resp.read().decode())
        jobs = data.get("data", [])
        print(f"Status: SUCCESS, Total jobs returned: {len(jobs)}")
        if jobs:
            sample = jobs[0]
            print(f"Sample Title: {sample.get('title')}")
            print(f"Sample Company: {sample.get('company_name')}")
            print(f"Sample Created At (timestamp): {sample.get('created_at')}")
            print(f"Sample Location: {sample.get('location')}")
            print(f"Sample Tags: {sample.get('tags')}")
            print(f"Keys available: {list(sample.keys())}")
except Exception as e:
    print(f"Arbeitnow Failed: {e}")

print("\n--- 2. Testing Remotive API ---")
try:
    req = urllib.request.Request(
        "https://remotive.com/api/remote-jobs?category=software-dev&limit=10",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
        data = json.loads(resp.read().decode())
        jobs = data.get("jobs", [])
        print(f"Status: SUCCESS, Total jobs returned: {len(jobs)}")
        if jobs:
            sample = jobs[0]
            print(f"Sample Title: {sample.get('title')}")
            print(f"Sample Company: {sample.get('company_name')}")
            print(f"Sample Pub Date: {sample.get('publication_date')}")
            print(f"Sample Category: {sample.get('category')}")
            print(f"Sample Candidate Location: {sample.get('candidate_required_location')}")
            print(f"Sample Salary: {sample.get('salary')}")
            print(f"Sample Tags: {sample.get('tags')}")
            print(f"Keys available: {list(sample.keys())}")
except Exception as e:
    print(f"Remotive Failed: {e}")
