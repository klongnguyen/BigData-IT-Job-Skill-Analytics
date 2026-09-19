# Fresh Data (2026) Evaluation: Big Data IT Job Skill Analytics

Tài liệu này đánh giá các nguồn dữ liệu tuyển dụng cập nhật thời gian thực (năm 2026) nhằm cung cấp dòng dữ liệu mới (Fresh Data) cho hệ thống, phục vụ việc nhận diện Concept Drift và dự báo xu hướng kỹ năng.

---

## 1. Khảo sát các nguồn API công khai 2026

| Nguồn | Loại hình | Yêu cầu Authentication | Định dạng dữ liệu | Trường thời gian | Đánh giá tính khả thi |
|---|---|---|---|---|---|
| **Arbeitnow API** | REST API công khai | Không cần API key (Free) | JSON | `created_at` (Unix timestamp) | **Rất cao (Primary Source 1)**. Trả về 100–250 jobs/request, hỗ trợ phân trang, có đầy đủ description HTML/text, tags, vị trí. |
| **Remotive API** | REST API công khai | Không cần API key (Free) | JSON | `publication_date` (ISO 8601: `2026-09-17T13:22:05`) | **Rất cao (Primary Source 2)**. Chuyên sâu về IT/Software Development, có tags kỹ năng, location, description chi tiết. |
| **Adzuna API** | Commercial / Freemium | Cần `app_id` + `app_key` | JSON | `created` (ISO format) | **Cao (Secondary Source)**. Độ phủ toàn cầu lớn (US, UK, VN...), có thông tin salary chuẩn hóa. |
| **JSearch (RapidAPI)**| Aggregator API | Cần RapidAPI Key (500 free req/tháng) | JSON | `job_posted_at_timestamp` | **Trung bình - Cao**. Dữ liệu lấy từ LinkedIn, Indeed, Glassdoor; thích hợp lấy mẫu chất lượng cao. |

---

## 2. Kết quả kiểm tra API thực tế (Live Test Result - 09/2026)

Hệ thống đã thực hiện kiểm tra thực tế (qua script `src/collection/test_api_sources.py`):

### 2.1. Nguồn 1: Arbeitnow API (`https://www.arbeitnow.com/api/job-board-api`)
- **Trạng thái**: HTTP 200 OK.
- **Số lượng**: 250 tin tuyển dụng trên 1 request.
- **Timestamp ghi nhận**: `created_at: 1789818008` (tháng 09/2026).
- **Schema thực tế**:
  ```json
  {
    "slug": "procurement-manager-andercore-12345",
    "company_name": "Andercore",
    "title": "Procurement Manager",
    "description": "<p>Job description HTML...</p>",
    "remote": true,
    "url": "https://...",
    "tags": ["Operations", "Supply Chain"],
    "job_types": ["Full Time"],
    "location": "Berlin",
    "created_at": 1789818008
  }
  ```

### 2.2. Nguồn 2: Remotive API (`https://remotive.com/api/remote-jobs?category=software-dev`)
- **Trạng thái**: HTTP 200 OK.
- **Timestamp ghi nhận**: `publication_date: 2026-09-17T13:22:05` (tháng 09/2026).
- **Schema thực tế**:
  ```json
  {
    "id": 1928374,
    "url": "https://...",
    "title": "Senior .NET Full-stack Developer",
    "company_name": "Lemon.io",
    "category": "Software Development",
    "tags": [".Net", "C#", "python", "docker", "AWS", "AI/ML"],
    "job_type": "full_time",
    "publication_date": "2026-09-17T13:22:05",
    "candidate_required_location": "Worldwide",
    "salary": "$60k - $90k",
    "description": "Full job description text..."
  }
  ```

---

## 3. Đánh giá tính phù hợp với Unified Schema

1. **Trường thời gian**: Cả hai API đều cung cấp timestamp chính xác tại thời điểm đăng (`posted_at` = `publication_date` hoặc `created_at`), kết hợp với thời điểm gọi API (`collected_at` = `datetime.utcnow()`), đáp ứng 100% tiêu chí phân tích xu hướng thời gian.
2. **Trường kỹ năng & mô tả**:
   - `description` có đầy đủ chi tiết yêu cầu công việc để chạy module **Skill Extraction**.
   - Có sẵn trường `tags` chứa các từ khóa kỹ năng quan trọng (rất hữu ích để đối soát và đánh giá chéo).
3. **Phạm vi IT**: Tập trung mạnh vào các vị trí Software Engineer, Backend, Frontend, DevOps, Data Analyst/Engineer, AI/ML.

---

## 4. Kết luận
Hai nguồn **Arbeitnow** và **Remotive** hoàn toàn khả thi, miễn phí, ổn định, không yêu cầu xác thực phức tạp và cung cấp dữ liệu năm 2026 chất lượng cao. Chúng được lựa chọn làm nguồn **Fresh Data chính thức** cho Giai đoạn 1.
