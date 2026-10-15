"""Versioned, title-evidence IT occupation scope policy for pinned Bronze 2026."""

import json
import re
from functools import lru_cache
from pathlib import Path

from src.common.taxonomy import load_dictionaries, normalize_title


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "configs" / "job_scope_policy_2026_v1.json"
POLICY_VERSION = "2026_it_scope_v1"
TAXONOMY_VERSION_2026 = "v0.2"


@lru_cache(maxsize=128)
def _pattern(expression):
    return re.compile(expression, re.IGNORECASE)


def load_scope_policy(path=POLICY_PATH):
    policy = json.loads(Path(path).read_text(encoding="utf-8"))
    if policy.get("version") != POLICY_VERSION or policy.get("taxonomy_version") != TAXONOMY_VERSION_2026:
        raise ValueError("Unsupported 2026 IT scope policy or taxonomy version")
    rules = policy.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("2026 scope policy has no rules")
    ids = [rule.get("id") for rule in rules]
    if len(ids) != len(set(ids)) or not all(ids):
        raise ValueError("2026 scope policy rule IDs must be unique and nonempty")
    for rule in rules:
        if rule.get("decision") not in {"in_scope_other_it", "in_scope_mapped", "excluded"}:
            raise ValueError(f"Invalid 2026 scope decision: {rule.get('id')}")
        if rule.get("decision") == "in_scope_mapped":
            if rule.get("pattern") is not None:
                raise ValueError("Mapped taxonomy rule cannot use a separate pattern")
        else:
            if not isinstance(rule.get("pattern"), str) or not rule["pattern"]:
                raise ValueError(f"Missing regex for 2026 scope rule: {rule.get('id')}")
            _pattern(rule["pattern"])
    if policy.get("default_global_decision") != "unresolved":
        raise ValueError("Unmatched global titles must remain unresolved")
    return policy


def classify_scope(title, source, market, *, policy=None, title_mapping=None,
                   federal_series_2210_verified=False):
    """Return scope and occupation without guessing when title evidence is thin.

    `federal_series_2210_verified` must come from the pinned Bronze manifest,
    never from a title or the mere source string.
    """
    policy = policy if policy is not None else load_scope_policy()
    mapping = title_mapping if title_mapping is not None else load_dictionaries(TAXONOMY_VERSION_2026)[0]
    title = str(title or "").strip()
    if not title:
        raise ValueError("Scope classification requires a nonempty valid title")
    occupation = normalize_title(title, mapping)
    common = {"taxonomy_version": TAXONOMY_VERSION_2026,
              "scope_policy_version": POLICY_VERSION}
    if source == "usajobs_historic":
        if market != "US_FEDERAL" or not federal_series_2210_verified:
            raise ValueError("USAJOBS requires verified PositionSeries=2210 and US_FEDERAL")
        return {**common, "normalized_title": occupation,
                "scope_decision": "in_scope",
                "scope_label": occupation if occupation != "Other IT" else "IT ngoài 8 nhóm",
                "analysis_scope_basis": policy["federal_rule_id"],
                "scope_reason": "Verified USAJOBS PositionSeries=2210"}
    if source not in {"arbeitnow", "remotive"} or market != "GLOBAL":
        raise ValueError("Unexpected source/market in pinned global 2026 input")

    for rule in policy["rules"]:
        if rule["decision"] == "in_scope_mapped":
            matched = occupation != "Other IT"
        else:
            matched = _pattern(rule["pattern"]).search(title) is not None
        if not matched:
            continue
        if rule["decision"] == "in_scope_mapped":
            return {**common, "normalized_title": occupation,
                    "scope_decision": "in_scope", "scope_label": occupation,
                    "analysis_scope_basis": rule["id"], "scope_reason": rule["reason"]}
        if rule["decision"] == "in_scope_other_it":
            return {**common, "normalized_title": "Other IT",
                    "scope_decision": "in_scope", "scope_label": "IT ngoài 8 nhóm",
                    "analysis_scope_basis": rule["id"], "scope_reason": rule["reason"]}
        return {**common, "normalized_title": occupation,
                "scope_decision": "excluded", "scope_label": "ngoài IT",
                "analysis_scope_basis": rule["id"], "scope_reason": rule["reason"]}
    return {**common, "normalized_title": occupation,
            "scope_decision": "unresolved", "scope_label": "chưa đủ thông tin",
            "analysis_scope_basis": "insufficient_title_evidence",
            "scope_reason": "Title does not establish an IT or non-IT occupation"}
