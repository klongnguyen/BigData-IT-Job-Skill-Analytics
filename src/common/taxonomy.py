"""Shared, deterministic V0 occupation and skill matching rules."""

import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_VERSION = "v0.1"


def load_dictionaries():
    with (ROOT / "configs" / "job_title_mapping_v0.json").open(encoding="utf-8") as source:
        titles = json.load(source)
    with (ROOT / "configs" / "skills_v0.json").open(encoding="utf-8") as source:
        skills = json.load(source)
    return titles, skills


@lru_cache(maxsize=512)
def _alias_pattern(alias):
    alias = str(alias).strip()
    if not alias:
        return None
    return re.compile(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", re.IGNORECASE)


def _contains_alias(text, alias):
    pattern = _alias_pattern(str(alias))
    return pattern.search(text) is not None if pattern else False


def normalize_title(title, title_mapping=None):
    if not title:
        return "Other IT"
    mapping = title_mapping if title_mapping is not None else load_dictionaries()[0]
    text = str(title).casefold()
    matches = []
    for order, (role, aliases) in enumerate(mapping.items()):
        for alias in aliases:
            if _contains_alias(text, alias):
                matches.append((len(str(alias).split()), len(str(alias)), -order, role))
    return max(matches)[3] if matches else "Other IT"


def extract_skills(text, skills_dictionary=None):
    if not text:
        return []
    dictionary = skills_dictionary if skills_dictionary is not None else load_dictionaries()[1]
    clean = re.sub(r"<[^>]+>", " ", str(text))
    clean = re.sub(r"\s+", " ", clean)
    found = []
    for skill, aliases in dictionary.items():
        match_text = re.sub(r"(?i)\bexcel\s+(?:at|in)\b", " ", clean) if skill == "excel" else clean
        for alias in aliases:
            if _contains_alias(match_text, alias):
                found.append(skill)
                break
    return sorted(found)


def normalize_source_tags(value, skills_dictionary=None):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_tags = value
    else:
        import ast

        text = str(value).strip()
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            try:
                parsed = ast.literal_eval(text)
            except (ValueError, SyntaxError):
                parsed = [text]
        raw_tags = parsed if isinstance(parsed, (list, tuple, set)) else [parsed]
    result = set()
    for tag in raw_tags:
        result.update(extract_skills(str(tag), skills_dictionary))
    return sorted(result)
