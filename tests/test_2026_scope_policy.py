"""Regression gates for the versioned 2026 title-evidence policy."""

import csv
from collections import Counter

import pytest

from src.common.run_manifest import sha256_file
from src.common.taxonomy import load_dictionaries, normalize_title
from src.processing.scope_policy_2026 import POLICY_PATH, classify_scope, load_scope_policy


def test_taxonomy_v01_remains_pinned_and_v02_corrects_aliases():
    old, _ = load_dictionaries("v0.1")
    new, _ = load_dictionaries("v0.2")
    assert normalize_title("Research Scientist", old) == "Data Scientist"
    assert normalize_title("Research Scientist", new) == "Other IT"
    assert normalize_title("Systems Engineer", old) == "DevOps Engineer"
    assert normalize_title("Systems Engineer", new) == "Other IT"
    for title, expected in (
        ("Full-Stack Entwickler", "Software Engineer"),
        ("Softwareentwickler", "Software Engineer"),
        ("Full-Stack Rails Engineer", "Software Engineer"),
        ("Shopify Developer", "Software Engineer"),
        ("Front-end Developer", "Frontend Developer"),
    ):
        assert normalize_title(title, new) == expected


def test_scope_policy_fail_closed_and_federal_series_gate():
    assert classify_scope("Systems Engineer", "arbeitnow", "GLOBAL")["scope_decision"] == "unresolved"
    assert classify_scope("IT Systems Engineer", "arbeitnow", "GLOBAL")["scope_decision"] == "in_scope"
    assert classify_scope("Research Scientist", "arbeitnow", "GLOBAL")["scope_decision"] == "unresolved"
    assert classify_scope("Weiterbildung Software Developer", "arbeitnow", "GLOBAL")["scope_decision"] == "excluded"
    assert classify_scope("Service Desk Agent", "arbeitnow", "GLOBAL")["scope_label"] == "IT ngoài 8 nhóm"
    with pytest.raises(ValueError, match="2210"):
        classify_scope("IT Specialist", "usajobs_historic", "US_FEDERAL")
    assert classify_scope("IT Specialist", "usajobs_historic", "US_FEDERAL",
                          federal_series_2210_verified=True)["scope_decision"] == "in_scope"
    with pytest.raises(ValueError, match="source/market"):
        classify_scope("Data Analyst", "arbeitnow", "US_FEDERAL")


def test_ai_review_sample_regression():
    policy = load_scope_policy()
    sample = POLICY_PATH.parents[1] / "docs/data/2026_it_scope_sample.csv"
    assert sha256_file(sample) == policy["ai_review_sample_sha256"]
    with sample.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 175
    counts = Counter()
    for row in rows:
        decision = classify_scope(
            row["title"], row["source"], row["market"], policy=policy,
            federal_series_2210_verified=row["source"] == "usajobs_historic",
        )
        counts[decision["scope_decision"]] += 1
        assert {"in_scope": "1", "excluded": "0", "unresolved": ""}[
            decision["scope_decision"]] == row["in_scope_it"]
        assert decision["scope_label"] == row["manual_label"]
    assert counts == {"in_scope": 142, "excluded": 27, "unresolved": 6}
