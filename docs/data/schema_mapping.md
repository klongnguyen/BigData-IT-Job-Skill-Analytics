# Schema Mapping: Big Data IT Job Skill Analytics

Tài liệu này mô tả mapping theo header đang có trong archive và cấu trúc API đã quan sát. Giá trị thiếu được giữ `null`; trường nguồn không tồn tại không được bịa hoặc suy luận thành dữ liệu quan sát.

## 1. Mapping sang Unified Schema

| Trường chuẩn | Historical archive (`data_jobs.csv`) | Arbeitnow | Remotive | Quy tắc |
|---|---|---|---|---|
| `job_id` | Không có native ID; checksum dòng nguồn | `slug` | `id` | SHA-256 ổn định từ source + source record ID; archive dùng checksum raw |
| `title` | `job_title` | `title` | `title` | Giữ tiêu đề gốc đã trim |
| `normalized_title` | Từ `job_title` | Từ `title` | Từ `title` | Cùng taxonomy title mapping; unknown thành `Other IT` |
| `company` | `company_name` | `company_name` | `company_name` | Null nếu nguồn thiếu |
| `location` | `job_location` | `location` | `candidate_required_location` | Giữ nội dung nguồn |
| `city` | Không có mapping tin cậy hiện tại | Không chuẩn hóa trong collector | Không chuẩn hóa trong collector | `null` đến khi có parser có thể đánh giá |
| `country` | `job_country` nếu có | Không suy diễn từ nhãn vùng | Không suy diễn từ nhãn vùng | `null` nếu không phải quốc gia xác định |
| `market` | Hằng số phân loại `GLOBAL` | `GLOBAL` | `GLOBAL` | Metadata phạm vi MVP, không phải trường quan sát |
| `work_mode` | Không có mapping tin cậy hiện tại | `remote` nếu API cung cấp | Remote theo category/API | Null nếu không có bằng chứng |
| `description` | Không có cột `job_description` | `description` | `description` | Làm sạch HTML; historical giữ null |
| `experience_level` | Không có trong raw hiện tại | Chưa suy luận | Chưa suy luận | Null đến khi có logic đã đánh giá |
| `salary_min`, `salary_max` | Null nếu raw không cung cấp | Null | Null trong pipeline hiện tại | Không parse tự động chuỗi lương chưa chuẩn hóa |
| `currency` | Null nếu không có | Null | Null | Không mặc định USD khi thiếu bằng chứng |
| `posted_at` | `job_posted_date` | `created_at` | `publication_date` | Parse UTC; null/invalid được quarantine khỏi Silver phân tích thời gian |
| `collected_at` | Metadata batch nếu được ghi nhận | Thời điểm collector gọi API | Thời điểm collector gọi API | Không sinh giả cho archive; null nếu không lưu được |
| `source` | `kaggle_historical_archive` | `arbeitnow` | `remotive` | Gắn định danh nguồn |
| `skills` | `job_skills` source tags | JD nếu có; tags nếu không có JD | JD nếu có; tags nếu không có JD | Chuẩn hóa theo `skills_v0.json`; lưu `skills_origin` (`source_tags`/`extracted_from_jd`) trong provenance |

## 2. Provenance và giới hạn hiện tại

Unified Schema chỉ chứa dữ liệu phục vụ phân tích. Bảng provenance gắn 1:1 với mỗi dòng Silver còn lại cần lưu ít nhất `source_record_id`, `source_url`, `description_origin`, `skills_origin`, `taxonomy_version`, `ingestion_id`, `collected_at`, `raw_checksum` và chất lượng timestamp.

Archive hiện có `job_title`, `job_posted_date`, `job_skills`, `company_name` và các trường nguồn khác; không có JD, native job ID hoặc source URL. Vì vậy không thể dùng archive này để định lượng độ chính xác trích xuất skill từ JD, và không thể khôi phục trường nguồn không tồn tại bằng mapping.
