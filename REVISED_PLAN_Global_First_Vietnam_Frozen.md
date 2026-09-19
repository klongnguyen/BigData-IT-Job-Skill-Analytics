# REVISED PLAN — BIG DATA IT JOB MARKET SKILL FORECASTING

## Trạng thái cập nhật

**Vietnam Market: FROZEN / OPTIONAL EXTENSION**

Trong giai đoạn hiện tại, dự án chỉ triển khai và đánh giá trên **thị trường tuyển dụng quốc tế (Global Market)**.

Phần thị trường Việt Nam **không thuộc MVP** và chỉ được thực hiện nếu còn thời gian sau khi toàn bộ pipeline Global đã hoàn chỉnh.

Tuy nhiên, kiến trúc dữ liệu và cấu trúc dự án vẫn phải được thiết kế để có thể bổ sung Vietnam Market sau này mà không cần thay đổi lớn hệ thống.

---

# 1. Phạm vi chính thức của MVP

## In Scope

Dự án tập trung vào:

- Phân tích dữ liệu tuyển dụng CNTT quốc tế.
- Kết hợp Historical Data với Fresh Data.
- Chuẩn hóa Job Title.
- Chuẩn hóa Skill.
- Skill Extraction từ Job Description.
- Phân tích nhu cầu kỹ năng.
- Phân tích xu hướng theo thời gian.
- Dự báo / phân loại xu hướng kỹ năng.
- So sánh Historical Only, Recent Only và Hybrid.
- Recency Weighting.
- Dashboard trực quan.

## Out of Scope trong MVP

Các nội dung sau được đóng băng:

- Thu thập dữ liệu tuyển dụng Việt Nam.
- Phân tích riêng thị trường Việt Nam.
- Forecast riêng cho Việt Nam.
- Vietnam vs Global Skill Gap.
- Recommendation theo thị trường Việt Nam.
- Crawling TopCV / ITviec / VietnamWorks.

Các nội dung này chỉ được xem là:

> Optional Extension / Future Work

---

# 2. Mục tiêu dự án sau khi điều chỉnh

Xây dựng hệ thống Big Data có khả năng:

1. Thu thập và lưu trữ dữ liệu tuyển dụng CNTT quốc tế.
2. Kết hợp dữ liệu lịch sử và dữ liệu tuyển dụng mới.
3. Phân tích các vị trí CNTT có nhu cầu tuyển dụng cao.
4. Xác định kỹ năng quan trọng theo từng nghề.
5. Phân tích sự thay đổi nhu cầu kỹ năng theo thời gian.
6. Phân loại xu hướng:
   - Growing
   - Stable
   - Declining
7. Đánh giá hiệu quả của:
   - Historical Only
   - Recent Only
   - Hybrid + Recency Weighting
8. Xây dựng dashboard hỗ trợ người dùng theo dõi xu hướng kỹ năng.

---

# 3. Research Questions cập nhật

## RQ1
Những kỹ năng CNTT nào đang được yêu cầu nhiều nhất trên thị trường tuyển dụng quốc tế?

## RQ2
Yêu cầu kỹ năng khác nhau như thế nào giữa các vị trí CNTT?

## RQ3
Những kỹ năng nào đang có xu hướng tăng, ổn định hoặc giảm?

## RQ4
Dữ liệu tuyển dụng mới có làm thay đổi xu hướng so với dữ liệu lịch sử hay không?

## RQ5
Việc kết hợp Historical Data và Recent Data có cải thiện khả năng dự đoán xu hướng kỹ năng hay không?

## Future Research Question
Nếu mở rộng sang Việt Nam:

> Xu hướng kỹ năng CNTT tại Việt Nam khác với thị trường quốc tế như thế nào?

Câu hỏi này **không thuộc phạm vi MVP hiện tại**.

---

# 4. Phạm vi nghề CNTT

Giữ nguyên khoảng 6–8 nhóm nghề chính:

- Data Analyst
- Data Scientist
- Data Engineer
- Software Engineer
- Backend Developer
- Frontend Developer
- DevOps Engineer
- Machine Learning Engineer

---

# 5. Nguồn dữ liệu

## 5.1 Historical Data — Global

Ưu tiên dataset có:

- `job_id`
- `title`
- `company`
- `location`
- `country`
- `description`
- `experience_level`
- `salary`
- `posted_at`
- `skills`

Mục tiêu:

- Quy mô lớn.
- Có timestamp.
- Có nhiều thời điểm để tạo chuỗi thời gian.
- Có Job Description đủ để Skill Extraction.

## 5.2 Fresh Data — Global

Thu thập dữ liệu mới thông qua:

1. API chính thức.
2. Open Dataset cập nhật.
3. Crawler nếu nguồn cho phép.

Ưu tiên:

```text
API / Open Dataset
        >
Crawler
```

Fresh Data cần phục vụ:

- Phân tích xu hướng mới.
- Concept Drift.
- Recency Weighting.
- So sánh Historical vs Recent.
- Hybrid Model.

## 5.3 Vietnam Data

Trạng thái:

```text
FROZEN
```

Không thu thập trong MVP.

Chỉ triển khai nếu:

- Global Pipeline đã hoàn thiện.
- Dashboard đã hoàn thiện.
- Model đã được đánh giá.
- Còn đủ thời gian.

---

# 6. Market Dimension

Mặc dù MVP chỉ dùng Global Data, schema vẫn giữ trường:

```text
market
```

Giá trị hiện tại:

```text
GLOBAL
```

Tương lai có thể mở rộng:

```text
GLOBAL
VIETNAM
```

Điều này giúp tránh việc phải thay đổi schema khi bổ sung thị trường Việt Nam.

---

# 7. Unified Schema cập nhật

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
posted_at
collected_at
source
skills
```

Trong MVP:

```text
market = GLOBAL
```

Các trường quan trọng:

```text
posted_at
collected_at
market
source
```

---

# 8. Kiến trúc dữ liệu

## MVP hiện tại

```text
GLOBAL DATA
│
├── Historical Data
│
└── Fresh Data
        │
        ▼
      HDFS
        │
        ▼
 Bronze Layer
        │
        ▼
 Apache Spark
        │
 ┌──────┴────────┐
 │ Cleaning      │
 │ Deduplication │
 │ Normalization │
 │ Skill Extract │
 └──────┬────────┘
        │
        ▼
 Silver Layer
        │
        ▼
 Feature Engineering
        │
        ├───────────────┐
        ▼               ▼
   Analytics        Spark MLlib
        │               │
        │          Trend Prediction
        └───────┬───────┘
                ▼
            Gold Layer
                │
                ▼
             MongoDB
                │
                ▼
        Streamlit Dashboard
```

---

# 9. Cấu trúc dữ liệu có khả năng mở rộng Vietnam Market

```text
/jobs/

├── bronze/
│   ├── global/
│   │   ├── historical/
│   │   └── fresh/
│   │
│   └── vietnam/
│       ├── historical/
│       └── fresh/
│
├── silver/
│   ├── global/
│   └── vietnam/
│
└── gold/
    ├── global/
    │   ├── skill_stats/
    │   ├── job_stats/
    │   └── predictions/
    │
    └── vietnam/
        ├── skill_stats/
        ├── job_stats/
        └── predictions/
```

Trong MVP, `vietnam/` chỉ là placeholder hoặc chưa có dữ liệu.

---

# 10. Repository Structure đề xuất

```text
BigData-IT-Job-Skill-Analytics/
│
├── data/
│   ├── global/
│   │   ├── sample/
│   │   ├── raw/
│   │   └── processed/
│   │
│   └── vietnam/
│       └── README.md
│
├── docs/
│   ├── planning/
│   ├── data/
│   ├── architecture/
│   └── future_work/
│       └── vietnam_market_extension.md
│
├── config/
│   ├── skills.json
│   ├── job_title_mapping.json
│   └── markets.json
│
├── notebooks/
│
├── src/
│   ├── ingestion/
│   ├── processing/
│   ├── analytics/
│   ├── ml/
│   └── dashboard/
│
├── tests/
│
├── README.md
└── PLAN.md
```

Ví dụ `markets.json`:

```json
{
  "GLOBAL": {
    "enabled": true
  },
  "VIETNAM": {
    "enabled": false
  }
}
```

---

# 11. Phase 1 — Data Feasibility cập nhật

## Mục tiêu

Xác nhận rằng dữ liệu Global đủ điều kiện để thực hiện toàn bộ dự án.

| ID | Công việc | Trạng thái |
|---|---|---|
| P1-01 | Chốt Project Scope | Global only |
| P1-02 | Chốt Research Questions | Global only |
| P1-03 | Chốt nhóm nghề | Thực hiện |
| P1-04 | Chốt Skill Taxonomy | Thực hiện |
| P1-05 | Khảo sát Historical Global Dataset | Bắt buộc |
| P1-06 | Đánh giá Historical Dataset | Bắt buộc |
| P1-07 | Khảo sát Fresh Global Data | Bắt buộc |
| P1-08 | Kiểm tra API / Fresh Source | Bắt buộc |
| P1-09 | Crawler dự phòng | Khi cần |
| P1-10 | Thu Sample Data | Bắt buộc |
| P1-11 | Data Profiling | Bắt buộc |
| P1-12 | Schema Mapping | Bắt buộc |
| P1-13 | Unified Schema | Bắt buộc |
| P1-14 | Data Dictionary | Bắt buộc |
| P1-15 | Duplicate Strategy | Bắt buộc |
| P1-16 | Timestamp Strategy | Bắt buộc |
| P1-17 | Job Title Normalization thử nghiệm | Bắt buộc |
| P1-18 | Skill Extraction thử nghiệm | Bắt buộc |
| P1-19 | Time Coverage Analysis | Bắt buộc |
| P1-20 | GO / NO-GO | Bắt buộc |
| P1-VN | Vietnam Data Feasibility | FROZEN |

---

# 12. GO / NO-GO cập nhật

Chỉ đánh giá Global Data:

```text
1. Có Historical Global Dataset đủ lớn?
             ↓
            YES

2. Dataset có posted_at / timestamp?
             ↓
            YES

3. Có Fresh Global Data?
             ↓
            YES

4. Job Description đủ tốt cho Skill Extraction?
             ↓
            YES

5. Có thể Normalize Job Title + Skill?
             ↓
            YES

6. Có đủ time point để phân tích xu hướng?
             ↓
            YES
```

Nếu cả 6 đều đạt:

```text
GO
```

Vietnam Market **không phải điều kiện GO/NO-GO của MVP**.

---

# 13. Machine Learning

## Model A — Historical Only

```text
Historical Global Data
        ↓
Prediction
```

## Model B — Recent Only

```text
Recent Global Data
        ↓
Prediction
```

## Model C — Hybrid

```text
Historical
    +
Recent
    +
Recency Weighting
        ↓
Prediction
```

Mục tiêu:

> Đánh giá liệu việc kết hợp dữ liệu tuyển dụng lịch sử và dữ liệu mới có cải thiện khả năng dự báo xu hướng kỹ năng trên thị trường quốc tế hay không.

---

# 14. Time-based Split

Không dùng random split cho trend forecasting.

Ví dụ:

```text
TRAIN
2024 ---------------- 2025

VALIDATION
2026 Q1 ----------- 2026 Q2

TEST
2026 Q3
```

Nguyên tắc:

```text
Past
 ↓
Future
```

---

# 15. Dashboard cập nhật

## Page 1 — Global Market Overview

- Total Jobs
- Companies
- Countries
- Skills
- Jobs Over Time
- Top Occupations
- Experience Distribution

## Page 2 — Skill Analytics

Theo:

- Occupation
- Country
- Experience
- Time

## Page 3 — Job Comparison

So sánh kỹ năng giữa các occupation.

## Page 4 — Skill Trend

Hiển thị:

- Demand Rate
- Growth Rate
- Historical Trend
- Recent Trend

## Page 5 — Forecast

Hiển thị:

- Growing
- Stable
- Declining

## Future Page — Market Comparison

```text
Vietnam vs Global
```

Không triển khai trong MVP.

---

# 16. Kế hoạch 10 tuần cập nhật

| Tuần | Công việc | Kết quả |
|---|---|---|
| 1 | Chốt phạm vi Global, khảo sát Historical + Fresh Data | Proposal + Data Sources |
| 2 | Thu Historical Data, test Fresh Source, Unified Schema | Dataset Sample + Data Dictionary |
| 3 | HDFS + Spark + Bronze Layer + Ingestion | Pipeline ingestion |
| 4 | Spark Cleaning + Dedup + Normalization | Silver Dataset V1 |
| 5 | Skill Dictionary + Skill Extraction | Skill Extraction Pipeline |
| 6 | Spark EDA + Skill Demand Analytics | Analytics Report |
| 7 | Feature Engineering + Trend Model | Baseline Model |
| 8 | Historical vs Recent vs Hybrid + Recency Weighting | Model Comparison |
| 9 | MongoDB + Streamlit | Demo hoàn chỉnh |
| 10 | Testing + Report + Slide + Presentation | Final Product |

Vietnam Market không nằm trong lịch 10 tuần MVP.

---

# 17. MVP Checklist cập nhật

- [ ] Historical Global Dataset
- [ ] Fresh Global Dataset
- [ ] Timestamp Validation
- [ ] HDFS Storage
- [ ] Bronze Layer
- [ ] Spark ETL
- [ ] Data Cleaning
- [ ] Deduplication
- [ ] Job Title Normalization
- [ ] Skill Normalization
- [ ] Skill Extraction
- [ ] Skill Demand Analytics
- [ ] Time-based Trend Analysis
- [ ] Spark ML Model
- [ ] Historical vs Recent vs Hybrid Experiment
- [ ] Recency Weighting
- [ ] Model Evaluation
- [ ] MongoDB
- [ ] Streamlit Dashboard
- [ ] Final Report

Không thuộc MVP:

- [ ] Vietnam Dataset
- [ ] Vietnam Forecast
- [ ] Vietnam vs Global Comparison
- [ ] Vietnam Recommendation

---

# 18. Future Extension — Vietnam Market

Vietnam Market được giữ làm phase mở rộng.

Khi triển khai:

```text
Vietnam Historical Data
        +
Vietnam Fresh Data
        ↓
Same Unified Schema
        ↓
Same Spark Pipeline
        ↓
Vietnam Silver Layer
        ↓
Vietnam Skill Analytics
        ↓
Vietnam Trend Model
        ↓
Vietnam vs Global Comparison
```

Mục tiêu kiến trúc hiện tại là đảm bảo phần này có thể được thêm vào mà không phải viết lại toàn bộ hệ thống.

---

# 19. Nguyên tắc phát triển

## Principle 1 — Global First

Hoàn thành Global MVP trước mọi extension.

## Principle 2 — One Unified Schema, Multiple Markets

Schema hỗ trợ nhiều market ngay từ đầu.

## Principle 3 — Separate Market Analytics

Nếu Vietnam được bổ sung sau này, không trộn demand rate của Vietnam và Global thành một chỉ số duy nhất.

## Principle 4 — Do not over-engineer Vietnam now

Chỉ chừa:

- schema field
- folder
- config
- architecture hook

Không xây pipeline Việt Nam trong MVP.

---

# 20. Quyết định chính thức

```text
GLOBAL MARKET      = ACTIVE
VIETNAM MARKET     = FROZEN
```

Mục tiêu hiện tại:

```text
Historical Global Data
        +
Fresh Global Data
        ↓
HDFS
        ↓
Apache Spark
        ↓
Normalized Job Data
        ↓
Skill Analytics
        ↓
Trend Forecast
        ↓
Dashboard
```

Vietnam Market sẽ được xem là:

```text
Future Extension
```

và chỉ được triển khai nếu MVP Global đã hoàn thành đầy đủ.
