"""Pinned 2026 selection rejects substitution and unauthorized partial inputs."""

import json
import pytest

from src.common.run_manifest import file_entry, sha256_file
from src.processing.input_selection import (
    load_input_selection, verify_partial_contribution, PARTIAL_RUN_ID,
)


def _run(root, run_id, source, rows, status="complete"):
    directory = root / "bronze" / "runs" / run_id
    records = directory / "records"
    records.mkdir(parents=True)
    batch = records / "batch_001.json"
    batch.write_text(json.dumps(rows), encoding="utf-8")
    manifest = {
        "schema_version": 1, "run_id": run_id, "kind": "fresh", "status": status,
        "source": source, "total_rows": len(rows),
        "files": [file_entry(directory, batch, len(rows))],
    }
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return directory, sha256_file(directory / "manifest.json")


def _selection(root, runs):
    audit = {"input_runs": [
        {"run_id": run_id, "status": status, "source": source,
         "rows": rows, "manifest_sha256": manifest_sha}
        for run_id, _, manifest_sha, status, source, rows in runs
    ]}
    (root / "audit.json").write_text(json.dumps(audit), encoding="utf-8")
    contract = {
        "schema_version": 1, "selection_kind": "fixture",
        "audit_path": "audit.json", "audit_sha256": sha256_file(root / "audit.json"),
        "inputs": [
            {"kind": "fresh", "path": directory.relative_to(root).as_posix(),
             "run_id": run_id, "manifest_sha256": manifest_sha,
             "expected_status": status, "source": source, "rows": rows,
             **({"allow_partial": True, "partial_reason": "required_for_remotive_snapshot"}
                if status == "partial" else {})}
            for run_id, directory, manifest_sha, status, source, rows in runs
        ],
    }
    path = root / "selection.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path, contract


def test_selection_rejects_run_id_sha_and_file_tampering(tmp_path):
    directory, manifest_sha = _run(tmp_path, "complete_1", "public_api_snapshot", [
        {"source": "arbeitnow", "source_record_id": "A", "title": "Data Engineer"},
    ])
    path, contract = _selection(tmp_path, [("complete_1", directory, manifest_sha,
                                            "complete", "public_api_snapshot", 1)])
    load_input_selection(path, sha256_file(path), tmp_path, strict_2026=False)
    original_sha = sha256_file(path)
    contract["inputs"][0]["run_id"] = "forged"
    path.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ValueError, match="Input-selection SHA-256 mismatch"):
        load_input_selection(path, original_sha, tmp_path, strict_2026=False)
    with pytest.raises(ValueError, match="run_id"):
        load_input_selection(path, sha256_file(path), tmp_path, strict_2026=False)

    contract["inputs"][0]["run_id"] = "complete_1"
    path.write_text(json.dumps(contract), encoding="utf-8")
    (directory / "manifest.json").write_text('{"forged":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="manifest SHA-256 mismatch"):
        load_input_selection(path, sha256_file(path), tmp_path, strict_2026=False)


def test_unexpected_partial_fails_closed(tmp_path):
    directory, manifest_sha = _run(tmp_path, "other_partial", "public_api_snapshot", [
        {"source": "remotive", "source_record_id": "R"},
    ], status="partial")
    path, _ = _selection(tmp_path, [("other_partial", directory, manifest_sha,
                                     "partial", "public_api_snapshot", 1)])
    with pytest.raises(ValueError, match="Unexpected partial"):
        load_input_selection(path, sha256_file(path), tmp_path, strict_2026=False)


def test_partial_arbeitnow_must_be_covered_by_complete_run(tmp_path):
    partial_rows = [{"source": "arbeitnow", "source_record_id": "A"}] + [
        {"source": "remotive", "source_record_id": f"R{i}"} for i in range(15)
    ]
    partial_dir, partial_sha = _run(tmp_path, PARTIAL_RUN_ID, "public_api_snapshot",
                                    partial_rows, status="partial")
    full_dir, full_sha = _run(tmp_path, "complete_1", "public_api_snapshot", [
        {"source": "arbeitnow", "source_record_id": "A"},
    ])
    selected = [
        {"run_id": PARTIAL_RUN_ID, "source": "public_api_snapshot",
         "status": "partial", "files": [str(partial_dir / "records" / "batch_001.json")],
         "manifest_sha256": partial_sha},
        {"run_id": "complete_1", "source": "public_api_snapshot",
         "status": "complete", "files": [str(full_dir / "records" / "batch_001.json")],
         "manifest_sha256": full_sha},
    ]
    assert verify_partial_contribution(selected) == {
        "remotive_unique_from_partial": 15,
        "arbeitnow_unique_from_partial": 0,
        "arbeitnow_partial_ids_with_complete_lineage": 1,
    }
    full_file = full_dir / "records" / "batch_001.json"
    full_file.write_text(json.dumps([{"source": "arbeitnow", "source_record_id": "B"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="Partial Arbeitnow"):
        verify_partial_contribution(selected)
