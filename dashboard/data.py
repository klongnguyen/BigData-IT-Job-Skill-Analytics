"""Small, Spark-free serving layer. Every load verifies the pinned Gold run."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
AUDIT = Path("docs/data/phase03_analytics_audit.json")
CATALOG = Path("docs/data/dashboard_gold_catalog.json")
AUDIT_WHITELIST = {
    "legacy_2023": ("docs/data/phase03_analytics_audit.json", "data/gold/global/runs"),
    "scoped_2026": ("docs/data/2026_gold_run_audit.json", "data/gold/jobscope/runs"),
}
OCC_KEYS = ["market", "month", "source", "occupation"]
SCOPE_KEYS = OCC_KEYS + ["skills_origin", "taxonomy_version"]
TABLE_KEYS = {
    "market_stats": ["market", "month", "source"],
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
    dataset_id: str = "legacy_2023"


def load_catalog(root=ROOT):
    root = Path(root).resolve()
    path = root / CATALOG
    if path.exists():
        catalog = json.loads(path.read_text(encoding="utf-8"))
        entries = catalog.get("datasets")
        if catalog.get("schema_version") != 1 or not isinstance(entries, list):
            raise GoldError("Unsupported Gold dataset catalog")
    else:
        # Isolated legacy fixtures have a single fixed audit, never a latest-run scan.
        audit_path = root / AUDIT
        if not audit_path.is_file():
            raise GoldError("Missing audited Gold dataset catalog")
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        entries = [{"id": "legacy_2023", "label": "Legacy / archive 2023",
                    "audit_path": AUDIT.as_posix(), "audit_sha256": sha256(audit_path),
                    "run_namespace": "data/gold/global/runs", "run_id": audit["run_id"]}]
    result = {}
    for entry in entries:
        dataset_id = entry.get("id")
        if dataset_id not in AUDIT_WHITELIST or dataset_id in result:
            raise GoldError("Unrecognized or duplicate Gold dataset")
        audit_relative, namespace = AUDIT_WHITELIST[dataset_id]
        if entry.get("audit_path") != audit_relative or entry.get("run_namespace") != namespace:
            raise GoldError("Gold catalog path is outside whitelist")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", str(entry.get("run_id", ""))):
            raise GoldError("Invalid Gold catalog run ID")
        audit_path = root / audit_relative
        if sha256(audit_path) != entry.get("audit_sha256"):
            raise GoldError("Gold catalog audit SHA-256 mismatch")
        result[dataset_id] = entry
    return result


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


def load_gold(root=ROOT, audit_path=None, dataset="legacy_2023"):
    """Resolve paths from run_id, so evidence also works in relocated checkouts.

    No 'latest run' fallback and no cached integrity verdict: verify on each load.
    Audit and manifest may contain old machine paths, which are never followed.
    """
    try:
        root = Path(root).resolve()
        catalog = load_catalog(root)
        if dataset not in catalog:
            raise GoldError("Dataset is not in the audited catalog")
        entry = catalog[dataset]
        expected_audit = (root / entry["audit_path"]).resolve()
        if audit_path is not None and Path(audit_path).resolve() != expected_audit:
            raise GoldError("Arbitrary Gold audit path is not allowed")
        audit = json.loads(expected_audit.read_text(encoding="utf-8"))
        run_id = audit["run_id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id) or run_id != entry["run_id"]:
            raise GoldError("Invalid Gold run ID")
        run_dir = root / entry["run_namespace"] / run_id
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
        if manifest.get("predictive_gate", {}).get("decision") != "NO_GO":
            raise GoldError("Gold predictive gate must remain NO_GO")
        if dataset == "scoped_2026":
            if audit.get("status") != "passed" or audit.get("scope_summary") != {
                    "silver_rows": 8370, "scope_excluded_rows": 548,
                    "scope_unresolved_rows": 10788}:
                raise GoldError("JobScope 2026 audit/scope summary is invalid")
            for field in ("scope_policy_version", "scope_policy_sha256",
                          "ai_review_sample_sha256", "scope_summary", "input"):
                if manifest.get(field) != audit.get(field):
                    raise GoldError(f"JobScope 2026 audit/manifest mismatch: {field}")
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
            if dataset == "legacy_2023" and "market" not in frame.columns:
                frame["market"] = "GLOBAL"
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
        return GoldRun(manifest, tables, manifest_hash, dataset)
    except GoldError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise GoldError(f"Cannot load verified Gold: {exc}") from exc


def select_scope(frame, source, months, occupations=None, origin=None, taxonomy=None, market=None):
    """Select one market and source; empty selections mean no observations."""
    if not isinstance(source, str):
        raise ValueError("Select exactly one source")
    markets = frame.market.dropna().unique() if "market" in frame else ["GLOBAL"]
    if market is None:
        if len(markets) != 1:
            raise ValueError("Select exactly one market")
        market = markets[0]
    if not isinstance(market, str):
        raise ValueError("Select exactly one market")
    mask = frame.source.eq(source) & frame.month.isin(months) & frame.market.eq(market)
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
    keys = ["market", "source", "occupation", "skills_origin", "taxonomy_version", "skill"]
    numerator = skills.groupby(keys, as_index=False).skill_job_count.sum()
    denominator = occupations.groupby(["market", "source", "occupation"], as_index=False).job_count.sum()
    denominator = denominator.rename(columns={"job_count": "denominator_jobs"})
    result = numerator.merge(denominator, on=["market", "source", "occupation"], validate="many_to_one")
    result["demand_rate"] = result.skill_job_count / result.denominator_jobs.where(result.denominator_jobs.gt(0))
    return result.sort_values(["demand_rate", "skill"], ascending=[False, True]).reset_index(drop=True)


def trend_calendar(frame, start, end):
    """One skill series, calendar gaps are NaN; observed zeros survive."""
    identity = ["market", "source", "occupation", "skills_origin", "taxonomy_version", "skill"]
    if not frame.empty and len(frame[identity].drop_duplicates()) != 1:
        raise ValueError("Select exactly one source/occupation/evidence/skill series")
    months = pd.DataFrame({"month": pd.period_range(start, end, freq="M").astype(str)})
    result = months.merge(frame, on="month", how="left", validate="one_to_one")
    if "observed_delta_pp" in result:
        # Never display a change without a verified consecutive observation.
        result.loc[~result.consecutive_observed_month.eq(True), "observed_delta_pp"] = float("nan")
    return result
