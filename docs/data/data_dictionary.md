# Data Dictionary (Updated - 17 Fields): Big Data IT Job Skill Analytics

Tài liệu này cung cấp từ điển dữ liệu (Data Dictionary) chi tiết cho từng trường trong **Unified Schema (17 trường)** theo kiến trúc **Global First, Extensible for Vietnam**.

---

## 1. Chi tiết 17 trường trong Unified Schema

### 1. `job_id`
- **Tên trường**: Job Identifier
- **Kiểu dữ liệu**: `string` (VARCHAR 128)
- **Bắt buộc**: `NOT NULL` (Primary Key)
- **Mô tả**: Chuỗi định danh duy nhất cho từng tin tuyển dụng.
- **Ví dụ**: `"arbeitnow_senior-dev-123"`, `"remotive_1928374"`, `"hist_0042"`

### 2. `title`
- **Tên trường**: Job Title (Original)
- **Kiểu dữ liệu**: `string` (VARCHAR 255)
- **Bắt buộc**: `NOT NULL`
- **Mô tả**: Tiêu đề công việc gốc từ nhà tuyển dụng.
- **Ví dụ**: `"Senior Data Engineer - PySpark & Cloud (Remote)"`

### 3. `normalized_title`
- **Tên trường**: Normalized Occupation Title
- **Kiểu dữ liệu**: `string` (VARCHAR 64)
- **Bắt buộc**: `NOT NULL`
- **Mô tả**: Tên vị trí đã được chuẩn hóa về 8 nhóm nghề chính qua `configs/job_title_mapping_v0.json`.
- **Tập giá trị chuẩn**: `Data Analyst`, `Data Scientist`, `Data Engineer`, `Machine Learning Engineer`, `Software Engineer`, `Backend Developer`, `Frontend Developer`, `DevOps Engineer`, `Other IT`.

### 4. `company`
- **Tên trường**: Company Name
- **Kiểu dữ liệu**: `string` (VARCHAR 255)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Tên công ty đăng tuyển.

### 5. `location`
- **Tên trường**: Job Location (Raw)
- **Kiểu dữ liệu**: `string` (VARCHAR 255)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Địa điểm làm việc nguyên bản từ tin đăng.
- **Ví dụ**: `"San Francisco, CA"`, `"Berlin"`, `"Remote"`

### 6. `city`
- **Tên trường**: City Name
- **Kiểu dữ liệu**: `string` (VARCHAR 128)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Tên thành phố cụ thể được bóc tách từ `location`.
- **Ví dụ**: `"San Francisco"`, `"Berlin"`, `"Austin"`

### 7. `country`
- **Tên trường**: Country Name
- **Kiểu dữ liệu**: `string` (VARCHAR 64)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Tên quốc gia tuyển dụng.
- **Ví dụ**: `"United States"`, `"Germany"`, `"Worldwide"`

### 8. `market`
- **Tên trường**: Market Dimension
- **Kiểu dữ liệu**: `string` (VARCHAR 32)
- **Bắt buộc**: `NOT NULL`
- **Mô tả**: Phân vùng thị trường tuyển dụng. Trong MVP hiện tại, giá trị luôn là `"GLOBAL"`. Sẵn sàng mở rộng sang `"VIETNAM"` trong giai đoạn tiếp theo.
- **Tập giá trị**: `"GLOBAL"`, `"VIETNAM"`
- **Ví dụ**: `"GLOBAL"`

### 9. `work_mode`
- **Tên trường**: Work Mode
- **Kiểu dữ liệu**: `string` (VARCHAR 32)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Hình thức làm việc của vị trí tuyển dụng.
- **Tập giá trị chuẩn**: `"Remote"`, `"Onsite"`, `"Hybrid"`
- **Ví dụ**: `"Remote"`

### 10. `description`
- **Tên trường**: Job Description (Cleaned)
- **Kiểu dữ liệu**: `string` (TEXT)
- **Bắt buộc**: `NOT NULL`
- **Mô tả**: Toàn văn mô tả công việc đã làm sạch (strip HTML tags, chuẩn hóa khoảng trắng).

### 11. `experience_level`
- **Tên trường**: Seniority Level
- **Kiểu dữ liệu**: `string` (VARCHAR 32)
- **Bắt buộc**: `NULLABLE`
- **Tập giá trị**: `Intern`, `Junior`, `Mid`, `Senior`, `Lead`, `Principal`, `Unknown`.

### 12. `salary_min`
- **Tên trường**: Minimum Annual Salary (USD)
- **Kiểu dữ liệu**: `integer` (INT)
- **Bắt buộc**: `NULLABLE`

### 13. `salary_max`
- **Tên trường**: Maximum Annual Salary (USD)
- **Kiểu dữ liệu**: `integer` (INT)
- **Bắt buộc**: `NULLABLE`

### 14. `posted_at`
- **Tên trường**: Job Posted Timestamp (UTC)
- **Kiểu dữ liệu**: `timestamp` (`YYYY-MM-DD HH:MM:SS`)
- **Bắt buộc**: `NOT NULL`
- **Mô tả**: Thời điểm bài đăng được công khai trên nền tảng tuyển dụng.

### 15. `collected_at`
- **Tên trường**: Data Ingestion Timestamp (UTC)
- **Kiểu dữ liệu**: `timestamp` (`YYYY-MM-DD HH:MM:SS`)
- **Bắt buộc**: `NOT NULL`
- **Mô tả**: Thời điểm hệ thống ETL/Ingestion đọc và lưu dữ liệu.

### 16. `source`
- **Tên trường**: Data Source Identifier
- **Kiểu dữ liệu**: `string` (VARCHAR 64)
- **Bắt buộc**: `NOT NULL`
- **Ví dụ**: `"arbeitnow"`, `"remotive"`, `"kaggle_historical_archive"`

### 17. `skills`
- **Tên trường**: Extracted Skill Array
- **Kiểu dữ liệu**: `array<string>` (JSON ARRAY)
- **Bắt buộc**: `NOT NULL`
- **Mô tả**: Danh sách các kỹ năng chuẩn hóa trích xuất được từ `description`.
- **Ví dụ**: `["python", "sql", "spark", "docker", "aws"]`
