# GIAI ĐOẠN 1 – DATA FEASIBILITY & PROJECT DEFINITION

## Dự án: Big Data IT Job Skill Analytics

### Mục tiêu giai đoạn

Giai đoạn đầu tiên của dự án tập trung vào việc **khảo sát, xác nhận tính khả thi của dữ liệu và chốt thiết kế dữ liệu ban đầu** trước khi triển khai HDFS, Apache Spark, Machine Learning hay Dashboard.

Mục tiêu chính:

- Chốt phạm vi đề tài.
- Chốt câu hỏi nghiên cứu.
- Chốt nhóm nghề CNTT và nhóm kỹ năng.
- Tìm và đánh giá Historical Dataset.
- Tìm và kiểm tra Fresh Data năm 2026.
- Thu thập dữ liệu mẫu từ các nguồn.
- Thực hiện Data Profiling.
- Thiết kế Unified Schema.
- Thiết kế Data Dictionary.
- Kiểm tra khả năng chuẩn hóa Job Title và Skill.
- Xác nhận dữ liệu có đủ điều kiện để phân tích xu hướng theo thời gian.
- Thực hiện đánh giá GO / NO-GO.

---

# 1. Bảng kế hoạch chi tiết

| ID | Công việc | Nội dung thực hiện | Kết quả đầu ra | Tiêu chí hoàn thành |
|---|---|---|---|---|
| P1-01 | Chốt mục tiêu đề tài | Xác định rõ hệ thống phân tích thị trường tuyển dụng CNTT và dự báo xu hướng kỹ năng | `project_scope.md` | Có mục tiêu, đối tượng sử dụng, phạm vi và giới hạn |
| P1-02 | Chốt Research Questions | Chuẩn hóa các câu hỏi nghiên cứu RQ1–RQ5 | `research_questions.md` | Mỗi RQ có thể trả lời bằng dữ liệu |
| P1-03 | Chốt nhóm nghề CNTT | Giữ khoảng 6–8 nhóm nghề chính | Danh sách occupation chính thức | Không mở rộng quá nhiều job title |
| P1-04 | Chốt nhóm kỹ năng | Xác định các nhóm Programming, Database, Big Data, Cloud, DevOps, BI, AI/ML | `skill_scope.md` | Có taxonomy ban đầu |
| P1-05 | Khảo sát Historical Dataset | Tìm dataset tuyển dụng 2024–2025 hoặc dài hơn | Danh sách candidate dataset | Có ít nhất 2–3 nguồn để so sánh |
| P1-06 | Đánh giá Historical Dataset | Kiểm tra số record, schema, timestamp, description, location, salary, license | `historical_data_evaluation.md` | Chọn được 1 dataset chính |
| P1-07 | Khảo sát Fresh Data 2026 | Tìm API, open dataset hoặc nguồn crawl hợp lệ | Danh sách nguồn fresh data | Có ít nhất 1 nguồn khả thi |
| P1-08 | Kiểm tra API | Gọi thử API, kiểm tra giới hạn request, schema và số lượng record | Sample JSON / CSV | Thu được dữ liệu thật năm 2026 |
| P1-09 | Kiểm tra crawler dự phòng | Khảo sát crawler trong trường hợp API không đủ dữ liệu | `crawler_feasibility.md` | Có phương án dự phòng |
| P1-10 | Thu sample data | Lấy khoảng 100–500 record Historical và 100–500 record Fresh | `data/sample/` | Có dữ liệu thật để thử nghiệm |
| P1-11 | Data Profiling | Kiểm tra missing, duplicate, kiểu dữ liệu, timestamp và field coverage | `data_profile.md` | Biết rõ chất lượng từng nguồn |
| P1-12 | So sánh schema | Mapping field giữa Historical Data và Fresh Data | `schema_mapping.md` | Mọi field quan trọng được ánh xạ |
| P1-13 | Thiết kế Unified Schema | Chuẩn hóa schema chung cho toàn hệ thống | `unified_schema.md` | Schema đủ phục vụ ETL, Analytics và ML |
| P1-14 | Thiết kế Data Dictionary | Mô tả từng field, kiểu dữ liệu, nullable và nguồn gốc | `data_dictionary.md` | 100% field trong Unified Schema được mô tả |
| P1-15 | Xác định khóa / Duplicate Strategy | Thiết kế `job_id`, `job_hash`, rule nhận dạng duplicate | `deduplication_rules.md` | Có rule rõ ràng trước ETL |
| P1-16 | Chốt Timestamp Strategy | Phân biệt `posted_at` và `collected_at` | Một phần trong Unified Schema | Không nhầm thời điểm đăng và thời điểm thu thập |
| P1-17 | Kiểm tra khả năng Normalize Job Title | Thử mapping khoảng 50–100 job title | `job_title_mapping_v0.csv/json` | Phần lớn job sample map được vào occupation |
| P1-18 | Kiểm tra khả năng Extract Skill | Thử Skill Dictionary trên khoảng 50–100 description | `skills_v0.json` | Extract được các skill quan trọng |
| P1-19 | Kiểm tra dữ liệu thời gian | Xem số lượng job theo tháng / quý | Chart / bảng thống kê | Có đủ time point để phân tích trend |
| P1-20 | GO / NO-GO Review | Tổng hợp các tiêu chí feasibility | `go_no_go_report.md` | Ra quyết định GO hoặc điều chỉnh phạm vi |

---

# 2. Phạm vi nghề CNTT ban đầu

Đề xuất giữ khoảng 6–8 nhóm nghề tiêu biểu:

- Data Analyst
- Data Scientist
- Data Engineer
- Software Engineer
- Backend Developer
- Frontend Developer
- DevOps Engineer
- Machine Learning Engineer

Không nên mở rộng quá nhiều occupation ở giai đoạn đầu vì sẽ làm tăng độ phức tạp của bước chuẩn hóa Job Title và Skill.

---

# 3. Nhóm kỹ năng ban đầu

## Programming

- Python
- Java
- JavaScript
- C++
- C#

## Database

- SQL
- MySQL
- PostgreSQL
- MongoDB

## Data / Big Data

- Pandas
- NumPy
- Spark
- Hadoop
- Kafka
- Hive

## BI

- Power BI
- Tableau
- Excel

## Cloud

- AWS
- Azure
- GCP

## DevOps

- Docker
- Kubernetes
- Jenkins
- Terraform

## AI / ML

- TensorFlow
- PyTorch
- Scikit-learn
- Generative AI
- LLM
- RAG

---

# 4. Unified Schema ban đầu

Schema chuẩn dự kiến:

```text
job_id
title
normalized_title
company
location
country
description
experience_level
salary_min
salary_max
posted_at
collected_at
source
skills
```

Hai trường đặc biệt quan trọng:

```text
posted_at
collected_at
```

Trong đó:

- `posted_at`: thời điểm tin tuyển dụng được đăng.
- `collected_at`: thời điểm hệ thống thu thập dữ liệu.

Hai trường này là nền tảng để:

- Phân tích dữ liệu theo thời gian.
- Xây dựng trend.
- Time-based split.
- Recency weighting.
- Phân tích concept drift.

---

# 5. Lịch triển khai đề xuất

| Ngày | Công việc chính | Deliverable cuối ngày |
|---|---|---|
| Ngày 1 | Chốt scope, Research Questions, occupations và skill groups | `project_scope.md`, `research_questions.md` |
| Ngày 2 | Tìm và đánh giá Historical Dataset | `historical_data_evaluation.md` |
| Ngày 3 | Tìm Fresh Data / API 2026 và test request | `fresh_data_evaluation.md` + sample |
| Ngày 4 | Thu sample và thực hiện Data Profiling | `data_profile.md` |
| Ngày 5 | Mapping schema và thiết kế Unified Schema | `schema_mapping.md`, `unified_schema.md` |
| Ngày 6 | Thử Normalize Job Title và Skill Extraction | mapping V0 + `skills_v0.json` |
| Ngày 7 | Kiểm tra dữ liệu thời gian và GO / NO-GO | `go_no_go_report.md` |

---

# 6. Cấu trúc repo sau Giai đoạn 1

```text
BigData-IT-Job-Skill-Analytics/
│
├── data/
│   ├── sample/
│   │   ├── historical/
│   │   └── fresh/
│   │
│   ├── raw/
│   └── external/
│
├── docs/
│   ├── planning/
│   │   ├── project_scope.md
│   │   ├── research_questions.md
│   │   └── go_no_go_report.md
│   │
│   ├── data/
│   │   ├── data_sources.md
│   │   ├── historical_data_evaluation.md
│   │   ├── fresh_data_evaluation.md
│   │   ├── data_profile.md
│   │   ├── schema_mapping.md
│   │   ├── unified_schema.md
│   │   ├── data_dictionary.md
│   │   └── deduplication_rules.md
│   │
│   └── skills/
│       └── skill_scope.md
│
├── config/
│   ├── skills_v0.json
│   └── job_title_mapping_v0.json
│
├── notebooks/
│   └── 01_data_exploration.ipynb
│
├── src/
│   └── ingestion/
│
├── PLAN.md
└── README.md
```

---

# 7. Milestone

## M1 – Data Feasibility Confirmed

Giai đoạn 1 chỉ được xem là hoàn thành khi hệ thống xác nhận được tính khả thi của dữ liệu.

### Checklist

- [ ] Có Historical Dataset đủ lớn.
- [ ] Historical Dataset có `posted_at` hoặc timestamp tương đương.
- [ ] Có ít nhất một nguồn Fresh Data năm 2026.
- [ ] Thu được dữ liệu Fresh Data thực tế.
- [ ] Có Job Description đủ để trích xuất skill.
- [ ] Có thể chuẩn hóa Job Title.
- [ ] Có thể chuẩn hóa Skill.
- [ ] Có đủ dữ liệu theo tháng hoặc quý để phân tích trend.
- [ ] Hoàn thiện Unified Schema.
- [ ] Hoàn thiện Data Dictionary.
- [ ] Hoàn thiện Data Profiling.
- [ ] Có phương án xử lý duplicate.
- [ ] Hoàn thiện GO / NO-GO Report.

---

# 8. Tiêu chí GO / NO-GO

Trước khi chuyển sang xây dựng HDFS và Spark Pipeline cần kiểm tra:

```text
1. Có Historical Dataset đủ lớn?
             ↓
            YES

2. Dataset có posted_at / timestamp?
             ↓
            YES

3. Có nguồn Fresh Data 2026?
             ↓
            YES

4. Có thể normalize Job Title + Skill?
             ↓
            YES
```

Nếu cả bốn tiêu chí đều đạt:

```text
GO
```

Có thể chuyển sang:

```text
Data Ingestion
      ↓
HDFS Bronze Layer
      ↓
Spark ETL
      ↓
Silver Dataset
```

Nếu dữ liệu không có timestamp phù hợp hoặc Fresh Data không khả thi, cần điều chỉnh phạm vi đề tài trước khi tiếp tục.

---

# 9. Thứ tự ưu tiên thực hiện

Không nên bắt đầu bằng việc cài Hadoop hoặc xây ML Model.

Thứ tự ưu tiên:

```text
Historical Dataset
        ↓
Fresh Data 2026
        ↓
Sample Data
        ↓
Data Profiling
        ↓
Schema Mapping
        ↓
Unified Schema
        ↓
Job Title Normalization
        ↓
Skill Extraction thử nghiệm
        ↓
GO / NO-GO
        ↓
HDFS + Spark
```

---

# 10. Công việc nên bắt đầu ngay

Các task P1-01 đến P1-04 về cơ bản đã được xác định trong kế hoạch tổng thể.

Vì vậy, task thực thi đầu tiên nên là:

## P1-05 – Khảo sát Historical Dataset

Mục tiêu:

- Tìm ít nhất 2–3 dataset tuyển dụng tiềm năng.
- Kiểm tra:
  - Số lượng record.
  - Khoảng thời gian dữ liệu.
  - Có `posted_at` hay không.
  - Có `description` hay không.
  - Có `title` hay không.
  - Có `location` hay không.
  - Có salary hay không.
  - Có skill hay không.
  - License và điều kiện sử dụng.
- Chọn một dataset chính để làm Historical Data.

Sau khi hoàn thành P1-05 và P1-06, chuyển sang khảo sát Fresh Data 2026.

---

# 11. Kết quả cuối cùng của Giai đoạn 1

Sau khi hoàn thành Phase 1, dự án cần có:

```text
Project Scope
      +
Research Questions
      +
Historical Dataset
      +
Fresh Data Source
      +
Sample Data
      +
Data Profiling
      +
Unified Schema
      +
Data Dictionary
      +
Job Title Mapping V0
      +
Skill Dictionary V0
      ↓
GO / NO-GO
```

Nếu kết quả là **GO**, dự án chính thức chuyển sang:

# Giai đoạn 2 – Data Ingestion & Big Data Storage

```text
Data Sources
      ↓
Collector / API
      ↓
HDFS
      ↓
Bronze Layer
      ↓
Apache Spark
      ↓
Silver Layer
```
