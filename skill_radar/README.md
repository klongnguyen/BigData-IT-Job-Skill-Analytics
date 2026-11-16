# Skill Radar

Hệ thống phân tích thị trường tuyển dụng và dự báo nhu cầu kỹ năng CNTT dựa trên dữ liệu lớn.
Dự án làm lại từ đầu, tách khỏi `dashboard/` và `src/` cũ. Kế hoạch cải thiện: [KE_HOACH_CAI_TIEN.md](../KE_HOACH_CAI_TIEN.md). Hướng dẫn sử dụng từng màn hình và nguồn gốc dữ liệu của biểu đồ: [HUONG_DAN_SU_DUNG.md](../HUONG_DAN_SU_DUNG.md).

**Câu hỏi nghiên cứu:** hoạt động cộng đồng (Stack Overflow, npm, GitHub) có đi trước nhu cầu tuyển dụng kỹ năng không, và có giúp dự báo không?

## Dữ liệu
| Tầng | Nguồn | Trạng thái |
| --- | --- | --- |
| Nhu cầu (mục tiêu) | Hacker News "Ask HN: Who is hiring?", 185 chuỗi tháng từ 04/2011, 93.354 tin | xong |
| Tín hiệu | npm (11 kỹ năng, từ 2015) | xong |
| Tín hiệu | Stack Overflow theo tag, theo quý | chạy dở: 300 lượt/ngày nếu không có khóa API (`SE_API_KEY`) |
| Tín hiệu | GitHub Archive (Spark, lấy mẫu giờ) | chưa làm |

## Lưu trữ: SQLite theo mô hình Bronze / Silver / Gold
| Cơ sở dữ liệu | Git | Nội dung chính |
| --- | --- | --- |
| `data/warehouse.db` (~300 MB) | bỏ qua | `bronze_thread`, `bronze_comment` (HTML gốc); `postings`, `posting_skills`, `posting_features`, `demand_month`, `demand_quarter`, `etl_report`; `signal_npm_month`, `signal_se_quarter` |
| `data/gold.db` (~17 MB) | theo dõi | Dự báo (`radar_series`, `radar_paths`, `radar_history`, `backtest_cell`); kết quả mô hình (`run_info`, `model_score`, `model_horizon_error`, `label_score`, `selection_score`, `interval_quantile`, `leadlag*`); phân tích cho dashboard (`posting`, `posting_skill`, `market_quarter`, `location_year`, `skill_year`, `skill_pair_year`, `skill_pair_window`, `skill_attr_year`, `skill_salary`, `employer`, `skill_cluster`, `event`, `signal_quarter`, `gold_fact`) |

Dashboard chỉ đọc `gold.db` (chế độ chỉ đọc). Các file `data/raw/**` chỉ là bộ nhớ đệm tải từ API.

## Chạy
```powershell
pip install -r requirements.txt
python -m skill_radar.ingest.hn            # tải 185 chuỗi (có cache)
python -m skill_radar.ingest.npm
python -m skill_radar.ingest.stackexchange # đặt SE_API_KEY để chạy đủ trong 1 ngày
python -m skill_radar.process.hn_postings  # Bronze -> Silver (warehouse.db), ~6 phút
python -m skill_radar.process.signals      # nạp npm/Stack Overflow vào warehouse.db
python -m skill_radar.pipeline             # backtest + dự báo + bảng phân tích -> gold.db, ~1,5 phút
python -m streamlit run skill_radar/app.py --server.port 8502
python -m pytest -q tests
```
Đổi luật trích xuất đặc trưng trong `process/features.py`: chạy `python -m skill_radar.process.hn_postings --features-only` (~1,5 phút) rồi chạy lại `pipeline`.

## Dashboard (6 trang)
Tổng quan · Xu hướng · Hồ sơ kỹ năng · Hệ sinh thái · Skill Navigator · Dự báo & độ tin cậy. Liên kết trực tiếp: `?page=Xu hướng`. Giao diện nền trắng; biểu đồ tương tác (rê chuột, phóng to, bấm để chọn kỹ năng và xem chi tiết).

## Quy trình đánh giá (đặt trước)
Chuỗi quý 2015Q3–2026Q3 (45 quý). Chọn tham số và mô hình chỉ bằng dữ liệu tới 2022Q4. Holdout 2023Q1–2026Q3 chấm một lần.
Kỹ năng đủ điều kiện: tỷ lệ trung bình ≥ 1% trong cửa sổ chọn. Nhãn Rising/Stable/Fading: ngưỡng ±1,0 điểm phần trăm sau 4 quý.

Các chỉ số mô tả (remote, lương, cấp bậc, địa điểm, cụm công nghệ, Skill Navigator) **không** thuộc quy trình kiểm chứng trên: chúng là thống kê mô tả từ quy tắc regex, chưa đối chiếu với nhãn thủ công.
