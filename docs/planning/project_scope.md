# Project Scope: Big Data IT Job Skill Analytics

## 1. Tổng quan đề tài
Dự án **Big Data IT Job Skill Analytics** xây dựng một hệ thống phân tích dữ liệu lớn nhằm thu thập, lưu trữ, xử lý và dự báo xu hướng nhu cầu kỹ năng trong ngành Công nghệ Thông tin (CNTT). Hệ thống kết hợp dữ liệu tuyển dụng lịch sử (2020–2025) và dữ liệu tuyển dụng cập nhật năm 2026 để nắm bắt sự biến động nhanh chóng của thị trường lao động công nghệ.

---

## 2. Mục tiêu hệ thống (Objectives)
1. **Phân tích thực trạng**:
   - Xác định các vị trí CNTT có nhu cầu tuyển dụng cao nhất.
   - Thống kê top kỹ năng được yêu cầu nhiều nhất theo từng vị trí nghề nghiệp.
   - Phân tích tương quan giữa kỹ năng, vị trí và mức lương/kinh nghiệm.
2. **Theo dõi xu hướng (Trend Analysis)**:
   - Đo lường sự biến thiên của nhu cầu kỹ năng theo các mốc thời gian (tháng, quý, năm).
   - Phân loại trạng thái kỹ năng thành 3 nhóm: **Growing** (Đang tăng trưởng), **Stable** (Ổn định), **Declining** (Suy giảm).
3. **Dự báo tương lai (Forecasting)**:
   - Xây dựng mô hình dự báo nhu cầu kỹ năng trong các giai đoạn tiếp theo (ngắn hạn: 3–6 tháng; trung hạn: 1 năm).
   - So sánh 3 phương pháp tiếp cận:
     - Baseline 1: Chỉ sử dụng dữ liệu lịch sử.
     - Baseline 2: Chỉ sử dụng dữ liệu mới gần đây.
     - Hybrid Model: Mô hình kết hợp có trọng số thời gian (Recency Weighting) và xử lý Concept Drift.
4. **Trực quan hóa**:
   - Cung cấp Dashboard tương tác (Streamlit) cho người dùng khám phá xu hướng kỹ năng và đưa ra quyết định định hướng nghề nghiệp.

---

## 3. Đối tượng sử dụng (Target Audience)
- **Sinh viên & Ứng viên CNTT**: Nắm bắt xu hướng công nghệ mới nổi (ví dụ: Generative AI, LLM, Cloud Native), định hướng lộ trình học tập và chuẩn bị kỹ năng đáp ứng thị trường.
- **Nhà tuyển dụng & Doanh nghiệp**: Hiểu rõ mặt bằng kỹ năng thị trường, điều chỉnh yêu cầu tuyển dụng và chính sách đãi ngộ hợp lý.
- **Cơ sở đào tạo & Đại học**: Cập nhật giáo trình đào tạo phù hợp với nhu cầu thực tế của ngành công nghiệp.

---

## 4. Phạm vi hệ thống (Scope)

### 4.1. Phạm vi dữ liệu & Địa lý
- **Thị trường trọng tâm (Chính)**: Thị trường Toàn cầu / Tiếng Anh (Mỹ, Châu Âu, Remote). Nguồn dữ liệu phong phú, mốc thời gian liên tục từ 2020–2025, định dạng chuẩn hóa cao.
- **Thị trường bổ trợ**: Thị trường Việt Nam (thu thập bổ sung từ các nền tảng tuyển dụng CNTT trong nước để làm phong phú và địa phương hóa bài toán).
- **Khoảng thời gian**:
  - Historical Data: 2020 – 2025 (dữ liệu lịch sử).
  - Fresh Data: Năm 2026 (dữ liệu mới cập nhật qua API/Crawler).

### 4.2. Nhóm nghề nghiệp CNTT (Occupations)
Hệ thống tập trung vào 8 nhóm nghề trọng điểm:
1. **Data Analyst (DA)**
2. **Data Scientist (DS)**
3. **Data Engineer (DE)**
4. **Machine Learning Engineer (MLE)**
5. **Software Engineer (SWE)**
6. **Backend Developer (BE)**
7. **Frontend Developer (FE)**
8. **DevOps Engineer (DevOps)**

### 4.3. Nhóm kỹ năng (Skill Domains)
Hệ thống theo dõi 8 nhóm kỹ năng công nghệ chính:
1. **Programming Languages**: Python, Java, JavaScript, C++, C#, Go, TypeScript,...
2. **Database & Storage**: SQL, MySQL, PostgreSQL, MongoDB, Redis, Cassandra,...
3. **Big Data & Distributed Systems**: Spark, Hadoop, Kafka, Hive, Flink, Airflow,...
4. **Cloud Platforms**: AWS, Azure, GCP,...
5. **DevOps & Infrastructure**: Docker, Kubernetes, CI/CD, Jenkins, Terraform, Ansible,...
6. **Business Intelligence (BI) & Analytics**: Power BI, Tableau, Excel, Looker,...
7. **AI / Machine Learning / Deep Learning**: TensorFlow, PyTorch, Scikit-learn, Computer Vision, NLP,...
8. **Modern GenAI & LLM**: Generative AI, LLM, RAG, Prompt Engineering, LangChain,...

---

## 5. Giới hạn đề tài (Limitations & Out-of-Scope)
- **Chất lượng văn bản JD**: Độ chính xác trích xuất kỹ năng phụ thuộc vào chất lượng mô tả công việc (Job Description). Các JD quá ngắn hoặc không mô tả rõ yêu cầu kỹ thuật sẽ bị lọc bỏ.
- **Khác biệt ngôn ngữ**: Ngôn ngữ xử lý chính là tiếng Anh. Đối với tin tuyển dụng tiếng Việt, hệ thống áp dụng từ điển thuật ngữ kỹ thuật tiếng Anh được nhúng trong bài đăng.
- **Dự báo ngắn/trung hạn**: Mô hình dự báo xu hướng kỹ năng tập trung vào xu thế thị trường trong 3–12 tháng tới dựa trên các đặc trưng thống kê và chuỗi thời gian, không khẳng định chắc chắn 100% các biến động đột biến không thể dự báo trước của ngành công nghệ.
