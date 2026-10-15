"""Create a portable summary of a completed HDFS Bronze to Silver ETL run."""

import argparse
import json
from pathlib import Path

from src.common.run_manifest import sha256_file
from src.processing.spark_etl import _directory_evidence


def audit_hdfs_etl(manifest_path):
    path = Path(manifest_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("bronze_storage") != "hdfs":
        raise ValueError("Expected a completed ETL run that read Bronze from HDFS")
    metrics = manifest["metrics"]
    if metrics["input_rows"] != metrics["valid_rows"] + metrics["quarantine_rows"] or \
            metrics["valid_rows"] != metrics["silver_rows"] + metrics["identity_duplicates_removed"] or \
            metrics["silver_rows"] != metrics["provenance_rows"]:
        raise ValueError("ETL row accounting does not reconcile")
    if sum(run["rows"] for run in manifest["input_runs"]) != metrics["input_rows"]:
        raise ValueError("Bronze run counts do not reconcile")
    for run in manifest["input_runs"]:
        if not run.get("hdfs_records_uris") or not all(
                uri.startswith("hdfs://") for uri in run["hdfs_records_uris"]):
            raise ValueError("A Bronze run has no genuine HDFS input URI")
        if sha256_file(run["manifest_path"]) != run["manifest_sha256"]:
            raise ValueError("Bronze manifest checksum mismatch")
    outputs = {}
    for name in ("silver", "provenance", "quarantine"):
        declared = manifest["outputs"][name]
        actual = _directory_evidence(declared["path"])
        if actual != {"sha256": declared["sha256"], "files": declared["files"]}:
            raise ValueError(f"ETL output checksum mismatch: {name}")
        outputs[name] = actual["sha256"]
    return {
        "schema_version": 1, "run_id": manifest["run_id"],
        "completed_at": manifest["completed_at"],
        "etl_manifest_sha256": sha256_file(path),
        "bronze_storage": "hdfs", "hdfs_root": manifest["hdfs_root"],
        "input_runs": [{key: run[key] for key in
                        ("kind", "run_id", "status", "rows", "manifest_sha256", "hdfs_records_uris")}
                       for run in manifest["input_runs"]],
        "metrics": metrics, "output_sha256": outputs,
        "environment": manifest["environment"],
        "interpretation": "HDFS Bronze was read by the normalization ETL; Silver and provenance were written locally."
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    evidence = audit_hdfs_etl(args.manifest)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": evidence["run_id"], "metrics": evidence["metrics"]}))
