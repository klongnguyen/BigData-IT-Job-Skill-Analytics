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

## Cổng chất lượng của bản kế hoạch

Chỉ dừng vòng review khi đạt **ít nhất 8/10** theo cùng một rubric ở bản trước và sau khi sửa, đồng thời không còn lỗi nghiêm trọng về nguồn dữ liệu, rò rỉ thời gian hoặc tuyên bố dự báo thiếu bằng chứng.

| Tiêu chí | Điểm tối đa | Bằng chứng cần có |
|---|---:|---|
| Câu hỏi nghiên cứu và phạm vi MVP | 2 | Nghề, thị trường, đầu ra và ngoài phạm vi rõ ràng |
| Nguồn dữ liệu, provenance, tính đại diện | 2 | File gốc, trường thực có, thời gian, quyền sử dụng và sai lệch nguồn được ghi đúng |
| Nhãn, feature, backtest và so sánh mô hình | 3 | Horizon/cutoff rõ, không rò rỉ, cùng tập test, baseline và điều kiện từ chối dự báo |
| Roadmap 10 tuần và deliverables | 2 | Việc ưu tiên, cổng quyết định, đầu ra demo và nhánh dự phòng khả thi |
| Tái lập, đo chất lượng và giới hạn | 1 | Test, mẫu số, phiên bản taxonomy, limitations và quyết định GO/NO-GO |

Điểm này chấm **chất lượng kế hoạch**, không phải độ chính xác của một mô hình chưa được huấn luyện. ChatGPT review độc lập chấm bản sửa đầu **8,5/10**; sau khi đồng bộ các mục 8, 16–21 và 26, review lại diff và chấm bản cuối **9,3/10**, không còn lỗi nghiêm trọng. Điểm này không thay thế việc nghiệm thu dữ liệu và mô hình khi triển khai.

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

**Trạng thái đã kiểm chứng trong repository (03/10/2026):** `data/raw/data_jobs.csv` là tập Luke Barousse khoảng 786 nghìn bản ghi; file hiện có `job_posted_date`, `job_title` và `job_skills`, nhưng **không có cột `job_description`**. Phần Silver hiện tạo từ 50.000 bản ghi lịch sử đầu tiên, phân vùng năm 2023. Không coi tập mẫu 300 dòng có ngày 2022–2025 là bằng chứng rằng file lịch sử đầy đủ nhiều năm. [Dataset gốc](https://huggingface.co/datasets/lukebarousse/data_jobs) cũng ghi khoảng 786 nghìn dòng và giấy phép Apache-2.0.


- Dùng `job_skills` lịch sử để phân tích kỹ năng được gắn nhãn sẵn; **không gọi đây là kết quả trích xuất từ JD**.
- Dùng dữ liệu có JD thật để đánh giá bộ trích xuất kỹ năng; nhãn `job_skills` của tập lịch sử không tự động là ground truth độc lập cho cùng văn bản.
- Kiểm kê lại toàn bộ file lịch sử theo năm × nghề × quốc gia × nguồn trước khi thiết kế thí nghiệm. Phần dự báo chỉ được mở khi có đủ các mốc thời gian liên tiếp và số quan sát theo từng ô.
- Nếu tìm thêm nguồn lịch sử có JD và nhiều năm, lưu URL, giấy phép, phạm vi nghề, cách thu thập và ngày tải; chạy lại profiling trước khi nhập vào Silver.

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
- Kiểm tra thay đổi phân bố trong cùng nguồn/nghề trước khi gọi là Concept Drift.
- Đánh giá Recent Trend.
- Thực hiện Hybrid Forecast **nếu đạt cửa kiểm định dữ liệu ở mục 21 và 28**.
- Áp dụng Recency Weighting như một giả thuyết cần kiểm chứng, không mặc định tốt hơn.

**Mẫu hiện có:** 267 tin từ Arbeitnow và Remotive, chủ yếu trong khoảng 08–09/2026. Đây là bằng chứng collector hoạt động, chưa đủ để khẳng định dữ liệu mới đại diện cho 8 nghề hoặc huấn luyện mô hình theo tháng. Hai nguồn thiên về việc làm châu Âu/remote; biểu đồ số tin phản ánh **mẫu thu thập**, không phải tổng nhu cầu tuyển dụng thế giới.

Collector phải ghi số bản ghi theo nguồn × ngày × nghề, độ trễ đăng/thu thập, tỷ lệ thiếu trường và tỷ lệ trùng. Dashboard hiển thị nguồn, thời gian cập nhật và phạm vi mẫu. [Remotive yêu cầu dẫn nguồn, liên kết lại tin gốc và cho biết API public trễ 24 giờ](https://remotive.com/remote-jobs/api); [Arbeitnow cung cấp API theo trạng thái “as available” và yêu cầu liên kết lại](https://www.arbeitnow.com/terms). Kiểm tra điều khoản trước khi hiển thị lại tin hoặc công bố dữ liệu.

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

Schema Silver 18 trường ở `docs/data/unified_schema.md` là hợp đồng kỹ thuật hiện tại, nhưng các nguồn không có cùng mức thông tin. Archive lịch sử không có JD, vì vậy `description=null` và `description_origin=missing`; tuyệt đối không dựng description/JD từ title hoặc `job_skills`. **Quyết định cho MVP:** giữ 18 trường Silver và tạo bảng `job_provenance` riêng, nối **1:1 bằng `job_id` ổn định**, gồm `source`, `source_record_id`, `source_url` (nếu có), `description_origin` (`original_jd`/`missing`), `skills_origin` (`source_tags`/`extracted_from_jd`/`missing`), `taxonomy_version`, `ingestion_id`, `collected_at` và checksum bản ghi raw. Lưu bảng này cùng bản phát hành Silver; kiểm tra không thiếu/không trùng khóa trước khi tạo Gold hoặc ML.

Tạo `job_id = sha256(source | source_record_id)`. Nếu nguồn có ID bền vững thì dùng làm `source_record_id`; nếu không có (như archive lịch sử hiện tại), dùng checksum xác định của bản ghi nguồn làm `source_record_id`, không tự suy ra ID từ trường mô tả nghề nghiệp. `job_hash` chuẩn hóa company/title/location/posted date để **deduplicate bản ghi trùng chính xác theo quy tắc hiện hành**; đây là khóa khác với `job_id` để **truy vết bản ghi nguồn**. Không dùng ID phụ thuộc thứ tự xử lý như `monotonically_increasing_id()` làm khóa bền vững. Không điền ngày đăng hoặc quốc gia giả khi thiếu; chuyển bản ghi lỗi sang quarantine để kiểm tra.

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

Quy trình phải tách hai nguồn nhãn:

- Historical Luke Barousse: chuẩn hóa `job_skills` đã có với `skills_origin=source_tags`; `description=null` và `description_origin=missing` vì archive không có JD. Không dựng text từ title + tags rồi gọi đó là description/JD.
- Fresh có JD thật: trích xuất từ JD, đối soát với tags như tín hiệu phụ; gán nhãn thủ công một mẫu phân tầng theo nghề/nguồn để đo precision, recall và lỗi phủ định/ngữ cảnh.

Mọi bản ghi job-skill nối tới `job_provenance` qua `job_id` để lấy `skills_origin` và `taxonomy_version`; không trộn nhãn lịch sử với kết quả trích xuất từ JD như cùng một phép đo.

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

Mọi tỷ lệ trên dashboard phải ghi `n` ở mẫu số, nguồn, kỳ thời gian và chính sách dedup. Chỉ so sánh tăng/giảm giữa các kỳ khi phạm vi nguồn và nghề tương đương; tỷ lệ của mẫu thu thập không thể được diễn giải là tỷ lệ của toàn bộ thị trường thế giới.

---

# 15. Hai tầng Analytics

## Layer 1 – Macro Market Analytics

Phân tích trên tập tin tuyển dụng đã thu thập:

```text
Total Jobs
Top Occupations
Top Skills
Job Growth
Country Distribution
Experience Distribution
```

Mục tiêu:

> Cho biết phân bố trong các nguồn tuyển dụng quốc tế đang theo dõi thay đổi như thế nào; chỉ khái quát ra toàn thị trường khi thiết kế lấy mẫu cho phép.

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

Một dòng học máy là cặp `(occupation, skill)` tại **cuối tháng t**. Chỉ dùng tin có `posted_at` hợp lệ và `posted_at <= cutoff t` để tạo feature. Có hai chế độ thời gian, phải ghi rõ trong kết quả:

- **Retrospective archive backtest:** file lịch sử được tải sau năm 2023 vẫn dùng được để nghiên cứu diễn biến theo `posted_at`. `collected_at` ở đây là lúc nhập archive vào hệ thống, **không phải điều kiện `<= cutoff t`**; kết quả không được mô tả là mô phỏng những gì hệ thống thực sự đã biết vào năm 2023.
- **Prospective/live simulation:** với dữ liệu API thu thập định kỳ, cả `posted_at <= cutoff t` và `collected_at <= cutoff t` (cộng chính sách độ trễ được ghi trước) mới là thông tin có sẵn tại thời điểm dự báo. Tin đến muộn được ghi riêng, không lén thêm vào feature của cutoff cũ.

Dataset cho ML:

```text
occupation
skill
cutoff_month = t
rate_t, rate_t-1, rate_t-2, rate_t-3
job_count_t và số job chứa skill ở t
rolling_mean_3m, rolling_slope_3m (chỉ tới t)
source_mix_t, country_mix_t để kiểm soát sai lệch mẫu
label_t+1 (chỉ tạo khi tháng t+1 đã quan sát đủ)
```

Tính `demand_rate` bằng **số tin duy nhất** có skill / **số tin duy nhất** của occupation trong cùng tháng và cùng phạm vi nguồn. Không lấy `growth_rate` hoặc `demand_rate` của tháng tương lai làm feature. Ghi chế độ thời gian, phiên bản taxonomy, bộ lọc, nguồn và thời điểm chốt dữ liệu để tái lập kết quả.

---

# 17. Forecast Target

Horizon MVP: **tháng kế tiếp**. Với `p_t = demand_rate(o, s, t)`, đặt `Δ = p_(t+1) − p_t`, đơn vị **điểm phần trăm**, không phải tăng trưởng tương đối. Dải ±5 điểm phần trăm là **ngưỡng ý nghĩa nghiệp vụ đặt trước khi train**, không chọn để tối đa hóa điểm mô hình trên validation:

```text
Δ > +0,05  → Growing
−0,05 ≤ Δ ≤ +0,05 → Stable
Δ < −0,05 → Declining
```

Đây là **nhãn biến động tỷ lệ trong mẫu tin đăng**, không phải số việc làm tuyệt đối trên toàn thế giới. Chỉ gán nhãn nếu cả hai tháng có đủ mẫu theo cổng dữ liệu ở mục 21. Trước khi train, tính khoảng tin cậy 95% cho `Δ` bằng bootstrap trên tin duy nhất, phân tầng theo nguồn khi có đủ mẫu (chốt cách lấy mẫu trong báo cáo profiling):

- `Growing` khi **cận dưới > +0,05**; `Declining` khi **cận trên < −0,05**.
- `Stable` khi **toàn bộ khoảng tin cậy nằm trong [−0,05; +0,05]**.
- Các trường hợp còn lại: `Insufficient evidence`, loại khỏi tập nhãn train/test và báo tỷ lệ bị loại theo nghề, skill, tháng. Kiểm tra độ nhạy với dải ±3/±7 điểm phần trăm, không đổi ngưỡng chỉ để làm đẹp điểm model.

Tại thời điểm dự báo thật chưa có `p_(t+1)`: chỉ từ chối xuất nhãn theo cỡ mẫu ở `t`, chất lượng nguồn và độ tin cậy mô hình đã hiệu chỉnh trên validation; **không dùng khoảng tin cậy của tương lai** để quyết định có xuất dự báo hay không. Mỗi kết quả đi kèm kỳ dự báo, số tin, nguồn và mức tin cậy.

---

# 18. Machine Learning Strategy

Ưu tiên sau khi vượt cổng dữ liệu:

```text
One Global Model
+
Occupation as Feature
```

thay vì xây 8 model riêng ngay từ đầu. Tám nghề vẫn được phân tích mô tả, nhưng mô hình chỉ xuất dự báo cho nghề/kỹ năng đủ dữ liệu. Kiểm tra riêng hiệu năng từng nghề và dừng dự báo ở nhóm kém ổn định.

Input:

```text
occupation
skill
cutoff_month
rate_t và các lag tới t
job_count_t, rolling_mean_3m, rolling_slope_3m
source_mix_t, country_mix_t (nếu đủ dữ liệu)
```

`recency_weight` là **sample weight lúc train**, không nằm trong vector feature.

Output:

```text
Growing
Stable
Declining
```

Baseline bắt buộc: dự báo `Stable` và ngoại suy xu hướng gần nhất. Model đầu tiên: Logistic Regression đa lớp trong Spark MLlib; Random Forest chỉ thử nếu baseline đã ổn định. `GBTClassifier` của Spark chỉ hỗ trợ nhãn nhị phân, nên không dùng trực tiếp cho bài toán ba lớp ([tài liệu Spark](https://spark.apache.org/docs/4.2.0/api/python/reference/api/pyspark.ml.classification.GBTClassifier.html)).

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

Thêm **Model D – Hybrid không trọng số** để tách tác dụng của việc thêm dữ liệu mới khỏi tác dụng của Recency Weighting. Chỉ so sánh A/B/C/D trên **cùng tập test tương lai**, cùng occupation-skill đủ điều kiện và cùng phiên bản taxonomy. Nếu một nhánh không đủ dữ liệu huấn luyện, ghi `không khả thi` cùng lý do; không tạo chỉ số giả.

| Model | Dữ liệu train | Macro-F1 | Balanced accuracy | F1 từng lớp | Số cặp được dự báo |
|---|---|---:|---:|---|---:|
| A – Historical | Chỉ kỳ lịch sử hợp lệ | | | | |
| B – Recent | Chỉ kỳ mới trước cutoff | | | | |
| C – Hybrid có trọng số | Lịch sử + mới | | | | |
| D – Hybrid không trọng số | Lịch sử + mới | | | | |

Báo thêm confusion matrix, khoảng tin cậy bằng bootstrap theo tháng hoặc nguồn khi đủ mẫu, và hiệu năng theo nghề. Một cải thiện chỉ được nhận khi hơn baseline trên test tương lai và không làm giảm nghiêm trọng hiệu năng của nhóm nghề trọng tâm. Tham số mô hình và lựa chọn feature được chốt trên validation, **không chỉnh theo test**; dải nhãn ±5 điểm phần trăm đã đặt trước khi train (mục 17), chỉ báo phân tích độ nhạy với dải khác.

Research Objective:

> Xác định liệu Historical + Recent + Recency Weighting có cải thiện khả năng dự báo xu hướng kỹ năng theo occupation hay không.

---

# 20. Recency Weighting

Dùng trọng số ở bước train; `recency_weight` **không nằm trong vector feature**. Công thức ứng viên:

```text
weight = exp(-lambda × age)
```

`age` đo bằng tháng từ ngày đăng tới **cutoff của từng lần train**, không tính từ ngày chạy thí nghiệm. Thử vài giá trị half-life trên validation; so với Model D để biết trọng số có giúp hay không. Không áp dụng trọng số cho test hoặc tạo lợi thế do khác số lượng nguồn.

---

# 21. Time-Based Split

Không dùng Random Split. Dùng **rolling-origin backtest**: tại cutoff `t`, tạo feature từ các tin có `posted_at <= t`, dự báo `t+1`, rồi so với tháng `t+1` khi đã hoàn tất. Với live simulation còn lọc `collected_at <= t`; với archive hồi cứu giữ `collected_at` để truy vết nhưng không dùng nó làm bộ lọc hồi tố (mục 16). Tách train → validation → test theo thứ tự thời gian; để hở một tháng (horizon) tại ranh giới nếu hàng train sẽ dùng nhãn thuộc kỳ sau. Cố định tập test trước khi chọn mô hình.

**Cổng dữ liệu trước ML:**

1. Kiểm kê số tin theo nguồn × nghề × tháng sau khử trùng và xác nhận tháng thực tế có dữ liệu. Không suy ra chuỗi nhiều năm từ 300 dòng mẫu. Bảng Silver hiện chỉ có phân vùng `year=2023` và `year=2026`; khoảng trống 2024–2025 phải được lấp bằng nguồn được phép dùng hoặc coi là khoảng trống.
2. Mỗi nghề-tháng dùng để tính nhãn cần tối thiểu **30 tin duy nhất**, ít nhất **12 tháng liên tiếp có thể so sánh** cho mỗi nghề thử nghiệm khi dùng ba lag và horizon một tháng, và ít nhất **3 mốc cutoff có nhãn** để kiểm tra ngoài mẫu. Các ngưỡng này là cổng MVP thực dụng, phải báo độ nhạy khi thay đổi ngưỡng; riêng nhãn của kỹ năng hiếm còn phải vượt kiểm tra độ bất định. Không ngưỡng nào tự bảo đảm sức mạnh thống kê.
3. Nếu đổi nguồn giữa các năm, phải đánh giá riêng từng nguồn hoặc chuẩn hóa cơ cấu nguồn trước khi kết luận có drift. Không so sánh số lượng tin tuyệt đối giữa hai API có phạm vi thu thập khác nhau.
4. Khi chưa đủ điều kiện, chỉ công bố **analytics và observed trend** kèm cỡ mẫu; forecast hiển thị `Insufficient evidence`. Báo cáo rõ kết quả `NO-GO for predictive claims`, không dùng dữ liệu tương lai để lấp giả.

---

# 22. Dashboard

## Page 1 – Global IT Market Overview

Hiển thị trên **các nguồn đã thu thập**, kèm nguồn và kỳ cập nhật:

```text
Observed Job Postings
Companies
Countries
Top Occupations
Top Skills
Jobs Over Time
Experience Distribution
```

Chỉ hiển thị quốc gia nếu xác định được từ địa điểm gốc; `Worldwide/Remote` là phạm vi ứng tuyển, không phải quốc gia. Số tin qua thời gian cần ghi chú khi phạm vi nguồn thay đổi.

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

Đây là **mockup**, không phải kết quả đã tính. Trang thực tế phải hiện `Insufficient evidence` nếu cổng dữ liệu không đạt, cùng số tin, nguồn, tháng quan sát cuối và kỳ dự báo. Không hiển thị nhãn Growing/Stable/Declining cho ô chưa đủ bằng chứng.

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

Ở MVP, phần này chỉ xếp hạng kỹ năng **đã quan sát trong mẫu** theo nghề và độ phủ. Chỉ gắn nhãn “dự báo” nếu mô hình qua kiểm định ở mục 19–21; không đưa lời khuyên nghề nghiệp cá nhân hóa hoặc khẳng định toàn thị trường từ mẫu API thiên lệch.

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

**Đối chiếu triển khai ngày 03/10/2026:** Phase 1 có tài liệu và bài kiểm tra trên 567 dòng mẫu; Phase 2 đã có collector, Bronze JSON và Spark ETL ra Silver Parquet cho 50.087 bản ghi theo `docs/planning/phase_01_02_summary.md`. Đây là **pipeline file cục bộ**; chưa thấy bằng chứng HDFS đang chạy hoặc đường đọc/ghi HDFS end-to-end trong repository. `docs/planning/PHASE_03_Feature_Engineering_Spark_MLlib.md` là kế hoạch, chưa phải model đã huấn luyện. Các kết quả ở mẫu nhỏ không chứng minh đủ dữ liệu dự báo theo 8 nghề.

## Phase 1 – Data Feasibility

Trạng thái:

```text
IMPLEMENTED / QUALITY GATE REOPENED
```

Đã có tài liệu, bộ mẫu và script kiểm tra collector/schema. **Quyết định GO cũ chỉ xác nhận khả năng dựng pipeline thử nghiệm**, không xác nhận có JD lịch sử thật hoặc chuỗi 2022–2026 đủ điều kiện dự báo. Mẫu lịch sử 300 dòng và phép tổng hợp 567 dòng không được dùng làm bằng chứng về toàn bộ archive. Tuần 3 phải kiểm kê lại nguồn gốc và thời gian của file gốc; chỉ đóng lại Phase 1 sau khi cập nhật báo cáo feasibility.

Hạng mục cần nghiệm thu lại:

```text
Project Scope
Research Questions
Historical Data Validation trên file gốc, không trên mẫu tạo sẵn
Fresh Data Validation theo nguồn/nghề/tháng
Unified Schema
GO / NO-GO riêng cho analytics và predictive claims
```

## Phase 2 – Data Ingestion & Big Data Storage

Mục tiêu còn cần nghiệm thu:

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

Trạng thái: collector và Spark ETL chạy trên đường local đã được báo cáo hoàn thành; HDFS, job định kỳ, độ ổn định nguồn và kiểm tra dữ liệu nhiều tháng **chưa được xác nhận**. Chỉ đánh dấu M2 hoàn tất sau khi có log đọc/ghi HDFS và thống kê đầu vào/đầu ra tái lập được.

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

Đã có bản ETL đầu tiên. Việc còn lại: kiểm tra `posted_at` null/không hợp lệ thay vì gán ngầm năm-tháng 2026; kiểm chứng `country`, `job_id` xác định và quy tắc dedup; xuất `job_provenance` nối 1:1 với Silver theo mục 8; tách nhãn kỹ năng lịch sử có sẵn khỏi kỹ năng trích xuất từ JD mới. Test phải chứng minh ID ổn định qua lần chạy lại, khóa provenance không mồ côi và dữ liệu lỗi được quarantine theo từng nguồn. Đây là cổng trước Gold/ML.

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

Chỉ đo precision/recall trên mẫu JD thật được gán nhãn thủ công theo nghề và nguồn; báo tỷ lệ phủ riêng với độ chính xác. Không coi số skills/JD hoặc coverage là bằng chứng extraction chính xác.

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

Chỉ thực hiện sau cổng mục 21. Xây một dòng cho `(occupation, skill, cutoff_month=t)` theo mục 16:

```text
occupation
skill
cutoff_month=t
rate_t, rate_t-1, rate_t-2, rate_t-3
job_count_t, skill_job_count_t
rolling_mean_3m, rolling_slope_3m
source_mix_t, country_mix_t nếu đủ dữ liệu
label_t+1 chỉ sau khi quan sát tháng t+1 và vượt kiểm tra độ bất định
```

Lưu riêng `recency_weight` làm **sample weight của train**, không đưa vào vector feature. Kiểm tra mọi feature có `posted_at <= t`; với thí nghiệm live còn yêu cầu `collected_at <= t`. Báo số hàng bị loại vì thiếu tháng hoặc nhãn mơ hồ.

Milestone:

```text
M6 – ML Dataset Ready (chỉ khi qua cổng dữ liệu)
```

## Phase 7 – Trend Prediction

So sánh trên cùng tập test tương lai bằng rolling-origin backtest:

```text
Baseline Stable và baseline ngoại suy xu hướng
Model A – Historical Only
Model B – Recent Only
Model C – Hybrid + Recency Weighting
Model D – Hybrid không trọng số
```

Đánh giá:

```text
Macro-F1 và Balanced accuracy
F1 từng lớp và confusion matrix
Số cặp đủ điều kiện / tỷ lệ abstain theo nghề
Độ ổn định qua các cutoff
```

Chỉ huấn luyện và phát hành dự báo nếu cổng mục 21 đạt. Nhánh không đủ dữ liệu được ghi `không khả thi`, không điền điểm giả. Nếu toàn bộ là NO-GO, nghiệm thu bằng phân tích xu hướng quan sát được, báo cáo thiếu dữ liệu và kế hoạch thu thập tiếp; không công bố nhãn dự báo thiếu căn cứ.

Milestone:

```text
M7 – Forecast Model Ready hoặc NO-GO có bằng chứng
```

## Phase 8 – Gold Layer & MongoDB

Tạo:

```text
occupation_stats
skill_stats
skill_trends
predictions (chỉ khi qua cổng dự báo)
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

| Tuần | Ưu tiên và đầu ra có thể nghiệm thu | Quyết định |
|---|---|---|
| 1–2 | Feasibility, bộ mẫu, collector, Bronze/Silver local và test khởi đầu (đã báo cáo; cần đối chiếu chất lượng) | Chưa xem 567 dòng mẫu là dữ liệu train đủ |
| 3 | Audit toàn bộ dữ liệu theo nguồn/nghề/tháng, quyền sử dụng, JD thật, timestamp, nhãn kỹ năng; tìm nguồn bổ sung nhiều tháng. Lập bản kiểm toán nguồn có URL, ngày truy cập, giấy phép/điều khoản, phạm vi cho phép; cập nhật `docs/data/historical_data_evaluation.md` và báo cáo GO/NO-GO để thay các khẳng định cũ sai về JD và số năm | Chốt cổng nguồn dữ liệu và phạm vi nghề; Final Plan này là chuẩn quyết định tới khi tài liệu cũ được sửa |
| 4 | Ổn định ETL, test schema/dedup/timestamp; chứng minh một đường HDFS → Spark → Silver | M2/M3 hoặc ghi rõ hạng mục chưa đạt |
| 5 | Gán nhãn mẫu JD thật, đo extraction; bảng nghề–skill–tháng có cỡ mẫu và nguồn | M4/M5; loại ô quá ít dữ liệu |
| 6 | Hoàn thành analytics, dashboard bản đầu và baseline xu hướng quan sát | Chốt cổng `GO/NO-GO for forecasting` theo mục 21 |
| 7 | Nếu GO: feature/label không rò rỉ và rolling backtest; nếu NO-GO: phân tích sai lệch nguồn và độ bất định | Không ép 3 mô hình khi thiếu dữ liệu |
| 8 | Nếu GO: A/B/C/D trên cùng test, ablation trọng số; nếu NO-GO: báo cáo giới hạn và phương án thu thập | Chỉ công bố cải thiện có bằng chứng |
| 9 | Gold và Streamlit; MongoDB chỉ cho bảng serving cần truy vấn, có đường đọc Parquet dự phòng | Demo end-to-end với số liệu nguồn |
| 10 | Test, kiểm tra tái lập, báo cáo, slide và demo; đóng các lỗi ưu tiên cao | Bàn giao cùng limitations và quyết định GO/NO-GO |

---

# 28. MVP bắt buộc

**MVP bảo đảm trong 10 tuần:** dữ liệu lịch sử và mới có nguồn rõ ràng → Bronze → Spark Silver đã kiểm định → bảng tỷ lệ kỹ năng theo nghề/tháng có số mẫu → Gold → dashboard và báo cáo giới hạn. HDFS cần một đường end-to-end nếu là tiêu chí môn học; MongoDB là lớp serving tối thiểu, dashboard vẫn có thể đọc Gold Parquet khi MongoDB chưa sẵn sàng. Phân tích 8 nghề khi có dữ liệu, nhưng không buộc mọi nghề đều có forecast.

**MVP dự báo có điều kiện:** chỉ thêm feature/label tương lai, A/B/C/D, recency weighting và trang forecast sau khi vượt cổng mục 21. Nếu `NO-GO`, dashboard ghi `Insufficient evidence`, hiển thị xu hướng **đã quan sát** và phương án thu thập tiếp. Đây là kết quả nghiên cứu hợp lệ, không thay bằng nhãn dự báo mô phỏng.

Checklist trạng thái (đã có code ≠ đã nghiệm thu chất lượng):

- [x] Tài liệu Phase 1 và bài kiểm tra trên mẫu 567 dòng.
- [x] Mã ingestion lịch sử/mới, Bronze JSON và Spark Silver Parquet local đã được báo cáo chạy.
- [ ] Audit số liệu thực tế, phạm vi nguồn và giấy phép; sửa các khẳng định không khớp file gốc.
- [ ] Kiểm thử dữ liệu nguồn, JD/skill provenance, ngày hợp lệ, ID/dedup và phân bố tháng-nghề.
- [ ] Chứng minh HDFS end-to-end nếu bắt buộc trong môn học.
- [ ] Analytics nghề–skill–tháng với cỡ mẫu, confidence và giới hạn đại diện.
- [ ] Gold + dashboard demo; MongoDB serving tối thiểu khi cần.
- [ ] GO/NO-GO dự báo theo từng nghề/kỹ năng; chỉ train, test và công bố model khi đủ dữ liệu.
- [ ] Báo cáo, khả năng tái lập và demo cuối.

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

Dữ liệu mới là một giả thuyết có thể cải thiện dự báo; kiểm tra trên cùng tập test và so với phương án không trọng số:

```text
Recency Weighting
```

---

# 31. Kiến trúc logic cuối cùng

Sơ đồ dưới đây là **đích thiết kế**. Nhánh mô hình và Career Forecast chỉ kích hoạt khi dữ liệu vượt cổng mục 21; nếu không, Gold/Dashboard phục vụ analytics đã quan sát và báo thiếu bằng chứng. HDFS/MongoDB trong sơ đồ không có nghĩa đã hoàn tất triển khai.

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

Đây là hướng nghiên cứu và đích thiết kế. MVP luôn bàn giao pipeline phân tích có thể kiểm chứng; phần **dự báo** chỉ được công bố sau khi dữ liệu và backtest đạt các cổng đã định. Nếu không đủ dữ liệu, kết luận nghiên cứu là `NO-GO for predictive claims` và ghi rõ cần bổ sung dữ liệu gì.
