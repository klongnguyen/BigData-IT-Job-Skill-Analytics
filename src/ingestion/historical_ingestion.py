"""Stream a historical CSV into an immutable, checksummed Bronze run."""

import argparse
import csv
import hashlib
import json
import uuid
from pathlib import Path

from src.common.run_manifest import (
    discard_stage, file_entry, publish_run, sha256_file, start_run, utc_now,
)


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_CSV_PATH = BASE_DIR / "data" / "raw" / "data_jobs.csv"
BRONZE_HIST_DIR = BASE_DIR / "data" / "bronze" / "global" / "historical"


def ingest_historical_data(batch_size=100000, limit=None, raw_csv_path=RAW_CSV_PATH,
                           bronze_dir=BRONZE_HIST_DIR):
    if batch_size <= 0 or (limit is not None and limit <= 0):
        raise ValueError("batch_size and limit must be positive")
    raw_csv_path = Path(raw_csv_path)
    if not raw_csv_path.is_file():
        raise FileNotFoundError(f"Raw historical file not found: {raw_csv_path}")

    started_at = utc_now()
    input_checksum = sha256_file(raw_csv_path)
    run_id, stage, final = start_run(bronze_dir)
    ingestion_id = str(uuid.uuid4())
    collected_at = utc_now()
    entries = []
    batch = []
    total_rows = 0
    limit_reached = False

    def write_batch():
        nonlocal batch
        path = stage / "records" / f"historical_batch_{len(entries) + 1:03d}.json"
        with path.open("x", encoding="utf-8") as stream:
            json.dump(batch, stream, ensure_ascii=False)
        entries.append(file_entry(stage, path, len(batch)))
        batch = []

    try:
        with raw_csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                raw = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                checksum = hashlib.sha256(raw.encode("utf-8")).hexdigest()
                row.update({
                    "ingestion_id": ingestion_id,
                    "collected_at": collected_at,
                    "market": "GLOBAL",
                    "source": "kaggle_historical_archive",
                    "source_record_id": checksum,
                    "raw_checksum": checksum,
                    "source_url": None,
                })
                batch.append(row)
                total_rows += 1
                if len(batch) == batch_size:
                    write_batch()
                if limit is not None and total_rows >= limit:
                    limit_reached = True
                    break
        if batch:
            write_batch()
        if not entries:
            raise ValueError("Historical CSV has no data rows")
        manifest = {
            "run_id": run_id,
            "kind": "historical",
            "source": "kaggle_historical_archive",
            "status": "partial" if limit_reached else "complete",
            "coverage": "limited" if limit_reached else "full_input",
            "started_at": started_at,
            "finished_at": utc_now(),
            "ingestion_id": ingestion_id,
            "input": {
                "path": str(raw_csv_path.resolve()),
                "bytes": raw_csv_path.stat().st_size,
                "sha256": input_checksum,
                "limit": limit,
            },
            "files": entries,
            "total_rows": total_rows,
        }
        manifest_path = publish_run(stage, final, manifest)
    except Exception:
        discard_stage(stage)
        raise
    print(f"[Historical Ingestion] {total_rows:,} rows; manifest: {manifest_path}")
    return total_rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-csv", default=RAW_CSV_PATH)
    parser.add_argument("--bronze-dir", default=BRONZE_HIST_DIR)
    parser.add_argument("--batch-size", type=int, default=100000)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    ingest_historical_data(batch_size=args.batch_size, limit=args.limit,
                           raw_csv_path=args.raw_csv, bronze_dir=args.bronze_dir)
