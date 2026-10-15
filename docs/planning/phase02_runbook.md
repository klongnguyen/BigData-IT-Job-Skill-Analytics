# Runbook Phase 02 — ingestion, ETL và HDFS gate

## Bổ sung Bronze 2026 (15/10/2026)

Arbeitnow và Remotive là snapshot tin đang hoạt động; USAJOBS Historic `PositionSeries=2210` là dữ liệu quá khứ của riêng khu vực liên bang Mỹ. Chạy từng nguồn vào run bất biến, không ghi đè run cũ:

```powershell
python -m src.ingestion.fresh_ingestion --source arbeitnow --max-pages 100 --request-delay-seconds 1
python -m src.ingestion.fresh_ingestion --source remotive --max-pages 1
python -m src.ingestion.usajobs_historic_ingestion --start-date 2026-01-01 --end-date 2026-01-14 --max-pages 5
```

Với USAJOBS, lặp các khoảng tối đa 14 ngày đến ngày cần thu, xác minh mọi manifest `status=complete`, `coverage=complete` và các khoảng nối liền trước khi audit. Truy vấn cả tháng có thể trả 500 dòng rồi trang tiếp theo rỗng, nên run tháng đó phải coi là `partial` và chia nhỏ. Audit nhận **đường run cụ thể** để không quét nhầm run thử/partial:

```powershell
python -m src.collection.audit_2026_bronze <run-dir-1> <run-dir-2> ... --through-month 2026-10 --output docs/data/2026_ingestion_audit.json
```

Kiểm tra `input_runs`, `us_federal_window_coverage`, `duplicate_source_records_removed`, `title_classification` và từng `source_month_counts` trong audit. Dữ liệu Bronze local được `.gitignore` bỏ qua; [báo cáo 2026](../reviews/2026_DATA_EXPANSION_2026-10-15.md) chỉ rõ số liệu của đợt đã thu. Chưa dùng audit này để thay run Silver/Gold đã khóa.

USAJOBS `teleworkEligible=Y` chỉ là đủ điều kiện telework, không chuyển thành `Remote`; khi thiếu chỉ báo remote riêng, Bronze để `remote=null`. `positionlocations` có thể gồm nhiều nơi và phải giữ toàn bộ. Khi đưa Arbeitnow lên giao diện, đặt liên kết về Arbeitnow.com theo [điều khoản API](https://www.arbeitnow.com/terms); Remotive cũng yêu cầu ghi nguồn và liên kết tin gốc.

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

## 5. Kết quả Docker HDFS ngày 15/10/2026

[Review M2](../reviews/M2_HDFS_REVIEW_2026-10-15.md) đã đối chiếu hai smoke run trên Docker HDFS tại `hdfs://namenode:8020/bigdata_job_analy`:

| Bronze run | Trạng thái nguồn | Evidence | Input → output |
|---|---|---|---:|
| `20261004T103235056713Z-0811f6613d3c` | Historical `complete/full_input` | [`20261014T173656587825Z-9aee99826405`](../../data/manifests/hdfs/hdfs_smoke_20261014T173656587825Z-9aee99826405.json) | **785.741 → 785.741** |
| `20261004T075332383635Z-c9fddef628d7` | Fresh `partial/scoped` | [`20261014T173838902471Z-542df647c8cf`](../../data/manifests/hdfs/hdfs_smoke_20261014T173838902471Z-542df647c8cf.json) | **666 → 666** |

Trong container `project-smoke` có mount repo tại `/workspace` và `PHASE02_HDFS_URI=hdfs://namenode:8020/bigdata_job_analy`, kiểm tra lại bằng:

```bash
cd /workspace
python -m pytest -q tests/test_phase02_hdfs.py
python -m pytest -q tests --ignore=tests/test_dashboard.py
```

Lần kiểm tra 15/10: **2 passed, 0 skipped** cho live HDFS và **27 passed, 0 skipped** cho pipeline. Trên host, có thể dùng `docker exec hdfs-namenode hdfs dfsadmin -report` và `docker exec hdfs-namenode hdfs fsck /bigdata_job_analy/phase02_smoke/<run-id> -files -blocks` để xác minh DataNode/block. Các file smoke hiện đọc được và FSCK trả `HEALTHY`, nhưng nhiều block yêu cầu 3 replica trong cluster chỉ có một DataNode, nên báo under-replicated.

Smoke này **không chạy ETL tạo Silver**. Cổng kỹ thuật HDFS → Spark đã đạt; M2 còn cần quyết định phạm vi nghiệm thu và bằng chứng vận hành nêu trong review. Docker Compose của máy review nằm ngoài repo; cần cung cấp cấu hình tương đương nếu muốn tái lập ở máy khác.
