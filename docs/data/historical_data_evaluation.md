# Historical Data Evaluation — repository audit

**Cập nhật:** 04/10/2026
**Artifact có checksum và thống kê:** [`phase01_data_audit.json`](phase01_data_audit.json)

## Nguồn hiện có trong repository

| Thuộc tính | Giá trị đã kiểm kê |
|---|---|
| File | `data/raw/data_jobs.csv` |
| Số dòng | 785.741 |
| Phạm vi đăng tin | 01–12/2023 |
| Trường thời gian | `job_posted_date` |
| Chức danh | `job_title`, `job_title_short` |
| Kỹ năng | `job_skills`, `job_type_skills` (tags có sẵn trong archive) |
| Company | `company_name` |
| Job description | Không có cột `job_description` |
| Native stable job ID | Không có trường ID nguồn trong header hiện tại |
| License/điều khoản | Chưa xác minh bằng bằng chứng nguồn được lưu trong repository |

Checksum SHA-256, count theo tháng, columns, null counts và phân bố nghề × tháng nằm trong manifest. Sample `data/sample/historical/historical_sample_300.json` được lấy phân tầng 25 dòng mỗi tháng từ raw, với seed cố định; nó giữ nguyên tên trường nguồn. Sample không chứa JD và không thêm năm/dữ liệu 2024–2025.

## Giới hạn và quyết định

- Archive hữu ích cho analytics mô tả có giới hạn trong năm 2023, subject to nguồn và điều khoản sử dụng được xác minh.
- `job_skills` là tags/nhãn có sẵn của nguồn. Không gọi chúng là nhãn chuyên gia đã được xác nhận; không dùng chúng như ground truth độc lập để đánh giá extraction trên cùng JD.
- Vì thiếu JD, archive này không đánh giá được skill extraction từ văn bản và không hỗ trợ các tuyên bố extraction accuracy.
- Một năm dữ liệu không đủ cho các dự báo đa năm hoặc xác nhận seasonality. Không lấp khoảng trống lịch sử bằng sample synthetic.
- Các candidate datasets/ước lượng license trước đây chưa có provenance được ghi lại ở đây; đánh giá cần URL tải, version/date, checksum và điều khoản sử dụng trước khi phát hành.

**Quyết định:** GO cho prototype ingestion và analytics mô tả 2023 có giới hạn; NO-GO cho predictive claims đến khi có chuỗi lịch sử và backtest đủ căn cứ. Crawler/nguồn lịch sử bổ sung tiếp tục ở trạng thái planned cho tới khi được kiểm tra thật.
