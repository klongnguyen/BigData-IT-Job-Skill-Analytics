# Data Dictionary (Final - 18 Fields): Big Data IT Job Skill Analytics

Tài liệu này cung cấp từ điển dữ liệu chi tiết cho từng trường trong **Unified Schema (18 trường)** theo đặc tả chính thức của [FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md](file:///d:/Study/2026/Nam04_HK1/bigData_T.Ha/BigData_Job_Analy/FINAL_PLAN_BigData_IT_Job_Market_Skill_Forecasting.md).

---

## Chi tiết 18 trường trong Unified Schema

### 1. `job_id`
- **Tên trường**: Job Identifier
- **Kiểu dữ liệu**: `string` (VARCHAR 128)
- **Bắt buộc**: `NOT NULL` (Primary Key)
- **Mô tả**: SHA-256 ổn định từ nguồn và ID/mã định danh dòng nguồn; nếu upstream không có ID, dùng checksum nội dung raw. Không phải native ID và không dùng số thứ tự sinh theo lần chạy.
- **Ví dụ**: chuỗi SHA-256 64 ký tự hex.

### 2. `title`
- **Tên trường**: Job Title (Original)
- **Kiểu dữ liệu**: `string` (VARCHAR 255)
- **Bắt buộc**: `NOT NULL`
- **Mô tả**: Tiêu đề công việc gốc từ bài đăng tuyển dụng.
- **Ví dụ**: `"Senior React Developer (Remote)"`

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
- **Mô tả**: Tên thành phố từ trường nguồn đáng tin cậy; hiện API/archive không cung cấp mapping thống nhất nên thường là null, không lấy nguyên cụm location làm city.
- **Ví dụ**: `"San Francisco"`, `"Berlin"`, `"Austin"`

### 7. `country`
- **Tên trường**: Country Name
- **Kiểu dữ liệu**: `string` (VARCHAR 64)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Tên quốc gia tuyển dụng.
- **Ví dụ**: `"United States"`, `"Germany"`; giá trị vùng như `"Worldwide"` được giữ `null`.

### 8. `market`
- **Tên trường**: Market Dimension
- **Kiểu dữ liệu**: `string` (VARCHAR 32)
- **Bắt buộc**: `NOT NULL`
- **Mô tả**: Phân vùng thị trường. Trong MVP: luôn là `"GLOBAL"`.
- **Tập giá trị**: `"GLOBAL"`, `"VIETNAM"` (Future Extension)

### 9. `work_mode`
- **Tên trường**: Work Mode
- **Kiểu dữ liệu**: `string` (VARCHAR 32)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Hình thức làm việc: `"Remote"`, `"Onsite"`, `"Hybrid"`.

### 10. `description`
- **Tên trường**: Job Description (Cleaned)
- **Kiểu dữ liệu**: `string` (TEXT)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: JD đã làm sạch khi nguồn cung cấp. Archive Luke Barousse đang dùng không có trường JD; giá trị historical phải để `null`, không tạo nội dung thay thế.

### 11. `experience_level`
- **Tên trường**: Seniority Level
- **Kiểu dữ liệu**: `string` (VARCHAR 32)
- **Bắt buộc**: `NULLABLE`
- **Tập giá trị**: `Intern`, `Junior`, `Mid`, `Senior`, `Lead`, `Principal`, `Unknown`.

### 12. `salary_min`
- **Tên trường**: Minimum Annual Salary
- **Kiểu dữ liệu**: `integer` (INT)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Mức lương tối thiểu hàng năm.

### 13. `salary_max`
- **Tên trường**: Maximum Annual Salary
- **Kiểu dữ liệu**: `integer` (INT)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Mức lương tối đa hàng năm.

### 14. `currency`
- **Tên trường**: Salary Currency
- **Kiểu dữ liệu**: `string` (VARCHAR 16)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Đơn vị tiền tệ của mức lương theo dữ liệu nguồn; để `null` nếu không xác định, không mặc định `USD`.
- **Ví dụ**: `"USD"`, `"EUR"`, `"GBP"`

### 15. `posted_at`
- **Tên trường**: Job Posted Timestamp (UTC)
- **Kiểu dữ liệu**: `timestamp` (`YYYY-MM-DD HH:MM:SS`)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Thời điểm bài đăng được công khai trên nền tảng tuyển dụng. Thiếu hoặc parse lỗi thì để `null` và đưa khỏi luồng cần partition theo thời gian.

### 16. `collected_at`
- **Tên trường**: Data Ingestion Timestamp (UTC)
- **Kiểu dữ liệu**: `timestamp` (`YYYY-MM-DD HH:MM:SS`)
- **Bắt buộc**: `NULLABLE`
- **Mô tả**: Thời điểm ETL/Ingestion đọc và nạp dữ liệu. Không giả lập cho archive lịch sử; thời điểm tạo batch có thể ghi ở metadata ingestion riêng.

### 17. `source`
- **Tên trường**: Data Source Identifier
- **Kiểu dữ liệu**: `string` (VARCHAR 64)
- **Bắt buộc**: `NOT NULL`
- **Ví dụ**: `"arbeitnow"`, `"remotive"`, `"kaggle_historical_archive"`

### 18. `skills`
- **Tên trường**: Extracted Skill Array
- **Kiểu dữ liệu**: `array<string>` (JSON ARRAY)
- **Bắt buộc**: `NOT NULL`
- **Mô tả**: Danh sách kỹ năng chuẩn hóa. Archive dùng source tags `job_skills`; fresh ưu tiên trích từ JD và chỉ fallback về tags khi JD thiếu. Trường provenance `skills_origin` phân biệt hai trường hợp; đây không phải nhãn ground truth.
- **Ví dụ**: `["python", "sql", "spark", "docker", "aws"]`
