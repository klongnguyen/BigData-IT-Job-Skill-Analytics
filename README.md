# BigData IT Job Skill Analytics

Hệ thống Big Data phục vụ **phân tích thị trường tuyển dụng CNTT quốc tế** và **dự báo xu hướng nhu cầu kỹ năng theo từng nhóm nghề**, sử dụng dữ liệu tuyển dụng lịch sử kết hợp với dữ liệu tuyển dụng mới.

> **Trạng thái hiện tại:** Đã hoàn thành **Giai đoạn 1 – Data Feasibility & Project Definition** và **Giai đoạn 2 – Data Ingestion & Big Data Storage**. Silver Layer đã được tạo thành công và hệ thống sẵn sàng chuyển sang giai đoạn phân tích dữ liệu, xây dựng đặc trưng và mô hình dự báo xu hướng.

---

## 1. Tổng quan đề tài

Đề tài tập trung xây dựng pipeline Big Data có khả năng:

- Thu thập dữ liệu tuyển dụng lịch sử và dữ liệu tuyển dụng mới.
- Làm sạch, chuẩn hóa và khử trùng lặp dữ liệu bằng Apache Spark.
- Chuẩn hóa chức danh tuyển dụng về các nhóm nghề CNTT chính.
- Trích xuất và chuẩn hóa kỹ năng từ mô tả công việc.
- Phân tích nhu cầu kỹ năng theo **Occupation + Skill + Time**.
- Phân loại xu hướng kỹ năng thành **Growing**, **Stable** hoặc **Declining**.
- Phân tích Concept Drift giữa dữ liệu lịch sử và dữ liệu mới.
- So sánh mô hình Historical, Recent và Hybrid kết hợp Recency Weighting.
- Xây dựng dashboard trực quan phục vụ phân tích thị trường tuyển dụng CNTT.

### Phạm vi thị trường

- **Global Market:** phạm vi chính thức của MVP (`market = "GLOBAL"`).
- **Vietnam Market:** hiện đang **FROZEN**, được giữ trong kiến trúc để có thể mở rộng sau khi MVP hoàn thiện.

### Nguyên tắc dự báo

Hệ thống **không dự báo xu hướng kỹ năng chung cho toàn ngành CNTT**.

Xu hướng được phân tích và dự báo theo từng nhóm nghề dựa trên bộ ba:

```text
Occupation + Skill + Time
```

Ví dụ, xu hướng `React` của Frontend Developer và xu hướng `Spark` của Data Engineer được xem là hai chuỗi nhu cầu riêng biệt.

---

## 2. Phạm vi nghề nghiệp

Hệ thống hiện chuẩn hóa dữ liệu về **8 nhóm nghề CNTT**:

1. Data Analyst
2. Data Scientist
3. Data Engineer
4. Machine Learning Engineer
5. Software Engineer
6. Backend Developer
7. Frontend Developer
8. DevOps Engineer

Taxonomy kỹ năng hiện gồm **8 nhóm công nghệ**, hơn **35 kỹ năng chính** cùng các từ khóa đồng nghĩa phục vụ Skill Extraction.

---

## 3. Nguồn dữ liệu đã xác thực

### Historical Data

Nguồn dữ liệu lịch sử đã được chọn có quy mô hơn **780.000 tin tuyển dụng**, có trường thời gian `job_posted_date` đạt yêu cầu để thực hiện phân tích chuỗi thời gian.

### Fresh Data

Hai nguồn API đã được kiểm thử thành công để lấy dữ liệu tuyển dụng mới:

- Arbeitnow API
- Remotive API

Kết quả kiểm định Phase 1 trên **567 bản ghi mẫu**:

```text
Trung bình kỹ năng trích xuất: 5.57 skills / job description
Khoảng thời gian dữ liệu kiểm thử: 50 tháng (2022 → 2026)
Kết quả GO / NO-GO: GO
```

Chi tiết xem tại:

- [Tổng kết Phase 01 & 02](docs/planning/phase_01_02_summary.md)
- [Báo cáo GO / NO-GO](docs/planning/go_no_go_report.md)

---

## 4. Unified Schema

Dữ liệu sau chuẩn hóa sử dụng **18 trường thống nhất**:

```text
job_id
title
normalized_title
company
location
city
country
market
work_mode
description
experience_level
salary_min
salary_max
currency
posted_at
collected_at
source
skills
```

Hệ thống đồng thời sử dụng `job_hash` SHA-256 để hỗ trợ phát hiện tin tuyển dụng trùng lặp hoặc repost.

---

## 5. Kiến trúc hệ thống

```text
          Historical Job Data
                  +
            Fresh Job APIs
                  |
                  v
          RAW / INGESTION
                  |
                  v
            Bronze Layer
       Raw JSON + Metadata
                  |
                  v
           Apache Spark
     -----------------------
     Cleaning
     Text Normalization
     Deduplication SHA-256
     Job Title Mapping
     Skill Extraction
     Unified Schema
     -----------------------
                  |
                  v
            Silver Layer
       Parquet + Snappy
      Partition year/month
                  |
                  v
       Feature Engineering
                  |
          +-------+-------+
          |               |
          v               v
      Analytics       Spark MLlib
          |          Trend Prediction
          +-------+-------+
                  |
                  v
             Gold Layer
                  |
                  v
              MongoDB
                  |
                  v
        Streamlit Dashboard
```

---

## 6. Kết quả đã hoàn thành

### Phase 01 – Data Feasibility & Project Definition ✅

Đã hoàn thành:

- Chốt phạm vi Global-first và đóng băng Vietnam Market.
- Xây dựng 6 câu hỏi nghiên cứu RQ1 – RQ6.
- Xác định 8 nhóm nghề CNTT.
- Xây dựng Skill Taxonomy và Job Title Mapping.
- Khảo sát và lựa chọn Historical Dataset.
- Kiểm thử Arbeitnow API và Remotive API.
- Thiết kế Unified Schema 18 trường.
- Thiết kế quy tắc Deduplication bằng SHA-256.
- Kiểm thử khả thi trên dữ liệu mẫu.
- Hoàn thành Milestone 1 với quyết định **GO**.

### Phase 02 – Data Ingestion & Big Data Storage ✅

Môi trường xử lý dữ liệu đã được thiết lập với:

```text
Python 3.11
PySpark 4.2.0
OpenJDK 17 LTS
Hadoop Winutils
```

Pipeline ingestion hiện đã xử lý:

```text
Historical Data : 50,000 records
Fresh Data 2026 :    267 records
--------------------------------
Bronze Input    : 50,267 records
Duplicates      :    180 records
--------------------------------
Silver Output   : 50,087 records
```

Silver Layer hiện được lưu dưới dạng:

```text
Parquet
+ Snappy Compression
+ Partition theo year / month
```

Dữ liệu đã được chuẩn hóa về đúng Unified Schema và sẵn sàng cho bước Analytics / Machine Learning.

---

## 7. Cấu trúc codebase hiện tại

```text
BigData-IT-Job-Skill-Analytics/
│
├── configs/
│   ├── job_title_mapping_v0.json
│   ├── skills_v0.json
│   └── markets.json
│
├── data/
│   ├── raw/
│   │   └── data_jobs.csv
│   │
│   ├── bronze/
│   │   └── global/
│   │       ├── historical/
│   │       └── fresh/
│   │
│   ├── silver/
│   │   └── global/
│   │
│   └── sample/
│
├── docs/
│   ├── planning/
│   ├── data/
│   └── skills/
│
├── src/
│   ├── ingestion/
│   │   ├── historical_ingestion.py
│   │   └── fresh_ingestion.py
│   │
│   └── processing/
│       └── spark_etl.py
│
├── tests/
│   └── test_phase01_feasibility.py
│
├── FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md
└── README.md
```

> Các dataset dung lượng lớn như file historical gốc và output Bronze/Silver có thể được giữ ngoài Git hoặc loại khỏi version control. Repository chủ yếu lưu source code, cấu hình, tài liệu và các file mẫu cần thiết để tái tạo pipeline.

---

## 8. Công nghệ sử dụng

### Đã sử dụng

- Python
- PySpark
- Apache Spark
- OpenJDK 17
- Hadoop / Winutils
- Parquet
- Snappy Compression
- Git / GitHub

### Các thành phần dự kiến cho các giai đoạn tiếp theo

- Spark MLlib
- MongoDB
- Streamlit
- Plotly

Có thể bổ sung Kafka hoặc Docker nếu phù hợp với tiến độ và phạm vi MVP.

---

## 9. Trạng thái dự án

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| Phase 01 | Data Feasibility & Project Definition | ✅ Hoàn thành |
| Phase 02 | Data Ingestion & Big Data Storage | ✅ Hoàn thành |
| Phase 03 | Data Processing / Analytics Preparation | 🔜 Tiếp theo |
| Phase 04 | Skill Demand Analytics | ⏳ Chưa thực hiện |
| Phase 05 | Feature Engineering & Trend Modeling | ⏳ Chưa thực hiện |
| Phase 06 | Model Evaluation / Hybrid Experiment | ⏳ Chưa thực hiện |
| Phase 07 | MongoDB & Dashboard | ⏳ Chưa thực hiện |
| Phase 08 | Integration / Testing / Final Report | ⏳ Chưa thực hiện |

### Hiện trạng hệ thống

```text
Raw Data
   ↓
Bronze Layer       ✅
   ↓
Spark ETL          ✅
   ↓
Silver Layer       ✅
   ↓
Skill Analytics    🔜
   ↓
Trend Modeling     ⏳
   ↓
Gold Layer         ⏳
   ↓
Dashboard          ⏳
```

**Nền tảng dữ liệu Silver Layer đã hoàn thiện và sẵn sàng cho giai đoạn tiếp theo.**

---

## 10. Tài liệu dự án

- **[Kế hoạch dự án chính](FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md)**
- **[Tổng kết Phase 01 & 02](docs/planning/phase_01_02_summary.md)**
- [Project Scope](docs/planning/project_scope.md)
- [Research Questions](docs/planning/research_questions.md)
- [GO / NO-GO Report](docs/planning/go_no_go_report.md)
- [Unified Schema](docs/data/unified_schema.md)
- [Data Dictionary](docs/data/data_dictionary.md)
- [Schema Mapping](docs/data/schema_mapping.md)
- [Deduplication Rules](docs/data/deduplication_rules.md)
- [Skill Scope](docs/skills/skill_scope.md)

---

## 11. Bước tiếp theo

Sau khi hoàn thành Phase 01 và Phase 02, trọng tâm tiếp theo của dự án là sử dụng **Silver Dataset** để xây dựng các tập dữ liệu phân tích theo:

```text
Occupation
    +
Skill
    +
Time
```

Từ đó tính toán Skill Demand Rate, Growth Rate, tạo các đặc trưng chuỗi thời gian và chuẩn bị dữ liệu cho mô hình phân loại xu hướng **Growing / Stable / Declining**.
