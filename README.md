# BigData Job Analy — báo cáo tiến độ và hướng dẫn chạy

**Cập nhật:** 15/10/2026 · **Phạm vi:** phân tích tin tuyển dụng IT theo nguồn, nghề, kỹ năng và tháng. Việt Nam chưa nằm trong MVP. Dự báo ở trạng thái **`NO_GO`** theo [Final Plan](FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md).

## Trạng thái hiện tại

Pipeline Bronze → Spark Silver → Gold mô tả đã tạo **786.300 tin Silver** và **5 bảng Gold** từ archive 2023 cùng snapshot API 666 tin. Gold run `20261004T110131548191Z-e38fa7303cf4` được khóa bằng [audit](docs/data/phase03_analytics_audit.json). Dashboard JobScope hiện có **6 trang**: tổng quan, nghề, kỹ năng và xu hướng, so sánh nghề, bằng chứng `NO_GO`, và kiểm kê Bronze 2026.

Đợt thu mới năm 2026 có **19.706 ID nguồn duy nhất** trong [23 run Bronze đã audit](docs/data/2026_ingestion_audit.json): Arbeitnow 12.952, Remotive 15, USAJOBS Historic series 2210 là 6.739. Trang kiểm kê 2026 hiển thị các số Bronze này **riêng**; chưa đưa chúng vào Gold vì 91,7% tiêu đề chưa khớp tám nhóm nghề và chưa có tập nhãn độc lập để đánh giá. `US_FEDERAL` không gộp vào `GLOBAL`.

Đường **HDFS Bronze → Spark ETL → Silver/provenance** đã chạy thật với run fresh 666 dòng: 666 valid, 5 ID trùng được gộp, 661 Silver và 661 provenance, 0 quarantine. [Audit HDFS ETL](docs/data/m2_hdfs_etl_audit.json) khóa SHA của manifest và các output. HDFS FSCK riêng run này `HEALTHY`, 0 block thiếu/hỏng/under-replicated sau khi đặt replica 1 cho lab một DataNode. Run cũ 786.300 Silver vẫn là Gold chính; bài thử HDFS 661 tin là đường tích hợp riêng.

**MongoDB serving** đã nhận đủ 5 bảng của Gold run đã khóa. Dashboard có thể đọc Parquet hoặc MongoDB, đối chiếu [serving audit](docs/data/mongo_serving_audit.json) với run/hash/số dòng. MongoDB local và raw Parquet/Bronze lớn không được đưa lên Git; clone mới cần khôi phục artifact hoặc tái chạy pipeline. Dashboard Mongo đang phục vụ local tại [http://127.0.0.1:8502](http://127.0.0.1:8502) trong phiên làm việc này.

## Milestone

| Mốc | Bằng chứng triển khai | Điều kiện còn mở |
|---|---|---|
| M2 · Ingestion/HDFS | HDFS smoke và HDFS→ETL→Silver đạt trên run fresh đã khóa; Bronze 2026 được audit. | Thu snapshot nhiều kỳ, kiểm tra ổn định nguồn và nghiệm thu lab một DataNode. |
| M3 · Silver | 786.300 Silver/provenance 1:1, có dedup và quarantine. | Biên bản nghiệm thu dataset. |
| M4 · Occupation–Skill | Taxonomy v0.1 và [công cụ lấy mẫu/đánh giá](src/skills/label_eval.py); mẫu 95 tin được tạo local. | Gán nhãn độc lập JD thật và đo precision/recall/F1 trước khi đổi taxonomy hoặc dùng Bronze 2026 làm Gold. |
| M5 · Analytics | 5 bảng Gold mô tả, checksum và công thức trong [báo cáo Phase 03](docs/reviews/PHASE_03_ANALYTICS_REPORT.md). | Nghiệm thu phạm vi nguồn và phân tích. |
| M6/M7 · Dự báo | [Hồ sơ `NO_GO` có bằng chứng](docs/reviews/M7_NO_GO_ACCEPTANCE.md). | M6/model không đủ điều kiện; nhánh M7 `NO_GO` chờ nhóm/giảng viên chấp thuận. |
| M8 · Serving | Parquet và MongoDB phục vụ cùng Gold run, đọc lại 5 bảng đạt. | Nghiệm thu triển khai trên môi trường bàn giao. |
| M9 · Dashboard | 6 trang, AppTest và HTTP health đạt; xem [runbook](docs/planning/dashboard_runbook.md). | Demo và ký nghiệm thu. |
| M10 · Final | [Báo cáo cuối](docs/final/FINAL_REPORT_2026-10-15.md), [slide nội dung](docs/final/PRESENTATION.md), [kịch bản demo](docs/final/DEMO_SCRIPT.md), kiểm thử đã tổng hợp. | Chấp thuận các giới hạn dữ liệu/milestone và thuyết trình chính thức. |

Không có nhãn dự báo Growing/Stable/Declining, metric mô hình hoặc dự báo tương lai: khoảng trống 2024–2025, khác biệt nguồn và taxonomy chưa được kiểm định làm gate `NO_GO`.

## Chạy dashboard

Windows, Python 3.11:

```powershell
python -m venv .venv-dashboard
./.venv-dashboard/Scripts/python.exe -m pip install -r requirements-dashboard.txt
./run_dashboard.ps1
```

Mặc định đọc Parquet tại [http://127.0.0.1:8501](http://127.0.0.1:8501). Để đọc Gold đã publish lên MongoDB local:

```powershell
./.venv-dashboard/Scripts/python.exe -m src.serving.mongo_gold
$env:JOB_GOLD_BACKEND = 'mongo'
./run_dashboard.ps1 -Port 8502
```

MongoDB URI mặc định `mongodb://127.0.0.1:27017`, database `jobscope`; có thể đặt `JOB_MONGO_URI` và `JOB_MONGO_DB`. Lệnh publish kiểm chứng Parquet, ghi/đọc lại Mongo và tạo audit pin; chạy lại cùng run chỉ xác minh, không nhân bản. Xem [runbook](docs/planning/dashboard_runbook.md) để khôi phục Gold hoặc chạy demo.

## Kiểm thử gần nhất

| Kiểm tra ngày 15/10/2026 | Kết quả |
|---|---|
| `docker exec hdfs-project-smoke python -m pytest -q tests --ignore=tests/test_dashboard.py --ignore=tests/test_mongo_gold.py` | **37 passed**, 1 cảnh báo Arrow fallback. |
| `.venv-dashboard` chạy `tests/test_dashboard.py tests/test_mongo_gold.py` | **14 passed**. |
| HDFS→ETL run fresh 666 và [audit hash](docs/data/m2_hdfs_etl_audit.json) | **Đạt**; 661 Silver/provenance 1:1. |
| MongoDB publish/readback, AppTest backend Mongo, HTTP health cổng 8502 | **Đạt**; 5 bảng đúng row count, overview/`NO_GO` không có exception, HTTP 200. |

Kiểm thử không thay thế đánh giá taxonomy thủ công hay nghiệm thu chính thức. Xem [báo cáo cuối](docs/final/FINAL_REPORT_2026-10-15.md) và [sơ đồ tiến độ](docs/planning/PROJECT_PROGRESS_DIAGRAM_2026-10-15.md) để biết các nhánh đang chờ.
