# Báo cáo Đánh giá Khả thi & Quyết định GO / NO-GO (Milestone 1)

## Dự án: Big Data IT Job Skill Analytics
- **Giai đoạn**: Giai đoạn 1 – Data Feasibility & Project Definition
- **Ngày đánh giá**: 19/09/2026
- **Trạng thái quyết định**: **GO (TIẾP TỤC TRIỂN KHAI GIAI ĐOẠN 2)**

---

## 1. Tóm tắt kết quả kiểm tra 4 tiêu chí cốt lõi (Core Criteria)

```text
1. Có Historical Dataset đủ lớn?
             ↓
        ĐẠT (YES) -> Kaggle / Luke Barousse Tech Jobs (2022–2025)
             ↓
2. Dataset có posted_at / timestamp chuẩn?
             ↓
        ĐẠT (YES) -> 100% bản ghi có ISO timestamp hoặc Unix epoch
             ↓
3. Có nguồn Fresh Data năm 2026 khả thi?
             ↓
        ĐẠT (YES) -> Arbeitnow & Remotive API (267 bản ghi thực tế 09/2026)
             ↓
4. Có thể Normalize Job Title & Trích xuất Skill?
             ↓
        ĐẠT (YES) -> Match 8 nhóm nghề; Trích xuất TB 5.57 kỹ năng/JD
             ↓
     ======================
         QUYẾT ĐỊNH: GO
     ======================
```

---

## 2. Chi tiết đánh giá theo Milestone 1 Checklist

| STT | Tiêu chí kiểm định | Kết quả thực nghiệm | Đánh giá |
|---|---|---|---|
| 1 | **Historical Dataset đủ lớn** | Đã khảo sát 3 tập dữ liệu (Luke Barousse, LinkedIn, Dice). Chọn tập Luke Barousse làm baseline với quy mô >780,000 bản ghi toàn cầu. | **ĐẠT** |
| 2 | **Có trường timestamp `posted_at`** | 100% bản ghi có mốc thời gian rõ ràng, trải đều qua 50 tháng (từ 2022 đến 2026). | **ĐẠT** |
| 3 | **Có nguồn Fresh Data 2026** | Thu thập thành công từ Arbeitnow API và Remotive API mà không cần API key, cập nhật đến tháng 09/2026. | **ĐẠT** |
| 4 | **Độ dài Job Description** | Độ dài trung bình >2,000 ký tự, đầy đủ trách nhiệm và yêu cầu kỹ thuật. | **ĐẠT** |
| 5 | **Chuẩn hóa Job Title (P1-17)** | Bộ từ điển `configs/job_title_mapping_v0.json` phân loại chính xác 8 nhóm nghề cốt lõi, tách biệt rõ ràng các tin phi công nghệ vào nhóm "Other IT". | **ĐẠT** |
| 6 | **Trích xuất kỹ năng (P1-18)** | Bộ từ điển `configs/skills_v0.json` (35 kỹ năng, 8 nhóm) đạt tỷ lệ phủ 72.66% trên tập hỗn hợp (và >90% trên tập chuyên biệt IT), trung bình 5.57 skills/JD. | **ĐẠT** |
| 7 | **Đủ dữ liệu theo thời gian (P1-19)** | Chuỗi thời gian liên tục qua 5 năm (2022: 62, 2023: 87, 2024: 69, 2025: 82, 2026: 267 jobs). | **ĐẠT** |
| 8 | **Unified Schema & Dictionary** | Hoàn thiện 14 trường dữ liệu (`job_id`, `title`, `normalized_title`, `posted_at`, `collected_at`, `skills`...) tại `docs/data/unified_schema.md` và `docs/data/data_dictionary.md`. | **ĐẠT** |
| 9 | **Deduplication Strategy** | Hoàn thiện thuật toán sinh `job_hash` (SHA-256) và quy tắc khử trùng lặp đa nền tảng / tin đăng lại tại `docs/data/deduplication_rules.md`. | **ĐẠT** |
| 10 | **Chiến lược dự phòng** | Hoàn thiện phương án crawler dự phòng và mở rộng thị trường Việt Nam (ITviec, TopCV, VietnamWorks) tại `docs/data/crawler_feasibility.md`. | **ĐẠT** |

---

## 3. Tổng hợp Deliverables đã hoàn thành trong Giai đoạn 1

Tất cả các tài liệu và mã nguồn quy định trong Phase 01 đã được hoàn thành đầy đủ:

1. **Planning & Scope**:
   - `docs/planning/project_scope.md`: Mục tiêu hệ thống, đối tượng sử dụng, phạm vi và giới hạn.
   - `docs/planning/research_questions.md`: Quy chuẩn hóa câu hỏi nghiên cứu RQ1–RQ5 cùng công thức toán học đo lường.
   - `docs/planning/go_no_go_report.md`: Báo cáo đánh giá khả thi này.
2. **Data Evaluation & Schema**:
   - `docs/data/historical_data_evaluation.md`: Đánh giá và chọn Historical Dataset.
   - `docs/data/fresh_data_evaluation.md`: Khảo sát và kiểm thử thực tế API 2026.
   - `docs/data/crawler_feasibility.md`: Khảo sát crawler dự phòng và dữ liệu thị trường Việt Nam.
   - `docs/data/data_profile.md`: Kết quả Data Profiling trên 567 bản ghi mẫu.
   - `docs/data/schema_mapping.md`: Bảng ánh xạ trường từ các nguồn vào Unified Schema.
   - `docs/data/unified_schema.md`: Đặc tả 14 trường dữ liệu và PySpark StructType.
   - `docs/data/data_dictionary.md`: Từ điển dữ liệu chi tiết cho 100% trường.
   - `docs/data/deduplication_rules.md`: Quy tắc khử trùng lặp và tính `job_hash`.
3. **Skills & Taxonomy**:
   - `docs/skills/skill_scope.md`: Hệ thống phân loại 8 nhóm kỹ năng.
   - `configs/skills_v0.json`: Từ điển kỹ năng và regex patterns.
   - `configs/job_title_mapping_v0.json`: Bộ ánh xạ chức danh sang 8 nhóm nghề.
4. **Data Samples & Scripts**:
   - `data/sample/historical/historical_sample_300.json` & `.csv`: 300 bản ghi lịch sử 2022–2025.
   - `data/sample/fresh/fresh_sample.json` & `.csv`: 267 bản ghi năm 2026 từ Arbeitnow & Remotive.
   - `src/collection/collect_samples.py`: Script thu thập mẫu tự động.
   - `src/collection/profile_samples.py`: Script profiling dữ liệu tự động.
   - `tests/test_phase01_feasibility.py`: Script kiểm định chuẩn hóa title và trích xuất skill.
   - `tests/test_results_phase01.json`: Kết quả kiểm định thực nghiệm.

---

## 4. Kế hoạch chuyển tiếp sang Giai đoạn 2 (Next Steps)

Với kết quả **GO**, dự án sẵn sàng chuyển sang:

### **GIAI ĐOẠN 2 – DATA INGESTION & BIG DATA STORAGE**
- **Mục tiêu**:
  1. Thiết lập hạ tầng lưu trữ phân tán Bronze Layer (HDFS / Data Lake).
  2. Xây dựng Data Collector tự động thu nạp Historical Data và Fresh Data định kỳ vào Bronze Layer.
  3. Xây dựng Apache Spark ETL Pipeline:
     - Làm sạch dữ liệu và loại bỏ HTML tags.
     - Khử trùng lặp theo `job_hash`.
     - Chuẩn hóa Job Title về 8 nhóm nghề qua `configs/job_title_mapping_v0.json`.
     - Trích xuất kỹ năng qua `configs/skills_v0.json`.
     - Xuất dữ liệu đã chuẩn hóa sang **Silver Layer** (định dạng Parquet phân vùng theo `year/month`).
