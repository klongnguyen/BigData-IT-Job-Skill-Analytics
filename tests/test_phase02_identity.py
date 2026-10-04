"""Source identity stays stable across ingestion runs and text normalization."""

from src.common.identity import canonical_text, stable_job_id


def test_stable_job_id_uses_canonical_source_identity():
    expected = stable_job_id("arbeitnow", "job-123")
    assert expected == stable_job_id("  ARBEITNOW  ", " JOB-123 ")
    assert len(expected) == 64
    assert expected != stable_job_id("remotive", "job-123")
    assert expected != stable_job_id("arbeitnow", "job-124")


def test_canonical_text_normalizes_unicode_and_whitespace():
    assert canonical_text("  DATA\u3000ENGINEER  ") == "data engineer"
    assert canonical_text(None) == ""
