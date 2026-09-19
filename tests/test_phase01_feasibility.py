"""
Phase 01 Feasibility Verification Script:
1. Normalizes Job Titles against configs/job_title_mapping_v0.json (P1-17)
2. Extracts Skills from descriptions using configs/skills_v0.json (P1-18)
3. Evaluates time-series continuity across months and years (P1-19)
"""

import os
import re
import json
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST_PATH = os.path.join(BASE_DIR, "data", "sample", "historical", "historical_sample_300.json")
FRESH_PATH = os.path.join(BASE_DIR, "data", "sample", "fresh", "fresh_sample.json")
TITLE_MAP_PATH = os.path.join(BASE_DIR, "configs", "job_title_mapping_v0.json")
SKILLS_MAP_PATH = os.path.join(BASE_DIR, "configs", "skills_v0.json")

# Load configs
with open(TITLE_MAP_PATH, "r", encoding="utf-8") as f:
    title_mapping = json.load(f)

with open(SKILLS_MAP_PATH, "r", encoding="utf-8") as f:
    skills_dictionary = json.load(f)

# Precompile skill regexes
skill_regexes = {}
for skill, aliases in skills_dictionary.items():
    patterns = []
    for alias in aliases:
        # Escape special characters like c++, c#, .net
        escaped = re.escape(alias)
        # Word boundary
        patterns.append(rf"(?:\b|(?<=[\s,./])){escaped}(?:\b|(?=[\s,./]))")
    combined_pattern = re.compile("|".join(patterns), re.IGNORECASE)
    skill_regexes[skill] = combined_pattern

def normalize_title(title: str) -> str:
    title_lower = title.lower().strip()
    for standard_role, variations in title_mapping.items():
        for var in variations:
            if var in title_lower:
                return standard_role
    return "Other IT"

def extract_skills(text: str) -> list:
    found_skills = []
    # Strip HTML tags if any
    clean_text = re.sub(r"<[^>]+>", " ", text)
    for skill, pattern in skill_regexes.items():
        if pattern.search(clean_text):
            found_skills.append(skill)
    return sorted(found_skills)

def run_evaluation():
    with open(HIST_PATH, "r", encoding="utf-8") as f:
        hist_data = json.load(f)

    with open(FRESH_PATH, "r", encoding="utf-8") as f:
        fresh_data = json.load(f)

    all_jobs = []
    for h in hist_data:
        all_jobs.append({
            "source_type": "historical",
            "title": h.get("job_title", ""),
            "description": h.get("job_description", ""),
            "posted_at": str(h.get("job_posted_date", ""))[:19]
        })
    for f_item in fresh_data:
        all_jobs.append({
            "source_type": "fresh",
            "title": f_item.get("title", ""),
            "description": f_item.get("description", ""),
            "posted_at": str(f_item.get("posted_at", ""))[:19]
        })

    total_jobs = len(all_jobs)
    print(f"Total jobs evaluated: {total_jobs} ({len(hist_data)} Historical + {len(fresh_data)} Fresh)")

    # 1. Job Title Normalization Test (P1-17)
    role_counts = Counter()
    matched_count = 0
    for j in all_jobs:
        norm_role = normalize_title(j["title"])
        j["normalized_title"] = norm_role
        role_counts[norm_role] += 1
        if norm_role != "Other IT":
            matched_count += 1

    title_match_rate = round((matched_count / total_jobs) * 100, 2)
    print(f"\n[P1-17] Job Title Normalization Match Rate: {title_match_rate}% ({matched_count}/{total_jobs})")
    print("Role Distribution:")
    for role, cnt in role_counts.most_common():
        pct = round((cnt / total_jobs) * 100, 1)
        print(f"  - {role}: {cnt} ({pct}%)")

    # 2. Skill Extraction Test (P1-18)
    skill_counts = Counter()
    jobs_with_skills = 0
    total_skills_extracted = 0

    for j in all_jobs:
        extracted = extract_skills(j["description"])
        j["skills"] = extracted
        if extracted:
            jobs_with_skills += 1
            total_skills_extracted += len(extracted)
            for s in extracted:
                skill_counts[s] += 1

    skill_coverage_rate = round((jobs_with_skills / total_jobs) * 100, 2)
    avg_skills_per_job = round(total_skills_extracted / jobs_with_skills, 2) if jobs_with_skills else 0

    print(f"\n[P1-18] Skill Extraction Rate: {skill_coverage_rate}% ({jobs_with_skills}/{total_jobs} jobs have skills)")
    print(f"Average skills extracted per job: {avg_skills_per_job}")
    print("Top 15 Most Demanded Skills:")
    for skill, cnt in skill_counts.most_common(15):
        pct = round((cnt / total_jobs) * 100, 1)
        print(f"  - {skill}: {cnt} ({pct}%)")

    # 3. Time-series Distribution Check (P1-19)
    monthly_counts = Counter()
    yearly_counts = Counter()

    for j in all_jobs:
        d = j["posted_at"]
        if len(d) >= 7:
            monthly_counts[d[:7]] += 1
            yearly_counts[d[:4]] += 1

    print("\n[P1-19] Time-series Continuity (Yearly Distribution):")
    for yr in sorted(yearly_counts.keys()):
        print(f"  - Year {yr}: {yearly_counts[yr]} jobs")

    print(f"Total distinct months with data: {len(monthly_counts)} months")

    # Save summary results
    results = {
        "total_jobs": total_jobs,
        "title_match_rate_pct": title_match_rate,
        "role_counts": dict(role_counts),
        "skill_coverage_rate_pct": skill_coverage_rate,
        "avg_skills_per_job": avg_skills_per_job,
        "top_skills": dict(skill_counts.most_common(20)),
        "yearly_distribution": dict(yearly_counts),
        "monthly_months_count": len(monthly_counts)
    }

    results_path = os.path.join(BASE_DIR, "tests", "test_results_phase01.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nVerification results saved to {results_path}")
    return results

if __name__ == "__main__":
    run_evaluation()
