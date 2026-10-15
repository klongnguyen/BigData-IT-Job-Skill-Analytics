# Kịch bản demo và bàn giao

## Chuẩn bị

1. Kiểm tra Python 3.11, `.venv-dashboard`, MongoDB local và Gold run được audit pin. Bản clone Git cần khôi phục `data/gold/global/runs/20261004T110131548191Z-e38fa7303cf4` trước khi publish Mongo.
2. Đối chiếu [Gold audit](../data/phase03_analytics_audit.json), [Mongo audit](../data/mongo_serving_audit.json), [HDFS ETL audit](../data/m2_hdfs_etl_audit.json). Không đổi thủ công run ID.
3. Khởi động dashboard Mongo từ gốc repository:

```powershell
./.venv-dashboard/Scripts/python.exe -m src.serving.mongo_gold
$env:JOB_GOLD_BACKEND = 'mongo'
./run_dashboard.ps1 -Port 8502
```

Mở <http://127.0.0.1:8502>. Nếu Mongo không có trên máy trình bày, bỏ biến `JOB_GOLD_BACKEND` và chạy Parquet trên cổng 8501 sau khi đã khôi phục Gold run.

## Trình tự thuyết trình (6–8 phút)

1. **Tổng quan:** chọn archive 2023; chỉ ra số tin, coverage, 12 tháng quan sát và nguồn. Nói rõ mẫu archive một năm.
2. **Nhóm nghề:** xem tỷ trọng trong cùng nguồn; đổi bộ lọc nghề/tháng và giải thích mẫu số.
3. **Kỹ năng & xu hướng:** chọn một nghề và kỹ năng, chỉ ra `skills_origin`; khoảng trống tháng không được nối đường.
4. **So sánh nghề:** chọn hai nghề trong cùng nguồn, giải thích mỗi nghề có mẫu số riêng.
5. **Dữ liệu 2026:** chỉ ra 19.706 ID Bronze theo nguồn; chọn USAJOBS và Arbeitnow để thấy phạm vi khác nhau; nhắc 91,7% title chưa khớp taxonomy và dữ liệu này chưa vào Gold.
6. **Dự báo & bằng chứng:** mở `NO_GO`, cho thấy gate, 32 tháng không quan sát và lý do không có model/nhãn dự báo.

## Bằng chứng đường dữ liệu HDFS

Môi trường Docker Compose hiện đặt ngoài repo tại `C:\Users\KIM LONG\docker-hdfs\docker-compose.yml`. Bài chạy đã hoàn tất với Bronze fresh cũ. Khi cần tái chạy, dùng output **mới** dưới `tmp/` để không thay run đã khóa:

```powershell
docker compose -f 'C:\Users\KIM LONG\docker-hdfs\docker-compose.yml' up -d namenode datanode project-smoke
docker exec hdfs-project-smoke python -m src.processing.spark_etl --fresh-run /workspace/tmp/phase02_acceptance/fresh/runs/20261004T075332383635Z-c9fddef628d7 --allow-partial-inputs --hdfs-root hdfs://namenode:8020/bigdata_job_analy --silver-dir /workspace/tmp/m2_hdfs_etl_rerun/silver --provenance-dir /workspace/tmp/m2_hdfs_etl_rerun/provenance --quarantine-dir /workspace/tmp/m2_hdfs_etl_rerun/quarantine --manifest-dir /workspace/tmp/m2_hdfs_etl_rerun/manifests
```

Run ID mới sẽ khác; tạo audit mới bằng `python -m src.processing.hdfs_etl_audit --manifest <manifest mới> --output <audit mới>` trong container. Không ghi đè [audit run đã kiểm chứng](../data/m2_hdfs_etl_audit.json) nếu chưa đối chiếu đầy đủ.

## Kiểm thử trước giờ demo

```powershell
docker exec hdfs-project-smoke python -m pytest -q tests --ignore=tests/test_dashboard.py --ignore=tests/test_mongo_gold.py
./.venv-dashboard/Scripts/python.exe -m pytest -q tests/test_dashboard.py tests/test_mongo_gold.py
git diff --check
```

Nếu dashboard báo thiếu Gold/Mongo, kiểm tra đúng run trong audit và artifact local. Không chuyển sang run khác chỉ để demo có số. Nếu Mongo chưa chạy, xem hướng dẫn khôi phục Parquet trong [runbook](../planning/dashboard_runbook.md).
