# GO / NO-GO cập nhật — Phase 01

**Đánh giá lại:** 04/10/2026
**Cơ sở:** kiểm kê `data/raw/data_jobs.csv`, sample historical lấy từ archive, sample fresh đã lưu và mã hiện có. Các con số freshness chỉ mô tả snapshot; không phải xác nhận API vẫn hoạt động hôm nay.

## Quyết định theo phạm vi

| Phạm vi | Quyết định | Cơ sở |
|---|---|---|
| Prototype ingestion, schema và Spark local | **GO** | Archive thật có 785.741 dòng; Bronze/Silver và mã pipeline đã tồn tại trong workspace. Đây là quyết định tiếp tục thử nghiệm kỹ thuật. |
| Descriptive analytics | **CONDITIONAL GO** | Có thể mô tả archive 2023 và snapshot fresh theo đúng nguồn, tháng, nhóm nghề, cỡ mẫu và provenance; không suy rộng sang toàn bộ thị trường. |
| Forecasting và predictive claims | **NO-GO** | Archive hiện tại chỉ có các tin năm 2023 và không có cột JD; fresh snapshot lưu có dữ liệu tháng 08–09/2026. Chưa có chuỗi lịch sử đủ dài/liên tục hoặc backtest đại diện. |
| Đóng quality gate Phase 01 | **REOPENED** | Cần hoàn tất provenance nguồn, audit theo nghề × tháng, contract schema và đánh giá taxonomy trên nhãn độc lập. |

## Bằng chứng trong repository

- `data/raw/data_jobs.csv`: header có `job_title`, `job_posted_date`, `job_skills`, `company_name`; **không có `job_description`**. Kiểm kê trước đây đếm được 785.741 dòng thuộc 12 tháng năm 2023. Chạy `python -m src.collection.audit_phase01_data` để sinh manifest/checksum mới.
- `data/sample/historical/historical_sample_300.json`: sample 300 dòng được lấy phân tầng từ archive 2023; giữ nguyên các trường nguồn và không tạo JD. Sample không chứng minh bao quát các năm khác.
- Dữ liệu trước đây tự sinh 2022–2025 được lưu trong `data/fixtures/synthetic/`; fixture chỉ dùng demo/kiểm thử, không đưa vào feasibility hoặc model metrics.
- `data/sample/fresh/fresh_sample.json`: snapshot đã lưu, không phải truy vấn live hiện tại; thống kê nguồn và tháng phải đọc từ manifest.
- Skill/title coverage là chỉ số bao phủ của rule-based matcher. Chưa có nhãn chuẩn độc lập, nên không diễn giải thành accuracy, precision hay recall.

## Các điều kiện trước khi xét lại

1. Lưu URL/phiên bản/ngày tải/checksum và điều khoản dùng của từng archive; trạng thái license hiện chưa được xác minh nhất quán trong repository.
2. Lập bảng số lượng theo nguồn × nghề × tháng sau quy tắc dedup; phân biệt tháng không có quan sát với nhu cầu bằng 0.
3. Bổ sung chuỗi dữ liệu thật cho nhiều năm và mẫu JD thật nếu cần đánh giá trích xuất văn bản. Không nội suy 2024–2025 hoặc tạo JD từ tags.
4. Đánh giá title/skill trên mẫu gán nhãn độc lập, phân tầng theo nguồn và nghề; báo precision/recall/F1 riêng với coverage.
5. Chỉ xét GO dự báo sau rolling-origin backtest, không rò rỉ thời gian và so sánh baseline trên cùng tập test.

Kết luận Phase 01 hiện tại: **GO cho prototype; conditional GO cho phân tích mô tả giới hạn; NO-GO cho dự báo.** Sự tồn tại của Spark/HDFS design hoặc một lượng lớn dòng trong một năm không thay thế các điều kiện trên.
