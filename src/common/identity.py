"""Stable identifiers and canonical keys derived from source record identity."""

import hashlib
import re
import unicodedata


def canonical_text(value):
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return re.sub(r"\s+", " ", text)


def stable_job_id(source, source_record_id):
    identity = f"{canonical_text(source)}|{canonical_text(source_record_id)}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()
