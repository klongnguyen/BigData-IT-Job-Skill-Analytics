"""Prove a real HDFS Bronze upload -> Spark read -> HDFS Parquet round trip."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from src.common.run_manifest import load_bronze_run, new_run_id, utc_now
from src.processing.spark_etl import create_spark_session


def run_hdfs_smoke(bronze_run, hdfs_root, evidence_dir=None, allow_partial=False):
    parsed = urlparse(hdfs_root)
    if parsed.scheme != "hdfs" or not parsed.netloc or not parsed.path.startswith("/"):
        raise ValueError("--hdfs-root must be a genuine hdfs://host:port/absolute/path URI")
    manifest, files, checksum = load_bronze_run(bronze_run, allow_partial=allow_partial)
    run_id = new_run_id()
    run_base = hdfs_root.rstrip("/") + "/phase02_smoke/" + run_id
    bronze_uri = run_base + "/bronze"
    output_uri = run_base + "/parquet"
    spark = create_spark_session()
    try:
        jvm = spark.sparkContext._jvm
        conf = spark.sparkContext._jsc.hadoopConfiguration()
        fs = jvm.org.apache.hadoop.fs.FileSystem.get(jvm.java.net.URI(hdfs_root), conf)
        if fs.getScheme() != "hdfs":
            raise RuntimeError("Resolved filesystem is not HDFS")
        bronze_path = jvm.org.apache.hadoop.fs.Path(bronze_uri)
        if fs.exists(bronze_path):
            raise FileExistsError(f"HDFS run path already exists: {bronze_uri}")
        if not fs.mkdirs(bronze_path):
            raise RuntimeError(f"Could not create HDFS Bronze path: {bronze_uri}")
        for local_file in files:
            src = jvm.org.apache.hadoop.fs.Path(Path(local_file).resolve().as_uri())
            dst = jvm.org.apache.hadoop.fs.Path(bronze_uri + "/" + Path(local_file).name)
            fs.copyFromLocalFile(src, dst)
            if not fs.exists(dst):
                raise AssertionError(f"HDFS upload not visible: {dst}")

        frame = spark.read.option("multiline", "true").json(bronze_uri + "/*.json")
        input_rows = frame.count()
        if input_rows != manifest["total_rows"]:
            raise AssertionError("Spark HDFS input count does not match Bronze manifest")
        frame.write.mode("errorifexists").parquet(output_uri)
        output_rows = spark.read.parquet(output_uri).count()
        if output_rows != input_rows:
            raise AssertionError("HDFS Parquet read-back count does not match input")
        evidence = {
            "schema_version": 1,
            "status": "completed",
            "run_id": run_id,
            "completed_at": utc_now(),
            "hdfs_uri": str(fs.getUri()),
            "bronze_uri": bronze_uri,
            "output_uri": output_uri,
            "input_manifest": str(Path(bronze_run).resolve() / "manifest.json"),
            "input_manifest_sha256": checksum,
            "input_rows": input_rows,
            "output_rows": output_rows,
            "spark_version": spark.version,
            "spark_master": spark.sparkContext.master,
            "java_version": jvm.java.lang.System.getProperty("java.version"),
        }
    finally:
        spark.stop()

    evidence_root = Path(evidence_dir or Path(__file__).resolve().parents[2] / "data" / "manifests" / "hdfs")
    evidence_root.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_root / f"hdfs_smoke_{run_id}.json"
    with evidence_path.open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, indent=2, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
    return evidence_path


def _parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bronze-run", required=True)
    parser.add_argument("--hdfs-root", required=True)
    parser.add_argument("--evidence-dir")
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    print(run_hdfs_smoke(args.bronze_run, args.hdfs_root,
                         evidence_dir=args.evidence_dir, allow_partial=args.allow_partial))
