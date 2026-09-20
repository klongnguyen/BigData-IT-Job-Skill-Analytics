# TỔNG KẾT GIAI ĐOẠN 1 & 2: BIG DATA IT JOB SKILL ANALYTICS

Tài liệu này tóm tắt toàn bộ kết quả đã thực hiện và nghiệm thu trong **Giai đoạn 1 (Data Feasibility & Project Definition)** và **Giai đoạn 2 (Data Ingestion & Big Data Storage)** theo chuẩn của [FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md).

---

## 1. GIAI ĐOẠN 1: DATA FEASIBILITY & PROJECT DEFINITION

### 1.1. Phạm vi đề tài & 6 Câu hỏi nghiên cứu (RQ1 – RQ6)
- **Phạm vi thị trường**:
  - **Global Market**: Là trọng tâm chính thức của MVP (`market = "GLOBAL"`).
  - **Vietnam Market**: Ở trạng thái **FROZEN (Đóng băng)**, là phần mở rộng tương lai (Future Work) sau khi MVP hoàn tất.
- **Nguyên tắc cốt lõi**: Dự báo xu hướng kỹ năng **phải dựa trên từng nhóm nghề (Occupation-Based)** theo bộ ba `(Occupation + Skill + Time)`, tuyệt đối không dự báo gộp chung cho toàn ngành CNTT.
- **6 Câu hỏi nghiên cứu**:
  - `RQ1`: Nhu cầu tuyển dụng giữa các vị trí CNTT quốc tế.
  - `RQ2`: Kỹ năng cốt lõi theo từng nhóm nghề.
  - `RQ3`: Biến thiên nhu cầu kỹ năng theo thời gian trong từng occupation.
  - `RQ4`: Phân loại xu hướng (Growing / Stable / Declining) theo từng occupation.
  - `RQ5`: Hiện tượng dịch chuyển công nghệ (Concept Drift) giữa dữ liệu lịch sử và dữ liệu mới.
  - `RQ6`: Đánh giá hiệu quả của mô hình Hybrid kết hợp Recency Weighting so với mô hình đơn lẻ.
- **Tài liệu bàn giao**:
  - [project_scope.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/planning/project_scope.md)
  - [research_questions.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/planning/research_questions.md)

### 1.2. Taxonomy 8 Nhóm nghề & 8 Nhóm kỹ năng
- **8 Nhóm nghề chuẩn**: Data Analyst, Data Scientist, Data Engineer, Machine Learning Engineer, Software Engineer, Backend Developer, Frontend Developer, DevOps Engineer.
- **Taxonomy kỹ năng**: 8 nhóm công nghệ với 35+ kỹ năng và hàng trăm từ khóa đồng nghĩa (synonyms).
- **Tài liệu & Cấu hình**:
  - [skill_scope.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/skills/skill_scope.md)
  - [skills_v0.json](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/configs/skills_v0.json)
  - [job_title_mapping_v0.json](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/configs/job_title_mapping_v0.json)
  - [markets.json](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/configs/markets.json)

### 1.3. Khảo sát nguồn dữ liệu & Đánh giá Khả thi (Milestone 1 GO)
- **Historical Data**: Khảo sát và chọn tập dữ liệu Luke Barousse (>780.000 bản ghi) với 100% trường `job_posted_date` chuẩn ISO.
- **Fresh Data (2026)**: Kiểm thử kết nối thành công 2 API thời gian thực: Arbeitnow API và Remotive API.
- **Kiểm định thực nghiệm**: Chạy script [test_phase01_feasibility.py](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/tests/test_phase01_feasibility.py) trên 567 bản ghi mẫu:
  - Tỷ lệ trích xuất kỹ năng đạt trung bình **5.57 skills/JD**.
  - Dữ liệu trải dài liên tục qua 50 tháng (2022 đến 2026).
- **Quyết định**: Đạt 100% tiêu chí $\rightarrow$ **Quyết định GO**.
- **Tài liệu bàn giao**:
  - [historical_data_evaluation.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/data/historical_data_evaluation.md)
  - [fresh_data_evaluation.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/data/fresh_data_evaluation.md)
  - [data_profile.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/data/data_profile.md)
  - [go_no_go_report.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/planning/go_no_go_report.md)

### 1.4. Thiết kế Unified Schema 18 trường & Quy tắc Khử trùng lặp
- Chuẩn hóa cấu trúc dữ liệu cho toàn bộ hệ thống gồm đúng 18 trường:
  `job_id, title, normalized_title, company, location, city, country, market, work_mode, description, experience_level, salary_min, salary_max, currency, posted_at, collected_at, source, skills`.
- Thiết kế thuật toán sinh mã băm SHA-256 `job_hash` và quy tắc lọc tin trùng lặp / tin repost.
- **Tài liệu bàn giao**:
  - [unified_schema.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/data/unified_schema.md)
  - [data_dictionary.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/data/data_dictionary.md)
  - [schema_mapping.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/data/schema_mapping.md)
  - [deduplication_rules.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/docs/data/deduplication_rules.md)

---

## 2. GIAI ĐOẠN 2: DATA INGESTION & BIG DATA STORAGE

### 2.1. Thiết lập hoàn tất Môi trường Big Data trên Windows
1. **PySpark 4.2.0**: Đã cài đặt thành công trong môi trường Python 3.11.
2. **OpenJDK 17 LTS**: Đã tải và cài đặt tại `C:\java\jdk-17`, cấu hình biến môi trường `JAVA_HOME`.
3. **Hadoop Winutils**: Cấu hình tiện ích `winutils.exe` và `hadoop.dll` tại `C:\hadoop\bin`, thiết lập biến môi trường `HADOOP_HOME`.
4. **Biến thực thi Python**: Thiết lập `PYSPARK_PYTHON` và `PYSPARK_DRIVER_PYTHON` trỏ đến `python.exe` chuẩn của hệ thống để chạy Spark worker trơn tru.

### 2.2. Dữ liệu thô & Bronze Layer (Raw Ingestion)
- Tải về toàn bộ file dữ liệu lịch sử chuẩn: [data/raw/data_jobs.csv](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/data/raw/data_jobs.csv) dung lượng **231 MB** (~780.000 tin tuyển dụng).
- Xây dựng module Ingestion:
  - [historical_ingestion.py](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/src/ingestion/historical_ingestion.py): Nạp đợt đầu **50.000 bản ghi** vào `data/bronze/global/historical/historical_batch_001.json` kèm metadata (`ingestion_id`, `collected_at`, `market="GLOBAL"`, `source="kaggle_historical_archive"`).
  - [fresh_ingestion.py](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/src/ingestion/fresh_ingestion.py): Gọi trực tiếp API lấy **267 bản ghi mới năm 2026** vào `data/bronze/global/fresh/`.

### 2.3. Pipeline Apache Spark ETL (Bronze $\rightarrow$ Silver Layer)
- Module thực thi: [src/processing/spark_etl.py](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/src/processing/spark_etl.py).
- Kết quả thực nghiệm của Spark:
  ```text
  - Đọc vào từ Bronze Layer: 50,267 bản ghi
  - Làm sạch văn bản, chuẩn hóa khoảng trắng: 100% bản ghi
  - Khử trùng lặp qua job_hash (SHA-256): Lọc bỏ 180 bản ghi trùng
  - Số bản ghi sạch cuối cùng: 50,087 bản ghi
  - Chuẩn hóa Job Title: Ánh xạ chính xác về 8 nhóm nghề chính
  - Trích xuất kỹ năng: Áp dụng từ điển skills_v0.json
  - Ép chuẩn: Đúng 18 trường của Unified Schema
  - Xuất ra Silver Layer: Định dạng Parquet nén Snappy tại data/silver/global/
    phân vùng đầy đủ theo 12 tháng năm 2023 và năm 2026 (year=2023/month=..., year=2026/month=...).
  ```

---

## 3. Trạng thái hiện tại của Codebase

```text
BigData-IT-Job-Skill-Analytics/
│
├── configs/
│   ├── job_title_mapping_v0.json   (Ánh xạ chức danh về 8 nhóm nghề)
│   ├── skills_v0.json              (Từ điển 35+ kỹ năng với regex)
│   └── markets.json                (Quản lý bật/tắt Global & Vietnam)
│
├── data/
│   ├── raw/
│   │   └── data_jobs.csv           (File gốc 231 MB, ~780.000 dòng)
│   ├── bronze/
│   │   └── global/
│   │       ├── historical/         (50.000 bản ghi raw JSON kèm metadata)
│   │       └── fresh/              (267 bản ghi fresh 2026 raw JSON)
│   ├── silver/
│   │   └── global/                 (50.087 bản ghi Parquet phân vùng theo year/month)
│   └── sample/                     (Tập mẫu kiểm thử Phase 1)
│
├── docs/
│   ├── planning/                   (Scope, RQ1-RQ6, GO/NO-GO, Summary)
│   ├── data/                       (Unified Schema, Dictionary, Mapping, Dedup)
│   └── skills/                     (Skill Taxonomy & Regex Rules)
│
├── src/
│   ├── ingestion/
│   │   ├── historical_ingestion.py (Nạp dữ liệu lịch sử vào Bronze)
│   │   └── fresh_ingestion.py      (Nạp dữ liệu API 2026 vào Bronze)
│   └── processing/
│       └── spark_etl.py            (Spark ETL chuyển đổi Bronze -> Silver)
│
└── tests/
    └── test_phase01_feasibility.py (Kiểm định khả thi Giai đoạn 1)
```

**Toàn bộ nền tảng dữ liệu sạch (Silver Layer) đã hoàn thiện và sẵn sàng 100% cho Giai đoạn 3!**
