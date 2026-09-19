# PLAN ĐỒ ÁN BIG DATA  
## Xây dựng hệ thống Big Data phân tích thị trường tuyển dụng và dự báo xu hướng nhu cầu kỹ năng CNTT

---

## 1. Tên đề tài

**Xây dựng hệ thống Big Data phân tích thị trường tuyển dụng và dự báo xu hướng nhu cầu kỹ năng CNTT từ dữ liệu lịch sử và dữ liệu tuyển dụng mới**

**Tên tiếng Anh đề xuất:**  
**A Big Data System for IT Job Market Analytics and Skill Demand Forecasting Using Historical and Near-Real-Time Recruitment Data**

---

## 2. Mục tiêu đề tài

Xây dựng hệ thống có khả năng:

1. Phân tích các vị trí CNTT đang có nhu cầu tuyển dụng cao.
2. Xác định các kỹ năng quan trọng đối với từng vị trí CNTT.
3. Phân tích sự thay đổi nhu cầu kỹ năng theo thời gian.
4. Phân loại xu hướng kỹ năng thành:
   - Growing
   - Stable
   - Declining
5. Kết hợp dữ liệu tuyển dụng lịch sử với dữ liệu tuyển dụng mới.
6. Xây dựng dashboard trực quan để hỗ trợ:
   - Sinh viên định hướng nghề nghiệp.
   - Người đi làm xác định kỹ năng cần bổ sung.
   - Doanh nghiệp và cơ sở đào tạo theo dõi xu hướng thị trường.

---

## 3. Câu hỏi nghiên cứu

### RQ1
Những kỹ năng CNTT nào đang được yêu cầu nhiều nhất trên thị trường tuyển dụng?

### RQ2
Yêu cầu kỹ năng khác nhau như thế nào giữa các vị trí CNTT?

### RQ3
Những kỹ năng nào đang có nhu cầu tăng, ổn định hoặc giảm?

### RQ4
Dữ liệu tuyển dụng mới có làm thay đổi xu hướng so với dữ liệu lịch sử hay không?

### RQ5
Có thể dự đoán xu hướng nhu cầu kỹ năng CNTT trong thời gian gần tiếp theo hay không?

---

## 4. Phạm vi đề tài

Chỉ tập trung vào một số nhóm nghề CNTT tiêu biểu:

- Data Analyst
- Data Scientist
- Data Engineer
- Software Engineer
- Backend Developer
- Frontend Developer
- DevOps Engineer
- Machine Learning Engineer

Một số nhóm kỹ năng chính:

### Programming
- Python
- Java
- JavaScript
- C++
- C#

### Database
- SQL
- MySQL
- PostgreSQL
- MongoDB

### Data / Big Data
- Pandas
- NumPy
- Spark
- Hadoop
- Kafka
- Hive

### BI
- Power BI
- Tableau
- Excel

### Cloud
- AWS
- Azure
- GCP

### DevOps
- Docker
- Kubernetes
- Jenkins
- Terraform

### AI / ML
- TensorFlow
- PyTorch
- Scikit-learn
- Generative AI
- LLM
- RAG

---

## 5. Nguồn dữ liệu

### 5.1. Historical Data

Sử dụng các bộ dữ liệu tuyển dụng công khai có quy mô lớn, ưu tiên dữ liệu có:

- `job_id`
- `title`
- `company`
- `location`
- `description`
- `experience_level`
- `salary`
- `posted_at`
- `skills`

Mục tiêu:

- Hàng trăm nghìn đến hơn 1 triệu tin tuyển dụng.
- Có dữ liệu từ năm 2024 và nếu có thể bổ sung năm 2025.

### 5.2. Fresh Data

Thu thập dữ liệu tuyển dụng mới trong năm 2026 thông qua:

1. API chính thức.
2. Dataset cập nhật.
3. Crawler nếu nguồn cho phép.

Ưu tiên:

```text
API / Open Dataset
        >
Crawler
```

### 5.3. Dữ liệu bổ sung

Có thể sử dụng thêm:

- Stack Overflow Developer Survey
- O*NET
- Các nguồn thống kê công nghệ khác

Các nguồn này dùng để đối chiếu xu hướng, không nhất thiết ghép trực tiếp với bảng Job Posting.

---

## 6. Kiến trúc hệ thống

```text
             HISTORICAL DATA
          Job Dataset 2024/2025
                  |
                  v
              +-------+
              | HDFS  |
              |Bronze |
              +---+---+
                  |
                  |
Fresh Job API 2026
                  |
                  v
        +--------------------+
        |   Apache Spark     |
        |--------------------|
        | Cleaning           |
        | Deduplication      |
        | Normalization      |
        | Skill Extraction   |
        | Job Classification |
        +---------+----------+
                  |
                  v
             Silver Layer
                  |
                  v
          Feature Engineering
                  |
          +-------+--------+
          |                |
          v                v
      Analytics       Spark MLlib
          |                |
          |         Trend Prediction
          |                |
          +-------+--------+
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

## 7. Kiến trúc dữ liệu Bronze - Silver - Gold

```text
/jobs/

├── bronze/
│   ├── historical/
│   └── fresh/
│
├── silver/
│   └── normalized_jobs/
│
└── gold/
    ├── skill_stats/
    ├── job_stats/
    └── predictions/
```

### Bronze

Lưu dữ liệu thô từ các nguồn.

### Silver

Dữ liệu đã:

- Làm sạch.
- Chuẩn hóa.
- Xóa duplicate.
- Chuẩn hóa job title.
- Chuẩn hóa skill.
- Chuẩn hóa location.
- Chuẩn hóa salary.

### Gold

Dữ liệu tổng hợp phục vụ:

- Analytics.
- Machine Learning.
- Dashboard.
- Prediction.

---

## 8. Unified Schema

Schema chuẩn đề xuất:

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

Nhằm phân biệt:

- Thời điểm tin được đăng.
- Thời điểm hệ thống thu thập dữ liệu.

---

## 9. Data Cleaning

Apache Spark được sử dụng để xử lý:

### Missing Values
- Thiếu salary.
- Thiếu location.
- Thiếu description.
- Thiếu experience.

### Duplicate Jobs

Có thể tạo `job_hash`:

```text
hash(
    normalized_title
    + company
    + location
    + normalized_description
)
```

Sau đó loại bỏ duplicate.

### Job Title Normalization

Ví dụ:

```text
Junior Data Analyst
Data Analyst I
BI Data Analyst
Data Analytics Specialist

        ↓

Data Analyst
```

### Skill Normalization

Ví dụ:

```text
JS
Javascript
JavaScript
JavaScript ES6

        ↓

JavaScript
```

```text
Postgres
PostgreSQL

        ↓

PostgreSQL
```

```text
Gen AI
GenAI
Generative AI

        ↓

Generative AI
```

---

## 10. Skill Extraction

Tạo `skills.json`:

```json
{
  "python": ["python"],
  "javascript": [
    "javascript",
    "js",
    "javascript es6"
  ],
  "postgresql": [
    "postgres",
    "postgresql"
  ],
  "generative_ai": [
    "genai",
    "gen ai",
    "generative ai"
  ]
}
```

Ví dụ mô tả tuyển dụng:

```text
Looking for a Data Engineer
with Python, SQL, Spark and AWS...
```

Hệ thống trích xuất:

```text
Python
SQL
Spark
AWS
```

Có thể tạo bảng:

| job_id | skill |
|---|---|
| 001 | Python |
| 001 | SQL |
| 001 | Spark |
| 001 | AWS |

---

## 11. Phân tích nhu cầu kỹ năng

Không chỉ đếm số lần skill xuất hiện.

Công thức:

```text
Demand Rate =
Jobs containing skill
----------------------
Total jobs
```

Ví dụ:

```text
Data Analyst

SQL       82%
Python    67%
Excel     62%
Power BI  49%
AWS       21%
```

Phân tích theo:

- Job
- Skill
- Time
- Country
- Experience Level
- Location

---

## 12. Machine Learning

### Mục tiêu chính

Phân loại xu hướng kỹ năng:

```text
Growing
Stable
Declining
```

### Feature đề xuất

```text
skill
month
job
demand_rate
growth_rate
previous_1
previous_2
previous_3
```

### Model đề xuất

- Logistic Regression
- Random Forest
- Gradient Boosted Trees

Triển khai bằng:

```text
Spark MLlib
```

---

## 13. Recency Weighting

Dữ liệu mới cần có trọng số cao hơn dữ liệu cũ.

Ví dụ:

```text
2024 jobs       weight 0.3
2025 jobs       weight 0.6
2026 Q1         weight 0.8
2026 Q3         weight 1.0
```

Có thể áp dụng:

```text
w = exp(-lambda * t)
```

Trong đó:

- `t`: tuổi dữ liệu.
- `lambda`: tốc độ giảm trọng số.

---

## 14. Experiment chính

So sánh ba phương án.

### Model A - Historical Only

```text
2024 - 2025
     ↓
 Prediction
```

### Model B - Recent Only

```text
2026
 ↓
Prediction
```

### Model C - Hybrid

```text
Historical
    +
Recent
    +
Recency Weighting
    ↓
Prediction
```

Bảng so sánh:

| Model | Accuracy | F1-score | MAE / Metric khác |
|---|---:|---:|---:|
| Historical | | | |
| Recent | | | |
| Hybrid | | | |

Mục tiêu:

> Kiểm tra liệu việc kết hợp dữ liệu lịch sử với dữ liệu mới có cải thiện khả năng dự đoán xu hướng kỹ năng hay không.

---

## 15. Time-based Split

Không dùng random split cho bài toán xu hướng.

Ví dụ:

```text
TRAIN
2024 ---------------- 2025
                        |
                        v

VALIDATION
2026 Q1 ----------- 2026 Q2
                        |
                        v

TEST
2026 Q3
```

Nguyên tắc:

```text
Past
 ↓
Future
```

Nhằm tránh Data Leakage.

---

# 16. Dashboard

Đề xuất sử dụng:

```text
Streamlit
```

## Page 1 - Market Overview

Hiển thị:

- Total Jobs
- Companies
- Locations
- Skills
- Jobs Over Time
- Top Occupations
- Experience Distribution

---

## Page 2 - Skill Analytics

Ví dụ:

```text
Job:
[ Data Analyst ▼ ]

SQL        82%
Python     67%
Power BI   49%
AWS        21%
```

---

## Page 3 - Job Comparison

Ví dụ:

```text
Data Analyst
      VS
Data Engineer
```

| Skill | Data Analyst | Data Engineer |
|---|---:|---:|
| SQL | 82% | 88% |
| Python | 67% | 79% |
| Power BI | 49% | 11% |
| Spark | 8% | 58% |
| AWS | 21% | 63% |

---

## Page 4 - Skill Trend

Ví dụ:

```text
Python

2024 ------ 2025 ------ 2026
43%          49%         61%

Trend:
Growing ↑
```

---

## Page 5 - Forecast

Ví dụ:

```text
Current Skill Demand

Python        61%
Spark         36%
Docker        41%
AWS           47%

Predicted Trend

Python        ↑
Spark         ↑
Docker        ↑↑
AWS           ↑
```

---

## 17. Phân công thành viên

| Thành viên A | Thành viên B |
|---|---|
| API / Data Collection | Data Analysis |
| HDFS | Feature Engineering |
| Spark ETL | Spark MLlib |
| Data Cleaning | Trend Model |
| MongoDB | Dashboard |
| Pipeline | Visualization |

Cả hai cùng thực hiện:

- Research
- Testing
- Report
- Slides
- Presentation

---

# 18. Kế hoạch 10 tuần

| Tuần | Công việc | Kết quả cần đạt |
|---|---|---|
| 1 | Chốt đề tài, câu hỏi nghiên cứu, phạm vi nghề CNTT; khảo sát dataset lịch sử và API dữ liệu mới | Proposal + danh sách nguồn dữ liệu |
| 2 | Tải dataset lịch sử; thử API; thiết kế schema chung | Dataset mẫu + Data Dictionary |
| 3 | Cài Hadoop/HDFS, Spark/PySpark; thiết kế Bronze/Silver/Gold; xây collector API | Pipeline thu thập dữ liệu chạy được |
| 4 | Spark Data Cleaning: missing, duplicate, salary, location, job title | Clean Dataset V1 |
| 5 | Xây Skill Dictionary; chuẩn hóa skill; trích xuất skill từ description | Skill Extraction Pipeline |
| 6 | EDA bằng Spark; xây baseline trend | Báo cáo Giai đoạn 1 |
| 7 | Feature Engineering + mô hình Growing/Stable/Declining | Baseline Model + Metrics |
| 8 | Cải thiện model; Historical vs Recent vs Hybrid; Recency Weighting | Model Comparison |
| 9 | MongoDB + Streamlit dashboard; tích hợp pipeline | Demo hoàn chỉnh |
| 10 | Kiểm thử, hoàn thiện báo cáo, slide, luyện thuyết trình | Source + Word + PPT + Demo |

---

# 19. MVP bắt buộc

Nếu thời gian bị giới hạn, cần đảm bảo hoàn thành:

```text
Historical Dataset

        +

Fresh Dataset

        ↓

HDFS

        ↓

Spark ETL

        ↓

Skill Extraction

        ↓

Skill Trend Analysis

        ↓

Spark ML Model

        ↓

Dashboard
```

Checklist:

- [ ] Historical Dataset
- [ ] Fresh Dataset
- [ ] HDFS Storage
- [ ] Spark ETL
- [ ] Data Cleaning
- [ ] Job Title Normalization
- [ ] Skill Normalization
- [ ] Skill Extraction
- [ ] Skill Trend Analysis
- [ ] Spark ML Model
- [ ] Dashboard
- [ ] Model Evaluation

---

# 20. Phần nâng cao

Chỉ thực hiện sau khi MVP đã hoàn chỉnh.

- Skill Gap Analysis
- Career Recommendation
- Salary Prediction
- FP-Growth Skill Combination
- Job Recommendation
- Kafka Streaming
- NLP Model
- Real-time Pipeline

> Kafka không phải thành phần bắt buộc trong MVP.

---

# 21. Rủi ro

| Rủi ro | Mức độ | Giải pháp |
|---|---|---|
| Không đủ dữ liệu 2025 | Cao | Tìm historical source bổ sung |
| API free ít dữ liệu | Trung bình | Kết hợp nhiều nguồn hợp lệ |
| Skill quá nhiều | Trung bình | Giới hạn 100-300 kỹ năng CNTT |
| Job title không đồng nhất | Trung bình | Mapping về 6-8 occupation |
| Schema giữa các nguồn khác nhau | Cao | Thiết kế Unified Schema |
| Dự báo không đủ tốt | Cao | Chuyển sang Growing/Stable/Declining |
| Spark phức tạp | Thấp | Ưu tiên PySpark DataFrame trước |
| Dashboard không hoàn thiện | Thấp | Làm Streamlit MVP từ sớm |
| Duplicate Job | Cao | Hash + Deduplication |
| Concept Drift | Cao | Fresh Data + Recency Weighting |

---

# 22. Tiêu chí GO / NO-GO

Trước khi chính thức triển khai, kiểm tra:

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

Nếu cả 4 đều **YES**:

```text
GO
```

Nếu không có dữ liệu thời gian phù hợp:

> Không nên sử dụng từ **dự báo xu hướng**.

Có thể đổi đề tài thành:

**Phân tích nhu cầu kỹ năng CNTT từ dữ liệu tuyển dụng quy mô lớn bằng Apache Spark**

---

# 23. Tiêu chí đánh giá tính khả thi

| Tiêu chí | Đánh giá |
|---|---:|
| Tính ứng dụng thực tế | 9/10 |
| Phù hợp Big Data | 9/10 |
| Khả năng tìm dữ liệu | 8/10 |
| Khả năng demo | 9/10 |
| Phù hợp nhóm 2 người | 8/10 |
| Độ khó | 7/10 |
| Khả năng mở rộng | 9/10 |
| Tổng thể | **8.5/10** |

---

# 24. Công nghệ dự kiến

```text
Python
PySpark
Apache Spark
Hadoop / HDFS
Spark MLlib
MongoDB
Streamlit
Git / GitHub
```

Có thể bổ sung:

```text
Kafka
Docker
Plotly
Pandas
Scikit-learn
```

nếu phù hợp với tiến độ.

---

# 25. Kết quả cuối cùng

Sản phẩm cuối cùng cần có:

```text
Big Data Job Dataset
        ↓
Data Processing Pipeline
        ↓
Normalized IT Job Dataset
        ↓
Skill Demand Analytics
        ↓
Trend Prediction
        ↓
Interactive Dashboard
```

Dashboard cần giúp người dùng trả lời:

1. Nghề CNTT nào đang tuyển nhiều?
2. Nghề đó cần kỹ năng gì?
3. Skill nào phổ biến nhất?
4. Skill nào đang tăng hoặc giảm?
5. Job nào cần một skill cụ thể?
6. Những kỹ năng nào được dự đoán sẽ tiếp tục tăng nhu cầu?

---

## Kết luận

Đề tài có tính khả thi cao nếu giải quyết được hai điều quan trọng nhất:

1. Có dữ liệu lịch sử đủ lớn và có timestamp.
2. Có nguồn dữ liệu tuyển dụng mới để cập nhật xu hướng năm 2026.

Hướng triển khai nên ưu tiên:

```text
Historical Data
      +
Fresh Data
      ↓
HDFS
      ↓
Apache Spark
      ↓
Skill Analytics
      ↓
Trend Prediction
      ↓
Dashboard
```

Trọng tâm nghiên cứu:

> **Đánh giá việc kết hợp dữ liệu tuyển dụng lịch sử với dữ liệu mới nhằm thích nghi với tốc độ thay đổi nhanh của nhu cầu kỹ năng CNTT.**
