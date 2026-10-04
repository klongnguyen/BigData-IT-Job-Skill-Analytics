"""Immutable local Bronze runs and verifiable input manifests."""

import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path


RUN_SCHEMA_VERSION = 1


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_run_id():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{stamp}-{uuid.uuid4().hex[:12]}"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def start_run(bronze_root, run_id=None):
    run_id = run_id or new_run_id()
    if not run_id.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Run ID must be alphanumeric with hyphens or underscores")
    runs_root = Path(bronze_root).resolve() / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    stage = runs_root / f".staging-{run_id}"
    final = runs_root / run_id
    if final.exists():
        raise FileExistsError(f"Bronze run already exists: {final}")
    stage.mkdir(exist_ok=False)
    (stage / "records").mkdir()
    return run_id, stage, final


def discard_stage(stage):
    stage = Path(stage).resolve()
    if stage.name.startswith(".staging-") and stage.parent.name == "runs" and stage.is_dir():
        shutil.rmtree(stage)


def file_entry(stage, path, rows):
    path = Path(path)
    return {
        "path": path.relative_to(stage).as_posix(),
        "rows": rows,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def publish_run(stage, final, manifest):
    stage = Path(stage)
    final = Path(final)
    manifest["schema_version"] = RUN_SCHEMA_VERSION
    manifest_path = stage / "manifest.json"
    with manifest_path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
    if final.exists():
        raise FileExistsError(f"Bronze run already exists: {final}")
    os.replace(stage, final)
    return final / "manifest.json"


def load_bronze_run(run_dir, expected_kind=None, allow_partial=False):
    """Validate all listed files before an ETL run consumes this local input."""
    run_dir = Path(run_dir).resolve()
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != RUN_SCHEMA_VERSION:
        raise ValueError(f"Unsupported Bronze manifest schema: {manifest_path}")
    if expected_kind and manifest.get("kind") != expected_kind:
        raise ValueError(f"Expected {expected_kind} run: {manifest_path}")
    if manifest.get("status") != "complete" and not allow_partial:
        raise ValueError(f"Bronze run is {manifest.get('status')}; pass allow_partial explicitly")
    if run_dir.name != manifest.get("run_id"):
        raise ValueError(f"Run ID does not match directory: {manifest_path}")
    files = []
    entries = manifest.get("files") or []
    if not entries:
        raise ValueError(f"Bronze run contains no listed records: {manifest_path}")
    for entry in entries:
        relative = Path(entry["path"])
        path = (run_dir / relative).resolve()
        if path.parent != (run_dir / "records").resolve() or path.suffix != ".json":
            raise ValueError(f"Unsafe Bronze record path: {relative}")
        if path.stat().st_size != entry["bytes"] or sha256_file(path) != entry["sha256"]:
            raise ValueError(f"Bronze record checksum mismatch: {path}")
        records = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(records, list) or len(records) != entry["rows"]:
            raise ValueError(f"Bronze record row count mismatch: {path}")
        files.append(str(path))
    if sum(entry["rows"] for entry in entries) != manifest.get("total_rows"):
        raise ValueError(f"Bronze manifest row total mismatch: {manifest_path}")
    return manifest, files, sha256_file(manifest_path)
