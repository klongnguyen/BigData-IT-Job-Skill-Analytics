# FINAL PROJECT PLAN
## Big Data IT Job Market Skill Analytics & Forecasting

---

# 1. Tên đề tài

## Tiếng Việt

**Xây dựng hệ thống Big Data phân tích thị trường tuyển dụng CNTT và dự báo xu hướng nhu cầu kỹ năng theo nhóm nghề từ dữ liệu lịch sử và dữ liệu tuyển dụng mới**

## Tiếng Anh

**A Big Data System for IT Job Market Analytics and Occupation-Based Skill Demand Forecasting Using Historical and Recent Recruitment Data**

---

# 2. Định hướng chính thức của dự án

Dự án tập trung vào:

```text
GLOBAL MARKET = ACTIVE
VIETNAM MARKET = FROZEN / FUTURE EXTENSION
```

Trong MVP:

- Chỉ sử dụng dữ liệu tuyển dụng quốc tế.
- Không crawl hoặc dự báo thị trường Việt Nam.
- Không trộn dữ liệu Việt Nam và quốc tế.
- Kiến trúc vẫn chừa sẵn khả năng mở rộng cho Việt Nam sau này.

Một nguyên tắc quan trọng khác:

> Dự báo kỹ năng không được thực hiện chung cho toàn ngành CNTT khi dùng cho tư vấn nghề nghiệp.

Forecast phải dựa trên:

```text
Occupation
    +
Skill
    +
Time
```

Ví dụ:

```text
Frontend Developer
        +
TypeScript
        +
2024 → 2026
        ↓
Growing
```

không phải:

```text
TypeScript
    ↓
Growing trong toàn IT
```

---

# 3. Mục tiêu dự án

Hệ thống cần có khả năng:

1. Thu thập và lưu trữ dữ liệu tuyển dụng CNTT quốc tế quy mô lớn.
2. Kết hợp Historical Data và Recent Data.
3. Chuẩn hóa dữ liệu từ nhiều nguồn.
4. Phân loại Job Posting về các nhóm nghề CNTT chuẩn.
5. Trích xuất kỹ năng từ Job Description.
6. Phân tích nhu cầu kỹ năng theo từng nghề.
7. Phân tích thay đổi nhu cầu kỹ năng theo thời gian.
8. Phân loại xu hướng kỹ năng:
   - Growing
   - Stable
   - Declining
9. So sánh:
   - Historical Only
   - Recent Only
   - Hybrid
10. Áp dụng Recency Weighting.
11. Xây dựng dashboard trực quan.
12. Hỗ trợ người dùng xác định kỹ năng phù hợp với nghề họ muốn theo đuổi.

---

# 4. Research Questions

## RQ1

Những vị trí CNTT nào đang có nhu cầu tuyển dụng cao trên thị trường quốc tế?

## RQ2

Những kỹ năng nào được yêu cầu nhiều nhất đối với từng nhóm nghề CNTT?

## RQ3

Nhu cầu kỹ năng thay đổi như thế nào theo thời gian trong từng occupation?

## RQ4

Những kỹ năng nào đang:

```text
Growing
Stable
Declining
```

trong từng nhóm nghề?

## RQ5

Dữ liệu tuyển dụng mới có làm thay đổi xu hướng so với dữ liệu lịch sử hay không?

## RQ6

Việc kết hợp Historical Data với Recent Data và Recency Weighting có cải thiện khả năng dự báo xu hướng kỹ năng hay không?

---

# 5. Phạm vi nghề CNTT

MVP tập trung vào khoảng 8 occupation:

```text
Data Analyst
Data Scientist
Data Engineer
Software Engineer
Backend Developer
Frontend Developer
DevOps Engineer
Machine Learning Engineer
```

Job title thực tế sẽ được normalize về các nhóm này.

Ví dụ:

```text
React Developer
Frontend Engineer
UI Web Developer
Javascript Frontend Engineer

        ↓

Frontend Developer
```

---

# 6. Nhóm kỹ năng

## Programming

```text
Python
Java
JavaScript
TypeScript
C++
C#
```

## Database

```text
SQL
MySQL
PostgreSQL
MongoDB
Redis
```

## Data / Big Data

```text
Spark
Hadoop
Kafka
Hive
Airflow
Pandas
NumPy
```

## Frontend

```text
React
Vue
Angular
Next.js
HTML
CSS
```

## Backend

```text
Spring Boot
Node.js
Django
Flask
.NET
REST API
```

## Cloud

```text
AWS
Azure
GCP
```

## DevOps

```text
Docker
Kubernetes
Jenkins
Terraform
CI/CD
```

## AI / ML

```text
TensorFlow
PyTorch
Scikit-learn
LLM
Generative AI
RAG
```

## BI

```text
Power BI
Tableau
Excel
```

Skill taxonomy có thể tiếp tục mở rộng sau khi Data Profiling.

---

# 7. Nguồn dữ liệu

## 7.1 Historical Global Data

Historical Dataset cần ưu tiên có:

```text
job_id
title
company
location
country
description
experience_level
salary
posted_at
skills
```

Yêu cầu quan trọng nhất:

```text
Có timestamp
+
Có Job Description
+
Có đủ dữ liệu theo thời gian
```

## 7.2 Recent / Fresh Global Data

Fresh Data được thu thập từ:

```text
Official API
    >
Updated Open Dataset
    >
Crawler nếu được phép
```

Mục tiêu:

- Bổ sung dữ liệu gần thời điểm hiện tại.
- Phát hiện Concept Drift.
- Đánh giá Recent Trend.
- Thực hiện Hybrid Forecast.
- Áp dụng Recency Weighting.

## 7.3 Vietnam Market

Trạng thái:

```text
FROZEN
```

Không thuộc MVP.

Chỉ thực hiện nếu:

```text
Global Pipeline hoàn chỉnh
+
Model hoàn chỉnh
+
Dashboard hoàn chỉnh
+
Còn thời gian
```

---

# 8. Unified Schema

Schema chuẩn:

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

Trong MVP:

```text
market = GLOBAL
```

Tương lai:

```text
market = GLOBAL
market = VIETNAM
```

---

# 9. Kiến trúc hệ thống

```text
                GLOBAL JOB DATA
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
 Historical Dataset          Recent Data
          │                       │
          └───────────┬───────────┘
                      ▼
               Data Ingestion
                      │
                      ▼
                    HDFS
                      │
                      ▼
                BRONZE LAYER
                 Raw Job Data
                      │
                      ▼
                Apache Spark
                      │
       ┌──────────────┼──────────────┐
       │              │              │
    Cleaning     Normalization   Deduplication
       │              │              │
       └──────────────┼──────────────┘
                      │
              Job Classification
                      │
                      ▼
                Skill Extraction
                      │
                      ▼
                SILVER LAYER
                      │
                      ▼
             Feature Engineering
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
      Analytics               Spark MLlib
          │                       │
 Occupation-Skill            Trend Model
    Analytics                     │
          │                       │
          └───────────┬───────────┘
                      ▼
                  GOLD LAYER
                      │
                      ▼
                   MongoDB
                      │
                      ▼
             Streamlit Dashboard
```

---

# 10. Bronze – Silver – Gold

## Bronze Layer

Lưu dữ liệu gần raw nhất.

```text
Historical
Recent
```

Chỉ thêm metadata cần thiết:

```text
source
market
collected_at
ingestion_id
```

Không thực hiện cleaning sâu.

## Silver Layer

Dữ liệu đã:

- Clean.
- Deduplicate.
- Normalize Job Title.
- Normalize Location.
- Normalize Experience.
- Normalize Skill.
- Chuẩn hóa timestamp.
- Skill Extraction.

## Gold Layer

Dữ liệu phục vụ:

```text
Analytics
Dashboard
Machine Learning
Forecast
```

Ví dụ:

```text
occupation_skill_monthly_stats
occupation_stats
skill_trends
model_predictions
```

---

# 11. Cấu trúc HDFS

```text
/jobs/

├── bronze/
│   ├── global/
│   │   ├── historical/
│   │   └── fresh/
│   │
│   └── vietnam/
│
├── silver/
│   ├── global/
│   └── vietnam/
│
└── gold/
    ├── global/
    │   ├── occupation_stats/
    │   ├── skill_stats/
    │   ├── trends/
    │   └── predictions/
    │
    └── vietnam/
```

`vietnam/` chỉ là placeholder trong MVP.

---

# 12. Job Title Normalization

Đây là một trong những bước quan trọng nhất của dự án.

Ví dụ:

```text
Junior React Developer
React.js Engineer
Frontend Engineer
Web UI Engineer

        ↓

Frontend Developer
```

Nếu bước này sai:

```text
Occupation sai
    ↓
Skill Demand sai
    ↓
Trend sai
    ↓
Forecast sai
```

---

# 13. Skill Extraction

Ví dụ Job Description:

```text
We are looking for a Frontend Developer
with React, TypeScript, Next.js and Docker.
```

Output:

```text
React
TypeScript
Next.js
Docker
```

Dữ liệu dạng:

| job_id | occupation | skill |
|---|---|---|
| 001 | Frontend Developer | React |
| 001 | Frontend Developer | TypeScript |
| 001 | Frontend Developer | Next.js |
| 001 | Frontend Developer | Docker |

---

# 14. Skill Demand Analytics

Demand Rate phải được tính theo occupation.

Công thức:

```text
Demand Rate(skill, occupation, time)

Jobs của occupation có chứa skill
---------------------------------
Tổng job của occupation trong thời gian đó
```

Ví dụ:

### Frontend Developer

```text
React       68%
TypeScript  57%
Next.js     35%
Docker      21%
```

### Backend Developer

```text
SQL         74%
Java        53%
Spring      48%
Docker      44%
Kafka       31%
```

Không sử dụng một Demand Rate chung cho toàn IT để recommendation.

---

# 15. Hai tầng Analytics

## Layer 1 – Macro Market Analytics

Phân tích toàn ngành:

```text
Total Jobs
Top Occupations
Top Skills
Job Growth
Country Distribution
Experience Distribution
```

Mục tiêu:

> Cho biết thị trường CNTT quốc tế đang thay đổi như thế nào.

## Layer 2 – Occupation Analytics

Phân tích theo nghề:

```text
Occupation
    ↓
Skills
    ↓
Demand Rate
    ↓
Time Trend
```

Layer này được sử dụng cho:

```text
Forecast
Recommendation
Career Guidance
```

---

# 16. Feature Engineering

Dataset cho ML:

```text
occupation
skill
month

demand_rate
growth_rate

lag_1
lag_2
lag_3

job_count

recency_weight
```

Ví dụ:

```text
occupation = Frontend Developer
skill = TypeScript
month = 2026-07

demand_rate = 0.57
growth_rate = 0.08

lag_1 = 0.54
lag_2 = 0.51
lag_3 = 0.49
```

---

# 17. Forecast Target

Target:

```text
Growing
Stable
Declining
```

Ví dụ:

```text
Frontend Developer
+
TypeScript
        ↓
Growing
```

```text
Backend Developer
+
Kafka
        ↓
Growing
```

Hai kết quả hoàn toàn độc lập.

---

# 18. Machine Learning Strategy

Ưu tiên:

```text
One Global Model
+
Occupation as Feature
```

thay vì xây 8 model riêng ngay từ đầu.

Input:

```text
occupation
skill
time
demand features
lag features
recency features
```

Output:

```text
Growing
Stable
Declining
```

Model đề xuất:

```text
Logistic Regression
Random Forest
Gradient Boosted Trees
```

Triển khai:

```text
Spark MLlib
```

---

# 19. Experiment chính

## Model A – Historical Only

```text
Historical Data
        ↓
Forecast
```

## Model B – Recent Only

```text
Recent Data
        ↓
Forecast
```

## Model C – Hybrid

```text
Historical
    +
Recent
    +
Recency Weighting
        ↓
Forecast
```

So sánh:

| Model | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Historical | | | | |
| Recent | | | | |
| Hybrid | | | | |

Research Objective:

> Xác định liệu Historical + Recent + Recency Weighting có cải thiện khả năng dự báo xu hướng kỹ năng theo occupation hay không.

---

# 20. Recency Weighting

Dữ liệu mới được ưu tiên cao hơn.

Ví dụ:

```text
2024      → lower weight
2025      → medium weight
2026      → high weight
```

Có thể dùng:

```text
weight = exp(-lambda × age)
```

Mục tiêu:

> Giảm ảnh hưởng của những yêu cầu kỹ năng đã lỗi thời.

---

# 21. Time-Based Split

Không dùng Random Split cho bài toán trend.

Ví dụ:

```text
TRAIN
2024 ---------------- 2025

VALIDATION
2026 Q1 -------- 2026 Q2

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

# 22. Dashboard

## Page 1 – Global IT Market Overview

Hiển thị:

```text
Total Jobs
Companies
Countries
Top Occupations
Top Skills
Jobs Over Time
Experience Distribution
```

## Page 2 – Occupation Analytics

User chọn:

```text
Occupation:
[ Frontend Developer ▼ ]
```

Hiển thị:

```text
Total Jobs
Top Skills
Top Countries
Experience
Demand Rate
```

## Page 3 – Skill Analytics

Ví dụ:

```text
Occupation:
Frontend Developer

Skill:
TypeScript
```

Hiển thị:

```text
Demand Rate
Job Count
Growth
Historical Trend
Recent Trend
```

## Page 4 – Job Comparison

Ví dụ:

```text
Frontend Developer
        VS
Backend Developer
```

So sánh:

```text
Skills
Demand
Experience
Cloud
DevOps
```

## Page 5 – Forecast

Input:

```text
Target Career:
[ Frontend Developer ▼ ]
```

Output:

```text
React          Stable
TypeScript     Growing
Next.js        Growing
Vue            Stable
Angular        Declining
```

---

# 23. Recommendation Layer

Recommendation không dựa trên:

```text
Toàn ngành IT đang cần gì?
```

mà dựa trên:

```text
Người dùng muốn theo nghề gì?
```

Input cơ bản:

```text
Target Occupation
Experience Level
```

Ví dụ:

```text
Target:
Frontend Developer

Level:
Junior
```

Hệ thống đưa ra:

```text
High Current Demand
+
Growing Skills
+
Relevant Skills
```

Không khuyến nghị Kafka cho Frontend chỉ vì Kafka tăng toàn ngành.

---

# 24. Future Vietnam Extension

Sau khi Global MVP hoàn thiện:

```text
Vietnam Historical
        +
Vietnam Fresh
        ↓
Same Unified Schema
        ↓
Same Spark Pipeline
        ↓
Vietnam Analytics
        ↓
Vietnam Forecast
```

Khi đó mới có thể xây:

```text
Vietnam vs Global
```

và:

```text
Skill Gap
Market Comparison
Vietnam Recommendation
```

---

# 25. Cấu trúc repository

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
│   ├── analytics/
│   └── future_work/
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
│   ├── normalization/
│   ├── skill_extraction/
│   ├── analytics/
│   ├── ml/
│   └── dashboard/
│
├── tests/
│
├── README.md
└── PLAN.md
```

---

# 26. Các Phase chính

## Phase 1 – Data Feasibility

Trạng thái:

```text
COMPLETED
```

Kết quả:

```text
Project Scope
Research Questions
Historical Data Validation
Fresh Data Validation
Unified Schema
GO / NO-GO
```

## Phase 2 – Data Ingestion & Big Data Storage

Mục tiêu:

```text
Source
 ↓
HDFS Bronze
 ↓
Spark Read
```

Task:

```text
P2-01 Hadoop / HDFS Setup
P2-02 Spark / PySpark Setup
P2-03 Bronze / Silver / Gold Structure
P2-04 Historical Data Loader
P2-05 Fresh Data Collector
P2-06 Metadata
P2-07 Validation
P2-08 Bronze Storage
P2-09 Spark Read Test
P2-10 Logging
P2-11 End-to-End Test
```

Milestone:

```text
M2 – Global Data Ingestion Ready
```

## Phase 3 – Spark ETL & Silver Layer

Thực hiện:

```text
Missing Values
Timestamp Cleaning
Salary Cleaning
Location Cleaning
Deduplication
Job Title Normalization
Experience Normalization
Skill Normalization
```

Milestone:

```text
M3 – Clean Normalized Job Dataset
```

## Phase 4 – Skill Extraction

Thực hiện:

```text
Skill Dictionary
Alias Mapping
Skill Extraction
Skill Validation
Job-Skill Table
```

Milestone:

```text
M4 – Occupation-Skill Dataset Ready
```

## Phase 5 – Analytics

Thực hiện:

```text
Market Overview
Occupation Analytics
Skill Demand Rate
Skill Growth Rate
Trend Analysis
Country Analysis
Experience Analysis
```

Milestone:

```text
M5 – Analytics Layer Ready
```

## Phase 6 – Feature Engineering

Xây:

```text
occupation
skill
month
demand_rate
growth_rate
lag_1
lag_2
lag_3
job_count
recency_weight
```

Milestone:

```text
M6 – ML Dataset Ready
```

## Phase 7 – Trend Prediction

Train:

```text
Historical Model
Recent Model
Hybrid Model
```

Đánh giá:

```text
Accuracy
Precision
Recall
F1-score
```

Milestone:

```text
M7 – Forecast Model Ready
```

## Phase 8 – Gold Layer & MongoDB

Tạo:

```text
occupation_stats
skill_stats
skill_trends
predictions
```

Lưu vào MongoDB phục vụ Dashboard.

Milestone:

```text
M8 – Serving Layer Ready
```

## Phase 9 – Dashboard

Xây:

```text
Global Overview
Occupation Analytics
Skill Analytics
Job Comparison
Trend
Forecast
```

Milestone:

```text
M9 – Working Demo
```

## Phase 10 – Evaluation & Finalization

Thực hiện:

```text
End-to-End Testing
Model Evaluation
Pipeline Testing
Dashboard Testing
Report
Slides
Demo
Presentation
```

Milestone:

```text
M10 – Final Project
```

---

# 27. Roadmap 10 tuần

| Tuần | Nội dung |
|---|---|
| 1 | Data Feasibility |
| 2 | Data Ingestion + HDFS |
| 3 | Spark ETL |
| 4 | Job Normalization + Dedup |
| 5 | Skill Extraction |
| 6 | Occupation & Skill Analytics |
| 7 | Feature Engineering |
| 8 | Trend Model + Experiments |
| 9 | MongoDB + Dashboard |
| 10 | Testing + Report + Presentation |

---

# 28. MVP bắt buộc

```text
Historical Global Data
        +
Recent Global Data
        ↓
HDFS
        ↓
Spark ETL
        ↓
Job Classification
        ↓
Skill Extraction
        ↓
Occupation Skill Analytics
        ↓
Trend Prediction
        ↓
MongoDB
        ↓
Dashboard
```

Checklist:

- [x] Phase 1 Data Feasibility
- [ ] Historical ingestion
- [ ] Fresh ingestion
- [ ] HDFS
- [ ] Spark
- [ ] Bronze Layer
- [ ] Silver Layer
- [ ] Deduplication
- [ ] Job Title Normalization
- [ ] Skill Normalization
- [ ] Skill Extraction
- [ ] Occupation Analytics
- [ ] Skill Demand Rate
- [ ] Trend Analysis
- [ ] Feature Engineering
- [ ] Historical Model
- [ ] Recent Model
- [ ] Hybrid Model
- [ ] Recency Weighting
- [ ] Model Evaluation
- [ ] Gold Layer
- [ ] MongoDB
- [ ] Dashboard
- [ ] Final Report

---

# 29. Optional Features

Chỉ làm sau MVP:

```text
Vietnam Market
Vietnam vs Global Comparison
Salary Prediction
Career Recommendation nâng cao
Skill Gap Analysis
FP-Growth Skill Combination
Kafka Streaming
Real-time Pipeline
Advanced NLP
LLM Skill Extraction
Country-specific Forecast
```

---

# 30. Nguyên tắc cuối cùng của dự án

## Global First

```text
Hoàn thành thị trường quốc tế trước.
```

## Vietnam Later

```text
Vietnam = Optional Extension
```

## Occupation First

```text
Không forecast skill chung để recommendation.
```

Forecast:

```text
Occupation + Skill + Time
```

## Macro Analytics ≠ Recommendation

Toàn ngành dùng cho:

```text
Market Overview
```

Occupation dùng cho:

```text
Forecast
Career Guidance
Recommendation
```

## Past → Future

Không sử dụng random split trong trend forecasting.

## Recent Data Matters

Dữ liệu mới phải có ảnh hưởng cao hơn thông qua:

```text
Recency Weighting
```

---

# 31. Kiến trúc logic cuối cùng

```text
                   GLOBAL IT JOB MARKET
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
       Historical Data              Recent Data
             │                           │
             └─────────────┬─────────────┘
                           ▼
                     HDFS Bronze
                           │
                           ▼
                     Apache Spark
                           │
                    Cleaning / ETL
                           │
                           ▼
                     Silver Layer
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
        Market Analytics        Job Classification
                                       │
                                       ▼
                               Skill Extraction
                                       │
                                       ▼
                           Occupation-Skill-Time
                                       │
                                       ▼
                              Feature Engineering
                                       │
                     ┌─────────────────┼─────────────────┐
                     ▼                 ▼                 ▼
                Historical          Recent            Hybrid
                   Model             Model             Model
                     │                 │                 │
                     └─────────────────┼─────────────────┘
                                       ▼
                                Trend Prediction
                                       │
                                       ▼
                                   Gold Layer
                                       │
                                       ▼
                                    MongoDB
                                       │
                                       ▼
                              Streamlit Dashboard
                                       │
                           ┌───────────┴───────────┐
                           ▼                       ▼
                    Market Overview        Career Forecast
                                             │
                                             ▼
                                      Target Occupation
                                             │
                                             ▼
                                       Relevant Skills
                                             │
                                             ▼
                                  Growing / Stable / Declining
```

---

# 32. Kết luận

Dự án chính thức được định hình thành:

> **Một hệ thống Big Data phân tích thị trường tuyển dụng CNTT quốc tế và dự báo xu hướng nhu cầu kỹ năng theo từng nhóm nghề bằng cách kết hợp dữ liệu lịch sử với dữ liệu tuyển dụng mới.**

Trọng tâm nghiên cứu không còn là:

```text
Skill nào đang hot trong IT?
```

mà là:

```text
Đối với nghề X,
skill nào hiện đang quan trọng,
skill nào đang tăng,
skill nào đang giảm,
và xu hướng đó có thay đổi khi
bổ sung dữ liệu tuyển dụng mới hay không?
```

Đây là hướng triển khai chính thức cho MVP của dự án.
