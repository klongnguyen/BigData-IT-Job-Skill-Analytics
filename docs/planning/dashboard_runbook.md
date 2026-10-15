# Runbook dashboard JobScope

JobScope đọc năm bảng Gold mô tả đã audit. Catalog `docs/data/dashboard_gold_catalog.json` pin hai dataset: `legacy_2023` trong `data/gold/global/runs` và `scoped_2026` trong `data/gold/jobscope/runs`. Không chọn “latest” hoặc đường dẫn tùy ý. Gold 2026 có 8.370 tin analytical, tách `GLOBAL` và `US_FEDERAL`.

## Cài và chạy trên Windows

```powershell
python -m venv .venv-dashboard
.\.venv-dashboard\Scripts\python.exe -m pip install -r requirements-dashboard.txt
.\.venv-dashboard\Scripts\python.exe -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501
```

Mở <http://127.0.0.1:8501>. Dùng `Ctrl+C` để dừng. Nếu cổng bận, đổi `--server.port 8502`. Mặc định là Parquet; không cần Spark/Java khi xem dashboard.

## Artifact bắt buộc

- Gold 2023: `data/gold/global/runs/20261004T110131548191Z-e38fa7303cf4`, manifest SHA-256 `2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d`.
- Gold 2026: `data/gold/jobscope/runs/20261015T144634600577Z-8d531796a5f6`, manifest SHA-256 `c9208520cecf115591d524120fc13bc1501de893a30897072e0f61c30c3cf1cd`.
- Mỗi run phải có manifest và đủ `market_stats`, `occupation_stats`, `skill_evidence_stats`, `skill_stats`, `skill_trends`. Các Parquet lớn ở local, không nằm trong Git; clone mới cần khôi phục đúng run từ bản lưu hoặc tái chạy pipeline.

Loader kiểm tra SHA của audit, manifest, danh sách và SHA output, số dòng, schema và khóa. Đường dẫn tuyệt đối trong audit/manifest không được tin để chọn run. Nếu mất hoặc sai checksum, dashboard báo lỗi và không dùng dữ liệu thay thế. [Gold audit 2026](../data/2026_gold_run_audit.json) là bằng chứng số liệu; [báo cáo cuối](../final/FINAL_REPORT_2026-10-15.md) giải thích giới hạn.

## MongoDB cho Gold cũ

Backend MongoDB đã được publish/audit cho **Gold 2023**. Nếu MongoDB local chạy ở `mongodb://127.0.0.1:27017`:

```powershell
.\.venv-dashboard\Scripts\python.exe -m src.serving.mongo_gold
$env:JOB_GOLD_BACKEND = 'mongo'
.\.venv-dashboard\Scripts\python.exe -m streamlit run dashboard/app.py --server.port 8502
```

`legacy_2023` đọc Mongo có [serving audit](../data/mongo_serving_audit.json); `scoped_2026` vẫn đọc Parquet audit. Có thể đặt `JOB_MONGO_URI` và `JOB_MONGO_DB`. Tránh ghi URI có mật khẩu vào Git.

## Thao tác demo và diễn giải

Chọn Dataset → Market → Source → Month → Occupation. Với scoped 2026, `GLOBAL` chứa Arbeitnow 1.621 và Remotive 10; `US_FEDERAL` chứa USAJOBS 2210: 6.739. Không trộn mẫu số. Trang “Dữ liệu 2026” hiển thị 21.435 raw → 19.706 unique → 8.370 Silver → 5 Gold; 548 excluded và 10.788 unresolved lưu riêng. 10.788 unresolved không phải non-IT. USAJOBS thiếu skill evidence chuẩn hóa; tỷ lệ kỹ năng để trống. Tháng không quan sát là gap, không điền 0. `NO_GO` trên trang dự báo áp dụng toàn run, không đổi khi lọc.

## Kiểm thử trước giờ báo cáo

```powershell
.\.venv-dashboard\Scripts\python.exe -m pytest -q tests/test_dashboard.py tests/test_mongo_gold.py
git diff --check
```

Mở cả hai dataset, thử bộ lọc `GLOBAL`/`US_FEDERAL`, mở sáu trang, xác nhận không có exception. Kiểm tra [demo script](../final/DEMO_SCRIPT.md). HDFS lab một DataNode, taxonomy chưa có ground truth độc lập và forecast `NO_GO` vẫn là giới hạn cần trình bày.
