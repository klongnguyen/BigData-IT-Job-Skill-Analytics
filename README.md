# BigData Job Analy — Skill Radar

Dự án làm lại từ đầu; toàn bộ mã nguồn và mô tả nằm trong [skill_radar/](skill_radar/README.md).


Hệ thống phân tích thị trường tuyển dụng và dự báo nhu cầu kỹ năng CNTT dựa trên dữ liệu lớn.
Dự án làm lại từ đầu, tách khỏi `dashboard/` và `src/` cũ.

**Câu hỏi nghiên cứu:** hoạt động cộng đồng (Stack Overflow, npm, GitHub) có đi trước nhu cầu tuyển dụng kỹ năng không, và có giúp dự báo không?

## Dữ liệu
| Tầng | Nguồn | Trạng thái |
| --- | --- | --- |
| Nhu cầu (mục tiêu) | Hacker News "Ask HN: Who is hiring?", 185 chuỗi tháng từ 04/2011, 93.354 tin | xong |
| Tín hiệu | npm (11 kỹ năng, từ 2015) | xong |
| Tín hiệu | Stack Overflow theo tag, theo quý | chạy dở: 300 lượt/ngày nếu không có khóa API (`SE_API_KEY`) |
| Tín hiệu | GitHub Archive (Spark, lấy mẫu giờ) | chưa làm |

## Chạy
```powershell
python -m skill_radar.ingest.hn            # tải 185 chuỗi (có cache)
python -m skill_radar.ingest.npm
python -m skill_radar.ingest.stackexchange # đặt SE_API_KEY để chạy đủ trong 1 ngày
python -m skill_radar.process.hn_postings  # Bronze -> Silver -> Gold nhu cầu
python -m skill_radar.pipeline             # backtest + độ trễ + dự báo + artifact
python -m streamlit run skill_radar/app.py --server.port 8502
python -m pytest -q tests/test_skill_radar.py
```

## Quy trình đánh giá (đặt trước)
Chuỗi quý 2015Q3–2026Q3 (45 quý). Chọn tham số và mô hình chỉ bằng dữ liệu tới 2022Q4. Holdout 2023Q1–2026Q3 chấm một lần.
Kỹ năng đủ điều kiện: tỷ lệ trung bình ≥ 1% trong cửa sổ chọn. Nhãn Rising/Stable/Fading: ngưỡng ±1,0 điểm phần trăm sau 4 quý.
