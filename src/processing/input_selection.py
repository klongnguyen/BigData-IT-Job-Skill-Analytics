"""Pinned selection of audited Bronze inputs for the 2026 Silver migration."""

import json
from collections import Counter
from pathlib import Path

from src.common.run_manifest import load_bronze_run, sha256_file


ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = "docs/data/2026_ingestion_audit.json"
PARTIAL_RUN_ID = "20261015T024120862520Z-6d0ef660e16f"
PARTIAL_MANIFEST_SHA256 = "74d13bc94ebc2ea2eae7d02eb856570d0c93aafe18d614ddbc91dc87a38a8a6c"
PARTIAL_ALLOWLIST = {(PARTIAL_RUN_ID, PARTIAL_MANIFEST_SHA256)}


def _workspace_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Input paths must be nonempty workspace-relative POSIX paths")
    path = Path(relative)
    if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
        raise ValueError(f"Unsafe workspace-relative path: {relative}")
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise ValueError(f"Input path escapes workspace: {relative}")
    return target


def _audit_entries(root, contract, strict_2026):
    audit_relative = contract.get("audit_path")
    if strict_2026 and audit_relative != AUDIT_PATH:
        raise ValueError("2026 selection must use the canonical Bronze audit")
    audit_path = _workspace_path(root, audit_relative)
    if sha256_file(audit_path) != contract.get("audit_sha256"):
        raise ValueError("Bronze audit SHA-256 mismatch")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    rows = audit.get("input_runs")
    if not isinstance(rows, list):
        raise ValueError("Bronze audit has no input_runs")
    if strict_2026 and (audit.get("audit_kind") != "2026_bronze_source_occupation_month" or len(rows) != 23):
        raise ValueError("Expected the audited set of exactly 23 Bronze 2026 runs")
    indexed = {row["run_id"]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError("Duplicate run_id in Bronze audit")
    return indexed


def _validate_run_metadata(manifest, entry, audit_entry, strict_2026):
    for key, manifest_key in (("run_id", "run_id"), ("kind", "kind"),
                              ("expected_status", "status"), ("source", "source"),
                              ("rows", "total_rows")):
        if key in entry and entry[key] != manifest.get(manifest_key):
            raise ValueError(f"Bronze {key} mismatch: {entry.get('run_id')}")
    for key, entry_key in (("status", "expected_status"), ("source", "source"),
                           ("rows", "rows"), ("manifest_sha256", "manifest_sha256")):
        if audit_entry[key] != entry[entry_key]:
            raise ValueError(f"Input selection differs from Bronze audit: {key}")
    if not strict_2026:
        return
    if manifest.get("kind") != "fresh":
        raise ValueError("2026 audit inputs must be fresh Bronze runs")
    if manifest.get("source") == "usajobs_historic":
        if (manifest.get("market_scope") != "US federal jobs" or
                not manifest.get("sources") or
                any(source.get("source") != "usajobs_historic" or
                    source.get("position_series") != "2210" or
                    source.get("market_scope") != "US federal jobs"
                    for source in manifest["sources"])):
            raise ValueError("USAJOBS run lacks verified PositionSeries=2210 scope")
    elif manifest.get("source") != "public_api_snapshot":
        raise ValueError("Unexpected source in 2026 input selection")


def load_input_selection(path, expected_sha256, workspace_root=ROOT, *,
                         strict_2026=True, allowed_partial=PARTIAL_ALLOWLIST):
    """Verify a selection file, its audit and every immutable Bronze run.

    The CLI uses strict_2026=True and the fixed partial allowlist. Other values
    are only useful for small, isolated test fixtures.
    """
    root = Path(workspace_root).resolve()
    selection_path = Path(path).resolve()
    if not selection_path.is_relative_to(root):
        raise ValueError("Input selection must be inside the workspace")
    if not expected_sha256 or sha256_file(selection_path) != expected_sha256:
        raise ValueError("Input-selection SHA-256 mismatch")
    contract = json.loads(selection_path.read_text(encoding="utf-8"))
    if contract.get("schema_version") != 1 or not isinstance(contract.get("inputs"), list):
        raise ValueError("Unsupported input-selection contract")
    if strict_2026 and contract.get("selection_kind") != "2026_bronze_to_silver":
        raise ValueError("Expected the 2026 Bronze-to-Silver selection contract")
    audit = _audit_entries(root, contract, strict_2026)
    entries = contract["inputs"]
    if not entries or len(entries) != len(audit):
        raise ValueError("Input selection must match every audited Bronze run")
    selected = []
    seen_ids = set()
    seen_paths = set()
    partials = set()
    for entry in entries:
        required = {"kind", "path", "run_id", "manifest_sha256", "expected_status", "source", "rows"}
        if not isinstance(entry, dict) or not required.issubset(entry):
            raise ValueError("Input selection entry is missing required pinned fields")
        run_id = entry.get("run_id")
        if run_id not in audit or run_id in seen_ids:
            raise ValueError(f"Unexpected or duplicate Bronze run_id: {run_id}")
        seen_ids.add(run_id)
        relative = entry.get("path")
        run_dir = _workspace_path(root, relative)
        if run_dir.name != run_id or run_dir in seen_paths:
            raise ValueError(f"Input path/run_id mismatch or duplicate: {relative}")
        seen_paths.add(run_dir)
        expected_status = entry.get("expected_status")
        pair = (run_id, entry.get("manifest_sha256"))
        allow_partial = expected_status == "partial" and entry.get("allow_partial") is True
        if expected_status not in {"complete", "partial"}:
            raise ValueError(f"Invalid expected Bronze status: {run_id}")
        if expected_status == "partial":
            if not allow_partial or pair not in allowed_partial or entry.get("partial_reason") != "required_for_remotive_snapshot":
                raise ValueError(f"Unexpected partial Bronze run: {run_id}")
            partials.add(pair)
        elif entry.get("allow_partial"):
            raise ValueError(f"Complete run cannot request partial exception: {run_id}")
        manifest_path = run_dir / "manifest.json"
        if sha256_file(manifest_path) != entry.get("manifest_sha256"):
            raise ValueError(f"Bronze manifest SHA-256 mismatch: {run_id}")
        manifest, files, manifest_sha = load_bronze_run(
            run_dir, expected_kind=entry.get("kind"), allow_partial=allow_partial,
        )
        if manifest_sha != entry["manifest_sha256"]:
            raise ValueError(f"Bronze manifest changed during verification: {run_id}")
        _validate_run_metadata(manifest, entry, audit[run_id], strict_2026)
        selected.append({
            "kind": manifest["kind"], "run_id": run_id, "status": manifest["status"],
            "rows": manifest["total_rows"], "source": manifest.get("source"),
            "market_scope": manifest.get("market_scope"),
            "manifest_path": str(manifest_path), "manifest_sha256": manifest_sha,
            "files": files, "sources": manifest.get("sources", []),
        })
    if set(audit) != seen_ids:
        raise ValueError("Input selection does not cover the Bronze audit")
    if strict_2026:
        if partials != PARTIAL_ALLOWLIST:
            raise ValueError("2026 input selection must contain exactly the pinned Remotive partial run")
        sources = Counter(run["source"] for run in selected)
        if sources != {"public_api_snapshot": 2, "usajobs_historic": 21}:
            raise ValueError("2026 input source/run composition differs from audit")
        verify_partial_contribution(selected)
    return selected, contract


def verify_partial_contribution(selected, expected_remotive=15):
    """The only 2026 partial run contributes Remotive, never unique Arbeitnow."""
    partial = next((run for run in selected if run["run_id"] == PARTIAL_RUN_ID), None)
    if partial is None:
        raise ValueError("Pinned Remotive partial run is missing")
    complete_ids = set()
    for run in selected:
        if run["source"] == "public_api_snapshot" and run["status"] == "complete":
            for file in run["files"]:
                for row in json.loads(Path(file).read_text(encoding="utf-8")):
                    if row.get("source") == "arbeitnow":
                        complete_ids.add(str(row.get("source_record_id")))
    partial_ar, partial_rem = set(), []
    for file in partial["files"]:
        for row in json.loads(Path(file).read_text(encoding="utf-8")):
            if row.get("source") == "arbeitnow":
                partial_ar.add(str(row.get("source_record_id")))
            elif row.get("source") == "remotive":
                partial_rem.append(str(row.get("source_record_id")))
            else:
                raise ValueError("Unexpected source in pinned partial run")
    if partial_ar - complete_ids:
        raise ValueError(f"Partial Arbeitnow has {len(partial_ar - complete_ids)} unique IDs; stop for review")
    if len(partial_rem) != expected_remotive or len(set(partial_rem)) != expected_remotive:
        raise ValueError("Pinned partial run does not contribute exactly 15 unique Remotive IDs")
    return {"remotive_unique_from_partial": len(partial_rem),
            "arbeitnow_unique_from_partial": len(partial_ar - complete_ids),
            "arbeitnow_partial_ids_with_complete_lineage": len(partial_ar)}


def build_2026_selection(workspace_root=ROOT):
    """Build the reviewable contract from the exact pinned Bronze audit."""
    root = Path(workspace_root).resolve()
    audit_path = root / AUDIT_PATH
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if len(audit.get("input_runs", [])) != 23:
        raise ValueError("Expected exactly 23 audited Bronze 2026 runs")
    entries = []
    for run in audit["input_runs"]:
        run_id = run["run_id"]
        base = ("data/bronze/us_federal/historic/runs" if run["source"] == "usajobs_historic"
                else "data/bronze/global/fresh/runs")
        entry = {"kind": "fresh", "path": f"{base}/{run_id}", "run_id": run_id,
                 "manifest_sha256": run["manifest_sha256"], "expected_status": run["status"],
                 "source": run["source"], "rows": run["rows"]}
        if run["status"] == "partial":
            if (run_id, run["manifest_sha256"]) not in PARTIAL_ALLOWLIST:
                raise ValueError(f"Unexpected partial run in Bronze audit: {run_id}")
            entry.update({"allow_partial": True, "partial_reason": "required_for_remotive_snapshot"})
        entries.append(entry)
    return {"schema_version": 1, "selection_kind": "2026_bronze_to_silver",
            "audit_path": AUDIT_PATH, "audit_sha256": sha256_file(audit_path),
            "inputs": entries}
