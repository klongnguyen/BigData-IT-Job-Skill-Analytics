"""Unified job-posting schema fields shared across ingestion and ETL."""

UNIFIED_JOB_FIELDS = [
    "job_id",
    "title",
    "normalized_title",
    "company",
    "location",
    "city",
    "country",
    "market",
    "work_mode",
    "description",
    "experience_level",
    "salary_min",
    "salary_max",
    "currency",
    "posted_at",
    "collected_at",
    "source",
    "skills",
]

UNIFIED_JOB_NULLABLE_FIELDS = {
    "company", "location", "city", "country", "work_mode", "description",
    "experience_level", "salary_min", "salary_max", "currency", "posted_at",
    "collected_at",
}

UNIFIED_JOB_REQUIRED_FIELDS = set(UNIFIED_JOB_FIELDS) - UNIFIED_JOB_NULLABLE_FIELDS
