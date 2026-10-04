# Runbook Phase 02 — ingestion, ETL và HDFS gate

## Môi trường đã kiểm tra

Lượt local ngày 04/10/2026 dùng Python 3.11.9, PySpark 4.2.0, Java 17.0.10. Cài dependency Phase 02 bằng `python -m pip install -r requirements-phase02.txt`. PySpark đọc `JAVA_HOME` từ môi trường; mã không tự gán đường dẫn JDK/Hadoop theo máy.

Trên Windows của lượt kiểm tra này, Java cần thư mục tạm có đường dẫn ngắn để khởi tạo SparkContext. Trước khi chạy Spark trong PowerShell:

```powershell
New-Item -ItemType Directory -Path 'C:\jtmp' -Force | Out-Null
$env:TEMP = 'C:\jtmp'
$env:TMP = 'C:\jtmp'
```

Đây là cấu hình cho môi trường đã thử, không phải yêu cầu chung của Spark. `SPARK_MASTER`, `SPARK_DRIVER_MEMORY` và `SPARK_SHUFFLE_PARTITIONS` có thể cấu hình qua biến môi trường; mặc định lần lượt là `local[2]`, `4g`, `8`.

## 1. Tạo Bronze run bất biến

```powershell
python -m src.ingestion.historical_ingestion --raw-csv data/raw/data_jobs.csv --bronze-dir tmp/phase02_acceptance/historical --batch-size 10000 --limit 50000
python -m src.ingestion.fresh_ingestion --bronze-dir tmp/phase02_acceptance/fresh --max-pages 2
```

Mỗi lệnh tạo `runs/<run_id>/manifest.json` và `records/*.json`, không thay file của run trước. `--limit` và `--max-pages` tạo input **partial/scoped**; manifest ghi rõ phạm vi, trạng thái từng nguồn, checksum và count. Chọn đúng hai thư mục `runs/<run_id>` cần ETL; không trỏ ETL tới thư mục gốc chứa mọi snapshot.

## 2. Chạy ETL trên input đã chọn

```powershell
python -m src.processing.spark_etl --historical-run <historical-run-dir> --fresh-run <fresh-run-dir> --allow-partial-inputs --silver-dir tmp/phase02_acceptance/silver --provenance-dir tmp/phase02_acceptance/provenance --quarantine-dir tmp/phase02_acceptance/quarantine --manifest-dir tmp/phase02_acceptance/etl_manifests
```

`--allow-partial-inputs` chỉ cho phép chạy một mẫu có giới hạn, không biến mẫu đó thành dữ liệu đầy đủ. ETL từ chối ghi đè output đã tồn tại. Muốn chạy lại, dùng đường output mới; chỉ dùng `--replace-existing` khi chủ ý thay bản cũ và giữ backup. Manifest ETL chỉ được publish sau khi các output Silver/provenance/quarantine đã ghi và được kiểm tra lại. Đối chiếu `input_rows = valid_rows + quarantine_rows`, `valid_rows = silver_rows + identity_duplicates_removed`, `silver_rows = provenance_rows = unique_job_ids`.

## 3. Test

```powershell
python -m pytest -q
```

Các test Bronze/identity dùng fixture tạm. Test Spark dùng fixture nhỏ và tự skip nếu SparkContext của máy không khởi tạo được; skip này phải được báo như một giới hạn kiểm chứng. Test HDFS cần `PHASE02_HDFS_URI` và không được tính là đạt khi bị skip.

## 4. Cổng HDFS thật cho M2

```powershell
python -m src.processing.hdfs_smoke --bronze-run <bronze-run-dir> --allow-partial --hdfs-root hdfs://<host>:<port>/<absolute-path>
```

Lệnh này yêu cầu URI có scheme `hdfs://`, upload file Bronze vào HDFS, đọc bằng Spark, ghi Parquet lên HDFS và đọc lại để so số dòng. Chỉ manifest `data/manifests/hdfs/hdfs_smoke_<run_id>.json` có `status=completed`, URI thật và count khớp mới là bằng chứng kỹ thuật cho HDFS. Sau đó cần đối chiếu thêm phạm vi input và điều kiện dữ liệu trong Final Plan trước khi đóng M2. Không dùng `file://`, thư mục local hoặc test bị skip để thay bằng chứng HDFS.
