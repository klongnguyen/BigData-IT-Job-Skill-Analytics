# Unified Schema Specification (Final - 18 Fields): Big Data IT Job Skill Analytics

Tài liệu này xác lập đặc tả **Unified Schema chuẩn (18 trường)** cho hệ thống phân tích và dự báo kỹ năng CNTT theo tinh thần của [FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md). Toàn bộ dữ liệu đầu vào sau khi thu thập (Bronze) và làm sạch sẽ được quy đổi về cấu trúc chuẩn này để lưu trữ vào Silver Layer (định dạng Parquet) phục vụ Spark ETL, Analytics và Spark MLlib.

---

## 1. Cấu trúc Unified Schema chuẩn (18 trường)

```json
{
  "job_id": "string",
  "title": "string",
  "normalized_title": "string",
  "company": "string",
  "location": "string",
  "city": "string",
  "country": "string",
  "market": "string",
  "work_mode": "string",
  "description": "string",
  "experience_level": "string",
  "salary_min": "integer",
  "salary_max": "integer",
  "currency": "string",
  "posted_at": "timestamp",
  "collected_at": "timestamp",
  "source": "string",
  "skills": ["string"]
}
```

### Nguyên tắc thị trường (Market Dimension):
- Trong MVP: `market = "GLOBAL"` cho toàn bộ bản ghi.
- Kiến trúc lưu trữ và schema sẵn sàng hỗ trợ `market = "VIETNAM"` sau này mà không cần thay đổi cấu trúc bảng.

---

## 2. Đặc tả kỹ thuật chi tiết 18 trường

| STT | Tên trường | Kiểu dữ liệu PySpark | Kiểu dữ liệu SQL | Nullable | Mô tả tóm tắt |
|---|---|---|---|---|---|
| 1 | `job_id` | `StringType()` | `VARCHAR(128)` | **Không (PK)** | Khóa chính duy nhất đại diện cho tin tuyển dụng |
| 2 | `title` | `StringType()` | `VARCHAR(255)` | **Không** | Tiêu đề công việc gốc từ nhà tuyển dụng |
| 3 | `normalized_title` | `StringType()` | `VARCHAR(64)` | **Không** | Tên vị trí đã chuẩn hóa về 8 nhóm nghề chính |
| 4 | `company` | `StringType()` | `VARCHAR(255)` | Có | Tên công ty đăng tuyển |
| 5 | `location` | `StringType()` | `VARCHAR(255)` | Có | Địa điểm làm việc nguyên bản (Thành phố, Bang hoặc Remote) |
| 6 | `city` | `StringType()` | `VARCHAR(128)` | Có | Tên thành phố cụ thể (nếu trích xuất được) |
| 7 | `country` | `StringType()` | `VARCHAR(64)` | Có | Quốc gia tuyển dụng (United States, UK, Germany, Worldwide...) |
| 8 | `market` | `StringType()` | `VARCHAR(32)` | **Không** | Phân vùng thị trường: `"GLOBAL"` (MVP) hoặc `"VIETNAM"` (Future) |
| 9 | `work_mode` | `StringType()` | `VARCHAR(32)` | Có | Hình thức làm việc: `"Remote"`, `"Onsite"`, `"Hybrid"` |
| 10 | `description` | `StringType()` | `TEXT` | **Không** | Toàn văn mô tả công việc (đã strip HTML tags) |
| 11 | `experience_level` | `StringType()` | `VARCHAR(32)` | Có | Cấp bậc kinh nghiệm (Junior, Mid, Senior, Lead, Unknown) |
| 12 | `salary_min` | `IntegerType()` | `INT` | Có | Mức lương tối thiểu quy đổi theo năm |
| 13 | `salary_max` | `IntegerType()` | `INT` | Có | Mức lương tối đa quy đổi theo năm |
| 14 | `currency` | `StringType()` | `VARCHAR(16)` | Có | Đơn vị tiền tệ (mặc định `"USD"`) |
| 15 | `posted_at` | `TimestampType()`| `TIMESTAMP` | **Không** | Thời điểm đăng tin (`YYYY-MM-DD HH:MM:SS` UTC) |
| 16 | `collected_at` | `TimestampType()`| `TIMESTAMP` | **Không** | Thời điểm hệ thống thu thập tin (`YYYY-MM-DD HH:MM:SS` UTC) |
| 17 | `source` | `StringType()` | `VARCHAR(64)` | **Không** | Nguồn gốc tin (`arbeitnow`, `remotive`, `kaggle_historical`...) |
| 18 | `skills` | `ArrayType(StringType())` | `JSON / ARRAY` | **Không** | Mảng danh sách các kỹ năng chuẩn hóa trích xuất được |

---

## 3. Định nghĩa Schema trong PySpark

```python
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    TimestampType, ArrayType
)

unified_job_schema = StructType([
    StructField("job_id", StringType(), False),
    StructField("title", StringType(), False),
    StructField("normalized_title", StringType(), False),
    StructField("company", StringType(), True),
    StructField("location", StringType(), True),
    StructField("city", StringType(), True),
    StructField("country", StringType(), True),
    StructField("market", StringType(), False),
    StructField("work_mode", StringType(), True),
    StructField("description", StringType(), False),
    StructField("experience_level", StringType(), True),
    StructField("salary_min", IntegerType(), True),
    StructField("salary_max", IntegerType(), True),
    StructField("currency", StringType(), True),
    StructField("posted_at", TimestampType(), False),
    StructField("collected_at", TimestampType(), False),
    StructField("source", StringType(), False),
    StructField("skills", ArrayType(StringType()), False)
])
```
