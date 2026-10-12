"""Small, Spark-free serving layer. Every load verifies the pinned Gold run."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
AUDIT = Path("docs/data/phase03_analytics_audit.json")
OCC_KEYS = ["month", "source", "occupation"]
SCOPE_KEYS = OCC_KEYS + ["skills_origin", "taxonomy_version"]
TABLE_KEYS = {
    "market_stats": ["month", "source"],
    "occupation_stats": OCC_KEYS,
    "skill_evidence_stats": SCOPE_KEYS,
    "skill_stats": SCOPE_KEYS + ["skill"],
    "skill_trends": SCOPE_KEYS + ["skill"],
}
COUNTS = {
    "market_stats": ["job_count", "skill_evidence_jobs", "known_country_jobs", "known_experience_jobs"],
    "occupation_stats": ["job_count", "source_month_jobs"],
    "skill_evidence_stats": ["origin_job_count", "occupation_job_count", "skill_evidence_jobs"],
    "skill_stats": ["occupation_job_count", "skill_job_count"],
    "skill_trends": ["occupation_job_count", "skill_job_count"],
}


class GoldError(ValueError):
    """An artifact cannot be used as verified dashboard evidence."""


@dataclass
class GoldRun:
    manifest: dict
    tables: dict[str, pd.DataFrame]
    manifest_sha256: str


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def directory_evidence(root):
    """Same evidence contract as Spark ETL; no Spark import at serving time."""
    root = Path(root).resolve()
    entries, digest = [], hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix != ".crc"):
        if not path.resolve().is_relative_to(root):
            raise GoldError("Gold file escapes its table directory")
        relative, checksum = path.relative_to(root).as_posix(), sha256(path)
        entries.append({"path": relative, "bytes": path.stat().st_size, "sha256": checksum})
        digest.update(f"{relative}:{checksum}\n".encode("utf-8"))
    return {"files": entries, "sha256": digest.hexdigest()}


def load_gold(root=ROOT, audit_path=None):
    """Resolve paths from run_id, so evidence also works in relocated checkouts.

    No 'latest run' fallback and no cached integrity verdict: verify on each load.
    Audit and manifest may contain old machine paths, which are never followed.
    """
    try:
        root = Path(root).resolve()
        audit = json.loads(Path(audit_path or root / AUDIT).read_text(encoding="utf-8"))
        run_id = audit["run_id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
            raise GoldError("Invalid Gold run ID")
        run_dir = root / "data/gold/global/runs" / run_id
        if not run_dir.resolve().is_relative_to(root):
            raise GoldError("Gold run escapes workspace")
        manifest_path = run_dir / "manifest.json"
        manifest_hash = sha256(manifest_path)
        if manifest_hash != audit["manifest_sha256"]:
            raise GoldError("Gold manifest SHA-256 mismatch")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != 1 or manifest.get("status") != "completed":
            raise GoldError("Gold run is not completed/schema is unsupported")
        for field in ("run_id", "analysis_type", "taxonomy_version", "predictive_gate"):
            if field not in audit or manifest.get(field) != audit[field]:
                raise GoldError(f"Gold audit/manifest mismatch: {field}")
        if manifest["analysis_type"] != "observed_descriptive_only":
            raise GoldError("This dashboard requires descriptive Gold")
        if not manifest.get("predictive_gate", {}).get("decision"):
            raise GoldError("Missing predictive gate evidence")
        tables = {}
        for name, keys in TABLE_KEYS.items():
            output = manifest["outputs"][name]
            table_path = run_dir / name
            if not table_path.resolve().is_relative_to(run_dir.resolve()):
                raise GoldError(f"Gold table escapes run: {name}")
            actual = directory_evidence(table_path)
            if actual != {"files": output["files"], "sha256": output["sha256"]}:
                raise GoldError(f"Gold table checksum mismatch: {name}")
            if any(output[k] != audit["outputs"][name][k] for k in ("rows", "sha256")):
                raise GoldError(f"Gold table audit mismatch: {name}")
            files = [table_path / e["path"] for e in actual["files"] if e["path"].endswith(".parquet")]
            if not files:
                raise GoldError(f"No Parquet files: {name}")
            frame = pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)
            if len(frame) != output["rows"]:
                raise GoldError(f"Gold row count mismatch: {name}")
            needed = set(keys + COUNTS[name])
            if not needed.issubset(frame.columns):
                raise GoldError(f"Missing Gold columns: {name}")
            if frame[keys].isna().any().any() or frame.duplicated(keys).any():
                raise GoldError(f"Null or duplicate Gold key: {name}")
            if not frame["month"].str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
                raise GoldError(f"Invalid month: {name}")
            if frame[COUNTS[name]].isna().any().any() or (frame[COUNTS[name]] < 0).any().any():
                raise GoldError(f"Invalid Gold counts: {name}")
            if "taxonomy_version" in frame and not frame.taxonomy_version.eq(manifest["taxonomy_version"]).all():
                raise GoldError(f"Taxonomy mismatch: {name}")
            tables[name] = frame
        return GoldRun(manifest, tables, manifest_hash)
    except GoldError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise GoldError(f"Cannot load verified Gold: {exc}") from exc


def select_scope(frame, source, months, occupations=None, origin=None, taxonomy=None):
    """A single source is mandatory; empty selections mean no observations."""
    if not isinstance(source, str):
        raise ValueError("Select exactly one source")
    mask = frame.source.eq(source) & frame.month.isin(months)
    if occupations is not None and "occupation" in frame:
        mask &= frame.occupation.isin(occupations)
    if origin is not None and "skills_origin" in frame:
        mask &= frame.skills_origin.eq(origin)
    if taxonomy is not None and "taxonomy_version" in frame:
        mask &= frame.taxonomy_version.eq(taxonomy)
    return frame.loc[mask].copy()


def summarize_skills(skills, occupations):
    """Count-weighted rates, with each occupation-month denominator counted once.

    Include jobs with no extracted skills. Keep evidence modes separate. The
    caller selects the same source, months and occupations on both frames.
    """
    keys = ["source", "occupation", "skills_origin", "taxonomy_version", "skill"]
    numerator = skills.groupby(keys, as_index=False).skill_job_count.sum()
    denominator = occupations.groupby(["source", "occupation"], as_index=False).job_count.sum()
    denominator = denominator.rename(columns={"job_count": "denominator_jobs"})
    result = numerator.merge(denominator, on=["source", "occupation"], validate="many_to_one")
    result["demand_rate"] = result.skill_job_count / result.denominator_jobs.where(result.denominator_jobs.gt(0))
    return result.sort_values(["demand_rate", "skill"], ascending=[False, True]).reset_index(drop=True)


def trend_calendar(frame, start, end):
    """One skill series, calendar gaps are NaN; observed zeros survive."""
    identity = ["source", "occupation", "skills_origin", "taxonomy_version", "skill"]
    if not frame.empty and len(frame[identity].drop_duplicates()) != 1:
        raise ValueError("Select exactly one source/occupation/evidence/skill series")
    months = pd.DataFrame({"month": pd.period_range(start, end, freq="M").astype(str)})
    result = months.merge(frame, on="month", how="left", validate="one_to_one")
    if "observed_delta_pp" in result:
        # Never display a change without a verified consecutive observation.
        result.loc[~result.consecutive_observed_month.eq(True), "observed_delta_pp"] = float("nan")
    return result
