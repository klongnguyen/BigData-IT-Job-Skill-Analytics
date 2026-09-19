# Unified Schema Specification (Updated - Global First): Big Data IT Job Skill Analytics

Tài liệu này xác lập đặc tả **Unified Schema** chuẩn cho hệ thống phân tích và dự báo kỹ năng CNTT theo tinh thần **Global First, Extensible for Vietnam**. Toàn bộ các nguồn dữ liệu đầu vào sau khi làm sạch sẽ được quy đổi về cấu trúc 17 trường chuẩn này trước khi lưu trữ vào Silver Layer và phục vụ Feature Engineering / MLlib.

---

## 1. Cấu trúc Unified Schema chuẩn (17 trường)

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
  "posted_at": "timestamp",
  "collected_at": "timestamp",
  "source": "string",
  "skills": ["string"]
}
```

Trong MVP hiện tại:
- `market = "GLOBAL"` cho toàn bộ bản ghi.
- Schema đã sẵn sàng để mở rộng sang `market = "VIETNAM"` sau này mà không cần thay đổi cấu trúc bảng hay luồng ETL.

---

## 2. Đặc tả kỹ thuật chi tiết từng trường

| STT | Tên trường | Kiểu dữ liệu PySpark | Kiểu dữ liệu SQL | Nullable | Mô tả tóm tắt |
|---|---|---|---|---|---|
| 1 | `job_id` | `StringType()` | `VARCHAR(128)` | **Không (PK)** | Khóa chính duy nhất đại diện cho tin tuyển dụng |
| 2 | `title` | `StringType()` | `VARCHAR(255)` | **Không** | Tiêu đề công việc gốc từ nhà tuyển dụng |
| 3 | `normalized_title` | `StringType()` | `VARCHAR(64)` | **Không** | Tên vị trí đã được chuẩn hóa về 8 nhóm nghề chính |
| 4 | `company` | `StringType()` | `VARCHAR(255)` | Có | Tên công ty đăng tuyển |
| 5 | `location` | `StringType()` | `VARCHAR(255)` | Có | Địa điểm làm việc nguyên bản (Thành phố, Bang hoặc Remote) |
| 6 | `city` | `StringType()` | `VARCHAR(128)` | Có | Thành phố cụ thể (nếu trích xuất được) |
| 7 | `country` | `StringType()` | `VARCHAR(64)` | Có | Quốc gia tuyển dụng (US, UK, Germany, Worldwide...) |
| 8 | `market` | `StringType()` | `VARCHAR(32)` | **Không** | Phân vùng thị trường: `"GLOBAL"` (MVP) hoặc `"VIETNAM"` (Future) |
| 9 | `work_mode` | `StringType()` | `VARCHAR(32)` | Có | Hình thức làm việc: `"Remote"`, `"Onsite"`, `"Hybrid"` |
| 10 | `description` | `StringType()` | `TEXT` | **Không** | Toàn văn mô tả công việc (đã strip HTML tags) |
| 11 | `experience_level` | `StringType()` | `VARCHAR(32)` | Có | Cấp bậc kinh nghiệm (Junior, Mid, Senior, Lead) |
| 12 | `salary_min` | `IntegerType()` | `INT` | Có | Mức lương tối thiểu quy đổi theo năm (USD) |
| 13 | `salary_max` | `IntegerType()` | `INT` | Có | Mức lương tối đa quy đổi theo năm (USD) |
| 14 | `posted_at` | `TimestampType()`| `TIMESTAMP` | **Không** | Thời điểm tin tuyển dụng được đăng (`YYYY-MM-DD HH:MM:SS`) |
| 15 | `collected_at` | `TimestampType()`| `TIMESTAMP` | **Không** | Thời điểm hệ thống thu thập tin (`YYYY-MM-DD HH:MM:SS`) |
| 16 | `source` | `StringType()` | `VARCHAR(64)` | **Không** | Nguồn gốc tin (`arbeitnow`, `remotive`, `kaggle`...) |
| 17 | `skills` | `ArrayType(StringType())` | `JSON / ARRAY` | **Không** | Mảng danh sách các kỹ năng chuẩn hóa trích xuất được |

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
    StructField("posted_at", TimestampType(), False),
    StructField("collected_at", TimestampType(), False),
    StructField("source", StringType(), False),
    StructField("skills", ArrayType(StringType()), False)
])
```
