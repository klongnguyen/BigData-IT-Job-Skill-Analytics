# Schema Mapping: Big Data IT Job Skill Analytics

Tài liệu này xác định bảng ánh xạ trường dữ liệu (Field Mapping) từ các nguồn dữ liệu đầu vào (Historical Data, Arbeitnow API, Remotive API) sang **Unified Schema** chuẩn của hệ thống.

---

## 1. Bảng ánh xạ tổng thể (Master Schema Mapping)

| Unified Schema Field | Historical Data Field (Kaggle/Luke) | Fresh Data: Arbeitnow | Fresh Data: Remotive | Logic chuyển đổi / Chuẩn hóa |
|---|---|---|---|---|
| `job_id` | `job_id` | `slug` (tiền tố `arbeitnow_`) | `id` (tiền tố `remotive_`) | Chuỗi định danh duy nhất (UUID hoặc tiền tố nguồn + ID) |
| `title` | `job_title` | `title` | `title` | Chuỗi text gốc, loại bỏ khoảng trắng thừa |
| `normalized_title` | `job_title_short` | *Suy luận qua title mapping* | *Suy luận qua title mapping* | Ánh xạ về 1 trong 8 nhóm nghề chuẩn |
| `company` | `job_company_name` | `company_name` | `company_name` | Tên công ty chuẩn hóa |
| `location` | `job_location` | `location` | `candidate_required_location` | Địa điểm làm việc hoặc "Remote" |
| `city` | `city` | *Trích xuất từ location* | *Trích xuất từ location* | Tên thành phố cụ thể (nullable) |
| `country` | `job_country` | *Trích xuất từ location* | *Trích xuất từ location* | Tên quốc gia hoặc "Worldwide" / "Unknown" |
| `market` | `"GLOBAL"` | `"GLOBAL"` | `"GLOBAL"` | Phân vùng thị trường (luôn là "GLOBAL" trong MVP) |
| `work_mode` | `work_mode` | *Suy luận từ remote* | `"Remote"` | "Remote", "Onsite", hoặc "Hybrid" |
| `description` | `job_description` | `description` (HTML) | `description` (HTML/Text) | Strip HTML tags, làm sạch văn bản |
| `experience_level` | *Suy luận từ title/JD* | *Suy luận từ title/JD* | *Suy luận từ title/JD* | Junior / Mid / Senior / Lead / Unknown |
| `salary_min` | `salary_min` | `null` | *Parse từ trường `salary`* | Số nguyên (USD/năm), nullable = true |
| `salary_max` | `salary_max` | `null` | *Parse từ trường `salary`* | Số nguyên (USD/năm), nullable = true |
| `posted_at` | `job_posted_date` | `created_at` (epoch timestamp) | `publication_date` (ISO 8601) | Chuẩn hóa về format `YYYY-MM-DD HH:MM:SS` (UTC) |
| `collected_at` | `collected_at` | `collected_at` | `collected_at` | Thời điểm hệ thống gọi API/thu thập (UTC) |
| `source` | `source` | `"arbeitnow"` | `"remotive"` | Định danh nguồn thu thập |
| `skills` | `job_skills` | *Trích xuất từ description + tags* | *Trích xuất từ description + tags* | Mảng JSON các kỹ năng chuẩn hóa trích xuất được |

---

## 2. Chi tiết logic chuyển đổi từng trường

### 2.1. Chuẩn hóa Thời gian (`posted_at` & `collected_at`)
- **Historical Data**: Chuỗi `2023-04-15 10:20:00` -> giữ nguyên định dạng ISO.
- **Arbeitnow**: Số nguyên Unix timestamp `1789818008` -> chuyển đổi qua `datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")`.
- **Remotive**: Chuỗi ISO 8601 `2026-09-17T13:22:05` -> loại bỏ ký tự `T` và múi giờ, quy về `YYYY-MM-DD HH:MM:SS` (UTC).
- **Trường `collected_at`**: Luôn được sinh tự động tại thời điểm ETL Ingestion bằng thời gian thực UTC.

### 2.2. Làm sạch Job Description (`description`)
- Với các nguồn trả về HTML (như Arbeitnow):
  - Áp dụng parser để loại bỏ toàn bộ thẻ HTML `<p>`, `<ul>`, `<li>`, `<b>`, `<br>`, `<div>`.
  - Thay thế các ký tự thực thể HTML: `&amp;` -> `&`, `&nbsp;` -> khoảng trắng.
  - Chuẩn hóa khoảng trắng và dấu xuống dòng.

### 2.3. Trích xuất mức lương (`salary_min`, `salary_max`)
- Nguồn Remotive thường trả về chuỗi text dạng `"$60k - $90k"` hoặc `"$120,000 / year"`:
  - Regex pattern: `\$?(\d+)[kK]?\s*[-–to]\s*\$?(\d+)[kK]?`
  - Nhân hệ số `1000` với các giá trị có hậu tố `k`.
  - Nếu không có thông tin lương hoặc lương theo giờ chưa quy đổi: lưu `null`.

### 2.4. Trích xuất mảng kỹ năng (`skills`)
- Nguồn Historical: Nếu đã có mảng `job_skills`, đối chiếu với bộ từ điển `configs/skills_v0.json` để chuẩn hóa mã kỹ năng.
- Nguồn Fresh: Kết hợp các từ khóa trong trường `tags` và kết quả quét regex từ `description` sạch để tạo mảng kỹ năng không trùng lặp (distinct array).
