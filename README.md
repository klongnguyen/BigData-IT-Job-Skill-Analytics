# BigData Job Analy · JobScope

**Trạng thái 15/10/2026:** Bronze → Silver → Gold mô tả 2026 và dashboard JobScope đã chạy, audit đạt. Mức sẵn sàng báo cáo khoảng **90% theo hạng mục bàn giao**; đây là ước lượng tiến độ, không phải thước đo chất lượng mô hình. Dự báo vẫn **`NO_GO`** theo [Final Plan](FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md).

## Kết quả đã kiểm chứng

| Lớp | Kết quả |
| --- | --- |
| Bronze 2026 | 23 run được pin; 21.435 raw, 19.706 ID duy nhất, 1.729 trùng; không sửa raw. [Audit](docs/data/2026_ingestion_audit.json). |
| Silver 2026 | Run `10d0710787d2402186356858d3331e50`; 8.370 analytical và 8.370 provenance; 548 ngoài phạm vi IT, 10.788 chưa đủ căn cứ, 0 quarantine. [Audit](docs/data/2026_silver_run_audit.json). |
| Gold 2026 | Run `20261015T144634600577Z-8d531796a5f6`; 5 bảng: 13 market, 66 occupation, 66 skill evidence, 401 skill stats, 401 skill trends. Cả ba bảng đếm tin đều tổng 8.370. [Audit](docs/data/2026_gold_run_audit.json). |
| Dashboard | Catalog chỉ nhận Gold 2023 và Gold 2026 đã audit. Bộ lọc Dataset → Market → Source → Month → Occupation; phân tích 2026 đọc Gold 2026. |
| Gold cũ | Run `20261004T110131548191Z-e38fa7303cf4` vẫn nguyên vẹn; manifest SHA-256 `2b37892022882e834b5437555c5c567aa2ab31103dc1d581b9b2f18cd9e7c74d`. |

Gold 2026 tách `GLOBAL` (Arbeitnow 1.621, Remotive 10) khỏi `US_FEDERAL` (USAJOBS PositionSeries 2210: 6.739). Tháng quan sát của Arbeitnow chỉ 10/2026; Remotive là 8 tin tháng 9 và 2 tin tháng 10; USAJOBS có quan sát từ tháng 1 đến tháng 10. Không điền 0 cho tháng thiếu. USAJOBS chưa có chứng cứ kỹ năng chuẩn hóa, nên dashboard không dựng tỷ lệ kỹ năng cho nguồn này.

`Other IT` chỉ được đưa vào Silver khi policy xác lập `in_scope`. 10.788 dòng chưa xác định **không được gọi là ngoài IT** và không nằm trong mẫu số Gold. [Mẫu review 175 dòng](docs/data/2026_it_scope_sample.csv) là nhãn hỗ trợ bởi AI, không phải ground truth hay precision/recall/F1. Snapshot API và USAJOBS liên bang có khung lấy mẫu khác archive 2023; không so sánh trực tiếp số lượng như cùng một thị trường.

## Chạy dashboard local

```powershell
.\.venv-dashboard\Scripts\python.exe -m streamlit run dashboard/app.py --server.port 8501
```

Mở [http://127.0.0.1:8501](http://127.0.0.1:8501). Mặc định đọc Parquet. Có thể dùng MongoDB cho **Gold cũ** qua `JOB_GOLD_BACKEND=mongo`; Gold 2026 luôn đọc Parquet đã xác minh. Bản clone Git cần khôi phục các run Parquet local theo đúng manifest và SHA trong audit; raw/Parquet lớn và MongoDB local không nằm trong repository. Xem [runbook](docs/planning/dashboard_runbook.md).

## Bằng chứng và báo cáo

- [Báo cáo cuối](docs/final/FINAL_REPORT_2026-10-15.md), [mức sẵn sàng báo cáo](docs/final/REPORT_READY_STATUS_2026-10-15.md), [sơ đồ tiến độ](docs/planning/PROJECT_PROGRESS_DIAGRAM_2026-10-15.md).
- [Kịch bản demo](docs/final/DEMO_SCRIPT.md) và [đề cương 10 slide](docs/final/PRESENTATION_OUTLINE_2026-10-15.md).
- [Gold audit 2026](docs/reviews/2026_GOLD_RUN_AUDIT_2026-10-15.md), [Silver audit 2026](docs/reviews/2026_SILVER_RUN_AUDIT_2026-10-15.md), [scope review](docs/reviews/2026_IT_SCOPE_AI_REVIEW_2026-10-15.md).

## Phần còn lại trước nghiệm thu 100%

Kiểm tra demo trên máy trình bày và khôi phục artifact nếu chuyển máy; cập nhật bản slide `.pptx` cũ theo đề cương 2026; xin nhóm/giảng viên chấp thuận phạm vi mẫu, đánh giá taxonomy độc lập và hồ sơ `NO_GO`; hoàn tất biên bản nghiệm thu. Chỉ xét dự báo sau khi có chuỗi dữ liệu đủ dài, có thể so sánh và đánh giá ngoài mẫu.
