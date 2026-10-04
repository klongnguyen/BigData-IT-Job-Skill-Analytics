# Project Scope: Big Data IT Job Skill Analytics

## 1. Tổng quan đề tài
Dự án **Big Data IT Job Skill Analytics** hướng tới hệ thống phân tích dữ liệu tuyển dụng CNTT và nghiên cứu xu hướng nhu cầu kỹ năng. Các năm bên dưới mô tả mục tiêu nghiên cứu, không phải coverage dữ liệu hiện có.

> **Coverage đã kiểm kê (Phase 01):** archive hiện có 785.741 dòng từ 2023-01 đến 2023-12, có source tags nhưng không có JD; fresh data hiện là snapshot đã lưu. Dữ liệu này chưa chứng minh chuỗi lịch sử 2020–2025 hay đủ điều kiện forecast. Xem [audit](../data/phase01_data_audit.json) và [GO/NO-GO](go_no_go_report.md).

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
   - Đích MVP là dự báo kỳ tháng kế tiếp từ tỷ lệ nhu cầu kỹ năng theo occupation; chỉ bật khi cổng dữ liệu và rolling backtest trong Final Plan đạt.
   - So sánh 4 nhánh trên cùng future test:
     - Baseline 1: Chỉ sử dụng dữ liệu lịch sử.
     - Baseline 2: Chỉ sử dụng dữ liệu mới gần đây.
     - Hybrid Model có Recency Weighting.
     - Hybrid Model không trọng số để tách tác dụng của dữ liệu mới khỏi weighting.
   - Nếu quality gate chưa đạt, chỉ báo analytics/observed trend và `Insufficient evidence`; không công bố nhãn forecast.
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
- **Thị trường trọng tâm (Chính)**: Mục tiêu là thị trường Toàn cầu / Tiếng Anh (Mỹ, Châu Âu, Remote). Nguồn archive hiện có chỉ bao phủ năm 2023; không giả định có chuỗi liên tục 2020–2025.
- **Thị trường bổ trợ**: Việt Nam đang **FROZEN** trong MVP; chỉ mở rộng sau khi hoàn tất cổng dữ liệu và nghiệm thu riêng.
- **Khoảng thời gian**:
  - Historical Data — cần các kỳ thật liên tiếp, có thể so sánh để phân tích/forecast; repository hiện chỉ kiểm kê được năm 2023.
  - Fresh Data — snapshot lưu năm 2026; chưa xác nhận collector chạy liên tục.

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
- **Horizon dự báo MVP**: Chỉ dự báo kỳ tháng kế tiếp theo rolling-origin khi quality gate dữ liệu đạt. Horizon dài hơn là future work, chỉ xem xét sau khi có đủ chuỗi thời gian và đánh giá ngoài mẫu; không xem đây là cam kết hiện tại.
