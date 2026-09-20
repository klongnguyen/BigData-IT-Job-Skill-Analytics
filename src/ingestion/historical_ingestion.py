"""
Historical Data Ingestion Module (Bronze Layer):
Reads the raw data_jobs.csv (Luke Barousse dataset), attaches ingestion metadata,
and saves into the Bronze Layer at data/bronze/global/historical/.
"""

import os
import csv
import json
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_CSV_PATH = os.path.join(BASE_DIR, "data", "raw", "data_jobs.csv")
BRONZE_HIST_DIR = os.path.join(BASE_DIR, "data", "bronze", "global", "historical")

os.makedirs(BRONZE_HIST_DIR, exist_ok=True)

def ingest_historical_data(batch_size: int = 100000, limit: int = None):
    print(f"[Historical Ingestion] Starting ingestion from {RAW_CSV_PATH}...")
    if not os.path.exists(RAW_CSV_PATH):
        raise FileNotFoundError(f"Raw historical file not found at {RAW_CSV_PATH}!")

    ingestion_id = str(uuid.uuid4())
    collected_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    total_rows = 0
    batch_num = 1
    current_batch = []

    with open(RAW_CSV_PATH, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Attach Bronze Layer metadata
            row["ingestion_id"] = ingestion_id
            row["collected_at"] = collected_at
            row["market"] = "GLOBAL"
            row["source"] = "kaggle_historical_archive"
            
            current_batch.append(row)
            total_rows += 1

            if len(current_batch) >= batch_size:
                batch_file = os.path.join(BRONZE_HIST_DIR, f"historical_batch_{batch_num:03d}.json")
                with open(batch_file, "w", encoding="utf-8") as out_f:
                    json.dump(current_batch, out_f, ensure_ascii=False)
                print(f"  -> Saved Batch {batch_num}: {len(current_batch):,} rows to {batch_file}")
                batch_num += 1
                current_batch = []

            if limit and total_rows >= limit:
                print(f"  -> Reached limit of {limit:,} rows.")
                break

    # Save remaining rows in final batch
    if current_batch:
        batch_file = os.path.join(BRONZE_HIST_DIR, f"historical_batch_{batch_num:03d}.json")
        with open(batch_file, "w", encoding="utf-8") as out_f:
            json.dump(current_batch, out_f, ensure_ascii=False)
        print(f"  -> Saved Final Batch {batch_num}: {len(current_batch):,} rows to {batch_file}")

    print(f"[Historical Ingestion] Completed! Total {total_rows:,} rows ingested into Bronze Layer.")
    return total_rows

if __name__ == "__main__":
    ingest_historical_data()
